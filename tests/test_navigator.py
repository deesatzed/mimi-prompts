"""Numbered workflow navigation sessions."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core import MiniPromptLibrary
from minipromptlib.models import ContextPacket, WorkflowState
from minipromptlib.navigator import InvalidChoiceError, WorkflowNavigator


class NavigatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.library = MiniPromptLibrary(Path(self.temp_dir.name) / "prompts.json")
        for number in range(4):
            prompt_id = self.library.save_mini_prompt(
                f"Checkpoint prompt {number}", name=f"checkpoint-{number}"
            )
            self.library.prompts[prompt_id]["workflow_states"] = ["checkpoint"]
        self.library._save()
        self.navigator = WorkflowNavigator(self.library)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_selecting_number_records_frequency_once(self) -> None:
        session = self.navigator.start(ContextPacket(explicit_state=WorkflowState.CHECKPOINT))

        selected = self.navigator.select(session, 1)

        self.assertEqual(selected.prompt_id, "checkpoint-0")
        self.assertEqual(self.library.get_prompt(selected.prompt_id)["selection_count"], 1)
        self.assertEqual(session.selected_prompt_ids, [selected.prompt_id])

    def test_more_returns_next_non_repeating_page(self) -> None:
        session = self.navigator.start(ContextPacket(explicit_state=WorkflowState.CHECKPOINT))
        first = self.navigator.current_page(session)
        second = self.navigator.more(session)

        self.assertEqual(len(first), 3)
        self.assertEqual(len(second), 1)
        self.assertFalse({item.prompt_id for item in first} & {item.prompt_id for item in second})

    def test_can_more_is_false_on_the_final_page(self) -> None:
        session = self.navigator.start(ContextPacket(explicit_state=WorkflowState.CHECKPOINT))

        self.assertTrue(self.navigator.can_more(session))
        self.navigator.more(session)

        self.assertFalse(self.navigator.can_more(session))

    def test_try_again_replaces_context_and_resets_page(self) -> None:
        session = self.navigator.start(ContextPacket(explicit_state=WorkflowState.CHECKPOINT))
        self.navigator.more(session)

        updated = self.navigator.try_again(session, ContextPacket(explicit_state=WorkflowState.CHECKPOINT))

        self.assertIs(updated, session)
        self.assertEqual(session.offset, 0)

    def test_preview_and_back_do_not_create_extra_selection(self) -> None:
        session = self.navigator.start(ContextPacket(explicit_state=WorkflowState.CHECKPOINT))
        selected = self.navigator.select(session, 1)
        self.navigator.nested_page(session)

        preview = self.navigator.composition_preview(session)
        self.navigator.back(session)

        self.assertIn("Checkpoint prompt 0", preview)
        self.assertEqual(session.selected_prompt_ids, [])
        self.assertEqual(self.library.get_prompt(selected.prompt_id)["selection_count"], 1)
        self.assertEqual(len(self.navigator.current_page(session)), 3)
        self.assertIn(selected.prompt_id, {item.prompt_id for item in self.navigator.current_page(session)})

    def test_invalid_number_keeps_current_page(self) -> None:
        session = self.navigator.start(ContextPacket(explicit_state=WorkflowState.CHECKPOINT))

        with self.assertRaises(InvalidChoiceError):
            self.navigator.select(session, 4)

        self.assertEqual(session.offset, 0)
