"""Progressive small-page ranking behavior."""

from __future__ import annotations

import unittest

from minipromptlib.models import ContextPacket, WorkflowState
from minipromptlib.ranking import page_ranked_prompts, rank_prompts


class PaginationTests(unittest.TestCase):
    def test_pages_are_limited_stable_and_non_repeating(self) -> None:
        prompts = [
            {
                "id": f"prompt-{number}",
                "name": f"prompt-{number}",
                "prompt_text": "Review this workflow.",
                "description": "",
                "tags": ["workflow"],
                "workflow_states": ["checkpoint"],
                "selection_count": number,
            }
            for number in range(7)
        ]
        ranked = rank_prompts(ContextPacket(explicit_state=WorkflowState.CHECKPOINT), prompts)

        first = page_ranked_prompts(ranked, offset=0)
        second = page_ranked_prompts(ranked, offset=3)
        third = page_ranked_prompts(ranked, offset=6)

        self.assertLessEqual(len(first), 3)
        self.assertLessEqual(len(second), 3)
        self.assertEqual(len(third), 1)
        self.assertFalse({item.prompt_id for item in first} & {item.prompt_id for item in second})
