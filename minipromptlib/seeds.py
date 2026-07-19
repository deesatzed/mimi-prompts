"""Deterministic conversion of the authored Markdown seed panel."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path
from typing import Any

from .core import MiniPromptLibrary


_STATE_BY_NUMBER = {
    2: ("proposal", "question"),
    4: ("proposal", "question"),
    5: ("failure", "general"),
    6: ("question", "checkpoint"),
    7: ("proposal", "undecided"),
    8: ("proposal", "question"),
    9: ("checkpoint", "proposal"),
    10: ("completion",),
    11: ("proposal", "question"),
    12: ("proposal",),
    13: ("proposal",),
    14: ("checkpoint", "proposal"),
    15: ("checkpoint", "proposal"),
    16: ("proposal",),
    17: ("proposal", "undecided"),
    18: ("checkpoint",),
    19: ("checkpoint",),
    20: ("proposal", "checkpoint"),
    21: ("proposal",),
    22: ("checkpoint", "proposal"),
    23: ("proposal",),
    24: ("checkpoint",),
    25: ("failure", "checkpoint"),
    26: ("checkpoint", "completion"),
    27: ("checkpoint",),
    28: ("proposal",),
    29: ("checkpoint", "undecided"),
    30: ("completion",),
    31: ("completion",),
    32: ("undecided",),
    33: ("completion",),
    34: ("completion",),
}


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:58] or "prompt"


def default_seed_panel() -> Path:
    """Return the packaged copy of the reviewed authored seed panel."""
    return Path(str(files("minipromptlib.data").joinpath("seeds.md")))


def load_seed_panel(path: str | Path) -> list[dict[str, Any]]:
    """Read every numbered prompt from the authored Markdown seed panel."""
    source = Path(path).read_text(encoding="utf-8")
    pattern = re.compile(
        r"^###\s+(\d+)\.\s+(.+?)\n(.*?)(?=^###\s+\d+\.\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    seeds: list[dict[str, Any]] = []
    for match in pattern.finditer(source):
        number = int(match.group(1))
        title = match.group(2).strip()
        prompt_text = match.group(3).strip()
        states = _STATE_BY_NUMBER.get(number, ("general",))
        seeds.append(
            {
                "number": number,
                "name": f"seed-{number:02d}-{_slug(title)}",
                "prompt_text": prompt_text,
                "description": f"Authored seed #{number}: {title}",
                "tags": ["seed", "workflow", *states],
                "category": "workflow",
                "workflow_states": list(states),
                "source_title": title,
            }
        )
    return seeds


def seed_library(
    library: MiniPromptLibrary,
    panel_path: str | Path,
    *,
    overwrite: bool = False,
) -> int:
    """Save the authored panel once and return the number of inserted prompts."""
    inserted = 0
    for seed in load_seed_panel(panel_path):
        if library.get_prompt(seed["name"]) and not overwrite:
            continue
        prompt_id = library.save_mini_prompt(
            seed["prompt_text"],
            name=seed["name"],
            tags=seed["tags"],
            category=seed["category"],
            description=seed["description"],
            overwrite=overwrite,
        )
        library.prompts[prompt_id]["workflow_states"] = seed["workflow_states"]
        library.prompts[prompt_id]["source_seed_number"] = seed["number"]
        library.prompts[prompt_id]["source_title"] = seed["source_title"]
        library._save()
        inserted += 1
    return inserted
