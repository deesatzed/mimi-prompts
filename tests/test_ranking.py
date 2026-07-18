"""Logic-plus-frequency ranking invariants."""

from __future__ import annotations

import unittest

from minipromptlib.models import ContextPacket, WorkflowState
from minipromptlib.ranking import rank_prompts


def prompt(prompt_id: str, *, states: list[str], selections: int = 0, text: str = "") -> dict:
    return {
        "id": prompt_id,
        "name": prompt_id,
        "prompt_text": text or "Guide the current workflow.",
        "description": "",
        "tags": ["workflow"],
        "workflow_states": states,
        "selection_count": selections,
    }


class RankingTests(unittest.TestCase):
    def test_frequency_breaks_a_same_state_relevance_tie(self) -> None:
        packet = ContextPacket(explicit_state=WorkflowState.QUESTION)
        ranked = rank_prompts(
            packet,
            [
                prompt("low", states=["question"], selections=1),
                prompt("high", states=["question"], selections=12),
            ],
        )

        self.assertEqual(ranked[0].prompt_id, "high")
        self.assertGreater(ranked[0].frequency_score, ranked[1].frequency_score)

    def test_irrelevant_frequency_cannot_beat_clear_workflow_match(self) -> None:
        packet = ContextPacket(build_status="pytest failed")
        ranked = rank_prompts(
            packet,
            [
                prompt("popular-completion", states=["completion"], selections=1000),
                prompt("new-failure", states=["failure"], selections=0),
            ],
        )

        self.assertEqual(ranked[0].prompt_id, "new-failure")

    def test_ranking_explains_state_and_frequency(self) -> None:
        packet = ContextPacket(explicit_state=WorkflowState.UNDECIDED)
        ranked = rank_prompts(packet, [prompt("tabletop", states=["undecided"], selections=3)])

        self.assertIn("undecided", ranked[0].reason)
        self.assertIn("used 3x", ranked[0].reason)
