"""Deterministic detect/generalize/file/dedupe pipeline for mini harvest."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core import MiniPromptLibrary
from minipromptlib.harvest import (
    build_drafts,
    detect_candidates,
    find_duplicate,
    generalize_text,
    recommend_folder,
)
from minipromptlib.seeds import seed_library


class DetectTests(unittest.TestCase):
    def test_empty_text_yields_no_candidates(self) -> None:
        self.assertEqual(detect_candidates(""), [])
        self.assertEqual(detect_candidates("   "), [])

    def test_finds_imperative_instructions_and_skips_narration(self) -> None:
        text = (
            "Always check for race conditions before approving any async PR. "
            "I was thinking about lunch today. "
            "Never merge without running the full test suite first. "
            "Thanks for the help earlier."
        )

        candidates = detect_candidates(text)

        texts = [c.original_text for c in candidates]
        self.assertEqual(len(candidates), 2)
        self.assertTrue(any("race conditions" in t for t in texts))
        self.assertTrue(any("test suite" in t for t in texts))
        self.assertFalse(any("lunch" in t for t in texts))
        self.assertFalse(any("Thanks" in t for t in texts))

    def test_short_and_long_sentences_are_excluded(self) -> None:
        too_short = "Always do it."
        too_long = "Always " + ("check this thing and that thing and another thing " * 20)

        self.assertEqual(detect_candidates(too_short), [] if len(too_short) < 25 else detect_candidates(too_short))
        self.assertEqual(detect_candidates(too_long), [])

    def test_duplicate_sentences_are_only_reported_once(self) -> None:
        text = "Always run the linter before committing. Always run the linter before committing."

        candidates = detect_candidates(text)

        self.assertEqual(len(candidates), 1)

    def test_no_instruction_shaped_text_yields_no_candidates(self) -> None:
        text = "The weather was nice yesterday and we went for a walk in the park together."

        self.assertEqual(detect_candidates(text), [])


class GeneralizeTests(unittest.TestCase):
    def test_kebab_project_identifiers_with_three_or_more_segments_are_parameterized(self) -> None:
        text, changes = generalize_text("Check the acme-billing-service config before deploying.")

        self.assertIn("{project}", text)
        self.assertTrue(any("acme-billing-service" in c for c in changes))

    def test_two_segment_kebab_compound_words_are_left_alone(self) -> None:
        text, changes = generalize_text("Always review the edge-case handling in real-time systems.")

        self.assertNotIn("{project}", text)
        self.assertEqual(changes, [])

    def test_file_paths_and_versions_are_parameterized(self) -> None:
        text, changes = generalize_text("Update config.py to use version 2.4.1 of the SDK.")

        self.assertIn("{file}", text)
        self.assertIn("{version}", text)
        self.assertEqual(len(changes), 2)

    def test_camel_case_identifiers_are_parameterized(self) -> None:
        text, changes = generalize_text("Make sure myProjectName passes CI.")

        self.assertIn("{project}", text)

    def test_plain_text_with_nothing_specific_is_unchanged(self) -> None:
        text, changes = generalize_text("Always check for edge cases before shipping.")

        self.assertEqual(text, "Always check for edge cases before shipping.")
        self.assertEqual(changes, [])


class FolderAndDedupeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        self.library = MiniPromptLibrary(self.storage)
        root = Path(__file__).resolve().parents[1]
        seed_library(self.library, root / "seeds.md")
        self.prompts = self.library.list_prompts(limit=1000)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_recommend_folder_matches_high_overlap_with_high_confidence(self) -> None:
        recommendation = recommend_folder(
            "Identify the primary user for a feature before building it.", self.prompts
        )

        self.assertEqual(recommendation.folder, "discover/user")
        self.assertEqual(recommendation.confidence, "high")

    def test_recommend_folder_proposes_new_folder_when_nothing_overlaps(self) -> None:
        recommendation = recommend_folder("Xyzzy plugh frobnicate quux wibble.", self.prompts)

        self.assertTrue(recommendation.folder.startswith("captured/"))
        self.assertEqual(recommendation.confidence, "low")

    def test_recommend_folder_handles_empty_text(self) -> None:
        recommendation = recommend_folder("   ", self.prompts)

        self.assertEqual(recommendation.folder, "general")
        self.assertEqual(recommendation.confidence, "low")

    def test_find_duplicate_matches_near_verbatim_text(self) -> None:
        near_duplicate = (
            "Identify the most important edge cases for `[workflow or feature]`, "
            "including incomplete data, incorrect permissions, unusual environments, "
            "interrupted operations, novice mistakes, and conflicting settings."
        )

        match = find_duplicate(near_duplicate, self.prompts)

        self.assertIsNotNone(match)
        self.assertEqual(match.prompt_id, "seed-25-edge-case-review")
        self.assertGreaterEqual(match.overlap, 0.6)

    def test_find_duplicate_returns_none_for_novel_text(self) -> None:
        match = find_duplicate("Completely unrelated novel instruction about pastry baking.", self.prompts)

        self.assertIsNone(match)

    def test_build_drafts_end_to_end_produces_no_writes(self) -> None:
        text = "Always identify the primary user for a feature before building it."

        drafts = build_drafts(text, self.prompts)

        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0].suggested_folder.folder, "discover/user")
        # Nothing was saved: build_drafts never touches the library object.
        self.assertEqual(len(self.library.list_prompts(limit=1000)), 34)

    def test_build_drafts_on_text_with_no_candidates_returns_empty_list(self) -> None:
        drafts = build_drafts("Just some narration about the weekend.", self.prompts)

        self.assertEqual(drafts, [])


if __name__ == "__main__":
    unittest.main()
