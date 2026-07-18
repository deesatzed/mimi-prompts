"""Workflow-state classification from bounded AI context."""

from __future__ import annotations

import unittest

from minipromptlib.classifier import classify_workflow_state
from minipromptlib.models import ContextPacket, WorkflowState


class ClassifierTests(unittest.TestCase):
    def test_explicit_state_overrides_inference(self) -> None:
        packet = ContextPacket(
            last_agent_message="The tests failed. What should we do?",
            explicit_state=WorkflowState.COMPLETION,
        )

        result = classify_workflow_state(packet)

        self.assertEqual(result.state, WorkflowState.COMPLETION)
        self.assertEqual(result.evidence, "explicit workflow state")

    def test_unsure_user_prefers_undecided_over_agent_question(self) -> None:
        packet = ContextPacket(
            last_agent_message="Which product direction should we choose?",
            last_user_message="Not sure, lets run through scenarios or tabletops and then decide.",
        )

        result = classify_workflow_state(packet)

        self.assertEqual(result.state, WorkflowState.UNDECIDED)

    def test_failed_build_is_classified_as_failure(self) -> None:
        packet = ContextPacket(build_status="pytest failed: 2 tests failed")

        result = classify_workflow_state(packet)

        self.assertEqual(result.state, WorkflowState.FAILURE)

    def test_completed_task_is_classified_as_completion(self) -> None:
        packet = ContextPacket(last_agent_message="The task list is complete; all checks passed.")

        result = classify_workflow_state(packet)

        self.assertEqual(result.state, WorkflowState.COMPLETION)

    def test_empty_context_falls_back_to_general(self) -> None:
        result = classify_workflow_state(ContextPacket())

        self.assertEqual(result.state, WorkflowState.GENERAL)
