"""Versioned, atomic JSON persistence for MiniPromptLib."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2


class StorageCorruptionError(RuntimeError):
    """Raised when a prompt store cannot be safely interpreted."""


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
    return prompts


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
