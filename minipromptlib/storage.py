"""Versioned, atomic JSON persistence for MiniPromptLib."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 3

DEFAULT_FOLDER = "general"


class StorageCorruptionError(RuntimeError):
    """Raised when a prompt store cannot be safely interpreted."""


def _derive_folder(entry: dict[str, Any]) -> str:
    """Best-effort folder for an entry that predates the v3 folder field.

    Deterministic and conservative: falls back to DEFAULT_FOLDER rather than
    guessing from free text. Seed-authored entries get their folder assigned
    explicitly by seeds.py, so this only matters for non-seed legacy entries.
    """
    category = str(entry.get("category") or "").strip().lower()
    if category and category != "workflow":
        return category
    states = entry.get("workflow_states") or []
    if states:
        return f"captured/{states[0]}"
    return DEFAULT_FOLDER


def migrate_to_v3(prompts: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Add a `folder` field to every entry that is missing one. Additive only.

    Never removes or renames the existing `category` field, so schema v2
    consumers reading the raw JSON (or a human editing it) are unaffected.
    Idempotent: entries that already carry `folder` are left untouched.
    """
    for entry in prompts.values():
        if not isinstance(entry, dict):
            raise StorageCorruptionError("Prompt library has a non-object prompt entry; refusing to migrate.")
        if "folder" not in entry or not entry["folder"]:
            entry["folder"] = _derive_folder(entry)
    return prompts


def load_prompts(path: Path) -> dict[str, dict[str, Any]]:
    """Load a legacy prompt dictionary or the current schema envelope."""
    if not path.exists():
        return {}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageCorruptionError(
            f"Could not read prompt library at {path}. The file was left unchanged."
        ) from exc

    if not isinstance(raw, dict):
        raise StorageCorruptionError(
            f"Prompt library at {path} must contain a JSON object. The file was left unchanged."
        )

    prompts = raw.get("prompts") if "schema_version" in raw else raw
    if not isinstance(prompts, dict) or not all(isinstance(item, dict) for item in prompts.values()):
        raise StorageCorruptionError(
            f"Prompt library at {path} has an invalid prompt mapping. The file was left unchanged."
        )
    return migrate_to_v3(prompts)


def save_prompts(path: Path, prompts: dict[str, dict[str, Any]]) -> None:
    """Atomically write the current schema envelope without partial JSON files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    payload = {"schema_version": SCHEMA_VERSION, "prompts": prompts}
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
