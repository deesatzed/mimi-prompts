"""Preview-first capture of reusable instructions from natural language."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .classifier import classify_workflow_state
from .models import ContextPacket, WorkflowState


@dataclass(frozen=True)
class CaptureDraft:
    name: str
    prompt_text: str
    tags: list[str]
    workflow_states: list[str]
    description: str


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:64] or "captured-prompt"


def create_capture_draft(prompt_text: str) -> CaptureDraft:
    """Create a reviewable draft without persisting anything."""
    prompt_text = prompt_text.strip()
    if not prompt_text:
        raise ValueError("prompt_text cannot be empty")
    state = classify_workflow_state(ContextPacket(last_user_message=prompt_text)).state
    lowered = prompt_text.lower()
    if "scenario" in lowered or "tabletop" in lowered:
        name = "tabletop-scenarios-before-deciding"
    else:
        name = _slug(prompt_text)
    return CaptureDraft(
        name=name,
        prompt_text=prompt_text,
        tags=["captured", "workflow", state.value],
        workflow_states=[state.value] if state != WorkflowState.GENERAL else ["general"],
        description="Captured from current user wording; review before reuse.",
    )


def save_capture_draft(library, draft: CaptureDraft, *, overwrite: bool = False) -> str:
    """Persist a reviewed draft exactly as supplied by the caller."""
    prompt_id = library.save_mini_prompt(
        draft.prompt_text,
        name=draft.name,
        tags=draft.tags,
        category="workflow",
        description=draft.description,
        overwrite=overwrite,
    )
    library.prompts[prompt_id]["workflow_states"] = list(draft.workflow_states)
    library._save()
    return prompt_id
