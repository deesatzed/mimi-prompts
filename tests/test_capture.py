"""Reviewed in-flow capture of new user wording."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core import MiniPromptLibrary
from minipromptlib.capture import create_capture_draft, save_capture_draft


class CaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.library = MiniPromptLibrary(Path(self.temp_dir.name) / "prompts.json")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_draft_does_not_change_storage_before_confirmation(self) -> None:
        draft = create_capture_draft(
            "Not sure, lets run through scenarios or tabletops and then decide."
        )

        self.assertEqual(draft.name, "not-sure-run-through-scenarios-tabletops-decide")
        self.assertIn("undecided", draft.workflow_states)
        self.assertEqual(len(self.library), 0)

    def test_name_is_derived_from_the_text_not_a_hardcoded_special_case(self) -> None:
        draft = create_capture_draft(
            "Always check for race conditions in my async FastAPI handlers "
            "before approving the PR for the acme-billing repo"
        )

        self.assertEqual(draft.name, "always-check-race-conditions-my-async-fastapi-handlers")
        self.assertLessEqual(len(draft.name), 64)
        # No mid-word truncation: every character up to the cut is a whole word.
        self.assertNotIn(draft.name[-1] + "-", draft.name[-2:])

    def test_confirmed_draft_saves_original_wording(self) -> None:
        source = "Walk through the user journey before deciding what to build."
        draft = create_capture_draft(source)

        prompt_id = save_capture_draft(self.library, draft)

        saved = self.library.get_prompt(prompt_id)
        self.assertEqual(saved["prompt_text"], source)
        self.assertEqual(saved["workflow_states"], draft.workflow_states)
