"""Inspectable, deterministic workflow-state classification."""

from __future__ import annotations

from .models import Classification, ContextPacket, WorkflowState


def classify_workflow_state(packet: ContextPacket) -> Classification:
    """Classify the immediate workflow state from bounded supplied context."""
    if packet.explicit_state is not None:
        return Classification(packet.explicit_state, "explicit workflow state")

    user = packet.last_user_message.lower()
    agent = packet.last_agent_message.lower()
    build = packet.build_status.lower()
    combined = " ".join((user, agent, build))

    if any(term in user for term in ("not sure", "unsure", "tabletop", "scenarios")):
        return Classification(WorkflowState.UNDECIDED, "user uncertainty language")
    if any(term in build for term in ("failed", "failure", "error", "traceback")) or any(
        term in combined for term in ("build failed", "test failed", "tests failed")
    ):
        return Classification(WorkflowState.FAILURE, "build or test failure language")
    if any(term in combined for term in ("task list is complete", "all checks passed", "completed", "finished")):
        return Classification(WorkflowState.COMPLETION, "completion language")
    if any(term in user for term in ("save this", "add this prompt", "make this a mini-prompt")):
        return Classification(WorkflowState.CAPTURE, "prompt capture language")
    if any(term in combined for term in ("review this section", "section is done", "checkpoint")):
        return Classification(WorkflowState.CHECKPOINT, "checkpoint language")
    if any(term in combined for term in ("new feature", "product direction", "scope", "proposal", "should we add")):
        return Classification(WorkflowState.PROPOSAL, "proposal language")
    if "?" in agent or any(term in agent for term in ("which", "what should", "can you clarify")):
        return Classification(WorkflowState.QUESTION, "agent question language")
    return Classification(WorkflowState.GENERAL, "no strong workflow-state evidence")
