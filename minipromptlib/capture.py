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


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "for", "from", "in", "is", "it",
    "of", "on", "or", "the", "this", "to", "we", "what", "with", "you", "your",
    "lets", "let", "then",
}


def _slug(value: str, *, max_length: int = 64, max_words: int = 8) -> str:
    """Build a name from the text's own meaningful words, never mid-word truncated."""
    words = [word for word in re.findall(r"[a-z0-9]+", value.lower()) if word not in _STOPWORDS]
    if not words:
        words = re.findall(r"[a-z0-9]+", value.lower())
    if not words:
        return "captured-prompt"

    name = ""
    for word in words[:max_words]:
        candidate = f"{name}-{word}" if name else word
        if len(candidate) > max_length:
            break
        name = candidate
    return name or "captured-prompt"


def create_capture_draft(prompt_text: str) -> CaptureDraft:
    """Create a reviewable draft without persisting anything."""
    prompt_text = prompt_text.strip()
    if not prompt_text:
        raise ValueError("prompt_text cannot be empty")
    state = classify_workflow_state(ContextPacket(last_user_message=prompt_text)).state
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
