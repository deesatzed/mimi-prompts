"""Typed data shared by workflow classification, ranking, and navigation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class WorkflowState(StrEnum):
    QUESTION = "question"
    CHECKPOINT = "checkpoint"
    COMPLETION = "completion"
    FAILURE = "failure"
    PROPOSAL = "proposal"
    UNDECIDED = "undecided"
    CAPTURE = "capture"
    GENERAL = "general"


@dataclass(frozen=True)
class ContextPacket:
    last_agent_message: str = ""
    last_user_message: str = ""
    build_status: str = ""
    explicit_state: WorkflowState | None = None
    selected_prompt_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Classification:
    state: WorkflowState
    evidence: str


@dataclass(frozen=True)
class RankedPrompt:
    prompt_id: str
    prompt: dict
    score: float
    reason: str
    logical_score: float
    frequency_score: float


@dataclass
class NavigationSession:
    packet: ContextPacket
    ranked: list[RankedPrompt]
    offset: int = 0
    selected_prompt_ids: list[str] = field(default_factory=list)
