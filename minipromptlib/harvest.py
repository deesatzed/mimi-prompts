"""Deterministic detect -> generalize -> file -> dedupe pipeline for `mini harvest`.

Design constraints (see GOAL_GAP_FIX.md Phase 3):
  - Input is only text the caller supplies (--file/--text/stdin). No conversation
    history is ever read implicitly.
  - Every stage here is a pure function over the supplied text and the current
    library snapshot. Nothing is persisted by this module; the CLI layer is the
    only place a save happens, and only after explicit per-candidate consent.
  - No LLM call anywhere in this module. An optional LLM-assisted pass is future,
    separately scoped work (see GOAL_GAP_FIX.md Phase 5) and must not bypass the
    preview/consent flow implemented here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .capture import _slug
from .ranking import _tokens


_IMPERATIVE_OPENERS = (
    "always", "never", "make sure", "before", "after", "when", "if",
    "check", "ensure", "verify", "review", "confirm", "avoid", "prefer",
    "use", "do not", "don't", "never use", "remember",
)

_NARRATION_MARKERS = (
    "i think", "i feel", "i was", "we were", "yesterday", "today i",
    "thanks", "sounds good", "ok,", "okay,", "sure,",
)

MIN_CANDIDATE_LENGTH = 25
MAX_CANDIDATE_LENGTH = 600

_PLACEHOLDER_PATTERNS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"https?://\S+"), "{url}"),
    (re.compile(r"\b\d+\.\d+\.\d+(?:[-+][\w.]+)?\b"), "{version}"),
    (re.compile(r"(?:/[\w.\-]+){2,}/?"), "{path}"),
    (re.compile(r"\b[\w.\-]+\.(?:py|js|ts|tsx|jsx|json|md|yaml|yml|toml|sql|go|rs|java|rb)\b"), "{file}"),
    (
        re.compile(
            # Three-or-more kebab-case segments (e.g. "acme-billing-service"): a
            # two-segment kebab word is left alone since those are usually
            # ordinary English compounds ("edge-case", "real-time").
            r"\b(?:[a-z][a-z0-9]*-){2,}[a-z0-9]+\b"
            r"|\b[a-z][a-z0-9]*(?:[A-Z][a-z0-9]*){2,}\b"
            r"|\b[a-z][a-z0-9]*_[a-z0-9_]+\b"
        ),
        "{project}",
    ),
)


@dataclass(frozen=True)
class Candidate:
    """A detected instruction-like sentence, before generalization."""

    original_text: str
    reason: str


@dataclass(frozen=True)
class GeneralizedCandidate:
    """A candidate with a proposed generalized rewrite and a diff summary."""

    original_text: str
    generalized_text: str
    changes: list[str]
    suggested_name: str


@dataclass(frozen=True)
class FolderRecommendation:
    folder: str
    confidence: str  # "high" | "medium" | "low"
    reason: str


@dataclass(frozen=True)
class DuplicateMatch:
    prompt_id: str
    name: str
    overlap: float  # 0.0-1.0 Jaccard token overlap


@dataclass(frozen=True)
class HarvestDraft:
    """Everything needed to preview and, on consent, save one candidate."""

    original_text: str
    generalized_text: str
    changes: list[str]
    suggested_name: str
    suggested_folder: FolderRecommendation
    duplicate: DuplicateMatch | None
    workflow_states: list[str] = field(default_factory=list)


# --------------------------- Detect ---------------------------


def detect_candidates(text: str) -> list[Candidate]:
    """Find instruction-like sentences in caller-supplied text only.

    Deterministic heuristics: imperative openings or rule markers, bounded
    length, and narration filtered out. Zero candidates is a valid outcome.
    """
    if not text or not text.strip():
        return []

    # Split on sentence-ish boundaries and bullet/newline separators.
    raw_pieces = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    candidates: list[Candidate] = []
    seen: set[str] = set()

    for piece in raw_pieces:
        sentence = piece.strip().lstrip("-*• \t")
        if not sentence:
            continue
        if len(sentence) < MIN_CANDIDATE_LENGTH or len(sentence) > MAX_CANDIDATE_LENGTH:
            continue

        lowered = sentence.lower()
        if any(marker in lowered for marker in _NARRATION_MARKERS):
            continue

        opener_match = next((op for op in _IMPERATIVE_OPENERS if lowered.startswith(op)), None)
        rule_marker_match = None
        if not opener_match:
            rule_marker_match = next(
                (op for op in ("always", "never", "make sure", "before", "must") if op in lowered),
                None,
            )
        if not opener_match and not rule_marker_match:
            continue

        dedupe_key = re.sub(r"\s+", " ", lowered)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        reason = f"imperative opening ({opener_match})" if opener_match else f"rule marker ({rule_marker_match})"
        candidates.append(Candidate(original_text=sentence, reason=reason))

    return candidates


# --------------------------- Generalize ---------------------------


def generalize_text(text: str) -> tuple[str, list[str]]:
    """Deterministically parameterize project-specific specifics.

    Returns (generalized_text, change_descriptions). Never invents content;
    only substitutes matched spans with placeholders.
    """
    result = text
    changes: list[str] = []
    for pattern, placeholder in _PLACEHOLDER_PATTERNS:
        found = pattern.findall(result)
        if not found:
            continue
        unique_found = []
        for m in found:
            if m not in unique_found:
                unique_found.append(m)
        for match in unique_found:
            if match == placeholder:
                continue
            result = result.replace(match, placeholder)
            changes.append(f"{match!r} -> {placeholder}")
    return result, changes


def generalize_candidate(candidate: Candidate) -> GeneralizedCandidate:
    generalized_text, changes = generalize_text(candidate.original_text)
    suggested_name = _slug(candidate.original_text)
    return GeneralizedCandidate(
        original_text=candidate.original_text,
        generalized_text=generalized_text,
        changes=changes,
        suggested_name=suggested_name,
    )


# --------------------------- File (folder recommendation) ---------------------------


_HIGH_CONFIDENCE_OVERLAP = 3
_MEDIUM_CONFIDENCE_OVERLAP = 1


def recommend_folder(text: str, library_prompts: list[dict]) -> FolderRecommendation:
    """Score folders by token overlap with their existing members.

    Below any real overlap, proposes a new folder derived from the text's own
    words rather than forcing a bad fit into an existing one.
    """
    candidate_tokens = _tokens(text)
    if not candidate_tokens:
        return FolderRecommendation(folder="general", confidence="low", reason="no meaningful tokens to match")

    folder_tokens: dict[str, set[str]] = {}
    for prompt in library_prompts:
        folder = prompt.get("folder") or "general"
        folder_tokens.setdefault(folder, set()).update(_tokens(prompt.get("prompt_text", "")))
        folder_tokens[folder].update(_tokens(prompt.get("name", "")))

    best_folder = None
    best_overlap = 0
    for folder, tokens in folder_tokens.items():
        overlap = len(candidate_tokens & tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_folder = folder

    if best_folder and best_overlap >= _HIGH_CONFIDENCE_OVERLAP:
        return FolderRecommendation(
            folder=best_folder,
            confidence="high",
            reason=f"{best_overlap} shared words with existing prompts in this folder",
        )
    if best_folder and best_overlap >= _MEDIUM_CONFIDENCE_OVERLAP:
        return FolderRecommendation(
            folder=best_folder,
            confidence="medium",
            reason=f"{best_overlap} shared word(s) with existing prompts in this folder",
        )

    proposed = "/".join(sorted(candidate_tokens)[:2]) or "general"
    return FolderRecommendation(
        folder=f"captured/{proposed}",
        confidence="low",
        reason="no existing folder overlaps enough; proposing a new folder from the text's own words",
    )


# --------------------------- Dedupe ---------------------------


DUPLICATE_THRESHOLD = 0.6


def find_duplicate(text: str, library_prompts: list[dict]) -> DuplicateMatch | None:
    """Token-Jaccard match against the store. None if nothing crosses the threshold."""
    candidate_tokens = _tokens(text)
    if not candidate_tokens:
        return None

    best: DuplicateMatch | None = None
    for prompt in library_prompts:
        existing_tokens = _tokens(prompt.get("prompt_text", ""))
        if not existing_tokens:
            continue
        union = candidate_tokens | existing_tokens
        if not union:
            continue
        overlap = len(candidate_tokens & existing_tokens) / len(union)
        if overlap >= DUPLICATE_THRESHOLD and (best is None or overlap > best.overlap):
            best = DuplicateMatch(
                prompt_id=prompt["id"],
                name=prompt.get("name", prompt["id"]),
                overlap=round(overlap, 2),
            )
    return best


# --------------------------- End-to-end draft assembly ---------------------------


def build_drafts(text: str, library_prompts: list[dict]) -> list[HarvestDraft]:
    """Run the full detect -> generalize -> file -> dedupe pipeline. Nothing is saved."""
    drafts: list[HarvestDraft] = []
    for candidate in detect_candidates(text):
        generalized = generalize_candidate(candidate)
        folder = recommend_folder(generalized.original_text, library_prompts)
        duplicate = find_duplicate(generalized.original_text, library_prompts)
        drafts.append(
            HarvestDraft(
                original_text=generalized.original_text,
                generalized_text=generalized.generalized_text,
                changes=generalized.changes,
                suggested_name=generalized.suggested_name,
                suggested_folder=folder,
                duplicate=duplicate,
            )
        )
    return drafts
