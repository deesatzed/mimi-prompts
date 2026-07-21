"""Deterministic workflow-first prompt ranking with bounded frequency weight."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable

from .classifier import classify_workflow_state
from .models import ContextPacket, RankedPrompt


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "for", "from", "in", "is", "it",
    "of", "on", "or", "the", "this", "to", "we", "what", "with", "you", "your",
}


def _tokens(value: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9]+", value.lower())
        if len(word) > 2 and word not in _STOPWORDS
    }


def _prompt_tokens(prompt: dict) -> set[str]:
    return _tokens(
        " ".join(
            [
                prompt.get("name", ""),
                prompt.get("prompt_text", ""),
                prompt.get("description", ""),
                " ".join(prompt.get("tags", [])),
            ]
        )
    )


def rank_prompts(packet: ContextPacket, prompts: Iterable[dict]) -> list[RankedPrompt]:
    """Rank prompts by workflow relevance, then bounded explicit selection frequency."""
    state = classify_workflow_state(packet).state.value
    prompts = list(prompts)
    matching = [prompt for prompt in prompts if state in prompt.get("workflow_states", [])]
    candidates = matching or prompts
    context_tokens = _tokens(
        " ".join((packet.last_agent_message, packet.last_user_message, packet.build_status))
    )
    highest_frequency = max((int(prompt.get("selection_count", 0)) for prompt in candidates), default=0)
    denominator = math.log1p(highest_frequency) or 1.0
    ranked: list[RankedPrompt] = []

    for prompt in candidates:
        prompt_matches_state = state in set(prompt.get("workflow_states", []))
        state_score = 10.0 if prompt_matches_state else 0.0
        overlap = len(context_tokens & _prompt_tokens(prompt))
        logical_score = state_score + min(float(overlap), 5.0)
        count = max(int(prompt.get("selection_count", 0)), 0)
        frequency_score = math.log1p(count) / denominator if highest_frequency else 0.0
        if prompt_matches_state:
            reason = f"matches {state}; used {count}x"
        else:
            reason = f"closest available — no {state} prompts yet; used {count}x"
        ranked.append(
            RankedPrompt(
                prompt_id=prompt["id"],
                prompt=prompt.copy(),
                score=logical_score + (frequency_score * 2.0),
                reason=reason,
                logical_score=logical_score,
                frequency_score=frequency_score,
            )
        )

    return sorted(ranked, key=lambda item: (-item.score, item.prompt_id))


def page_ranked_prompts(
    ranked: list[RankedPrompt], *, offset: int = 0, page_size: int = 3
) -> list[RankedPrompt]:
    """Return one stable, bounded suggestion page."""
    return ranked[offset : offset + page_size]


def is_weak_signal(packet: ContextPacket, prompts: Iterable[dict], *, page_size: int = 3) -> bool:
    """True when the classifier landed on `general` and the shown page has no real match.

    Matching `general` is not itself a real signal -- it is the classifier's
    fallback bucket when nothing else fits, so a prompt tagged `general` scores
    highly regardless of relevance. "Real match" here means at least one of the
    displayed candidates shares an actual context word with the query. Without
    this, the ranked page is really just an alphabetical shelf with a
    confident-sounding reason attached to it; the CLI uses this signal to offer
    a one-keypress clarifying question instead.
    """
    state = classify_workflow_state(packet).state.value
    if state != "general":
        return False
    context_tokens = _tokens(
        " ".join((packet.last_agent_message, packet.last_user_message, packet.build_status))
    )
    if not context_tokens:
        return True
    prompts = list(prompts)
    if not prompts:
        return False
    ranked = rank_prompts(packet, prompts)
    page = page_ranked_prompts(ranked, page_size=page_size)
    return all(not (context_tokens & _prompt_tokens(item.prompt)) for item in page)
