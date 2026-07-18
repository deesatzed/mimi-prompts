"""Characterization tests for public MiniPromptLibrary behavior."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core import MiniPromptLibrary


class CoreRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        self.library = MiniPromptLibrary(storage_path=self.storage)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_save_round_trip_preserves_prompt_fields(self) -> None:
        prompt_id = self.library.save_mini_prompt(
            "Walk through scenarios before deciding.",
            name="tabletop-first",
            tags=["workflow", "decision"],
            category="planning",
            description="Use scenarios before committing to a direction.",
        )

        reloaded = MiniPromptLibrary(storage_path=self.storage)
        prompt = reloaded.get_prompt(prompt_id)

        self.assertEqual(prompt_id, "tabletop-first")
        self.assertEqual(prompt["prompt_text"], "Walk through scenarios before deciding.")
        self.assertEqual(prompt["tags"], ["decision", "workflow"])
        self.assertEqual(prompt["category"], "planning")

    def test_duplicate_name_creates_a_versioned_identifier(self) -> None:
        self.library.save_mini_prompt("First version", name="review")
        second_id = self.library.save_mini_prompt("Second version", name="review")

        self.assertEqual(second_id, "review_v2")
        self.assertEqual(self.library.get_prompt(second_id)["prompt_text"], "Second version")

    def test_keyword_selection_works_without_an_llm(self) -> None:
        self.library.save_mini_prompt(
            "Inspect failing tests and isolate the smallest reproducible failure.",
            name="debug-failure",
            tags=["debug", "testing"],
        )
        self.library.save_mini_prompt(
            "Write a decision memo with trade-offs.",
            name="decision-memo",
            tags=["decision"],
        )

        selected = self.library.select_best_for_context("A test is failing during debugging")

        self.assertTrue(selected)
        self.assertEqual(selected[0]["id"], "debug-failure")

    def test_log_usage_tracks_outcomes_separately(self) -> None:
        prompt_id = self.library.save_mini_prompt("Test carefully", name="test-carefully")

        self.library.log_usage(prompt_id, success=True, notes="Caught a regression")
        prompt = self.library.get_prompt(prompt_id)

        self.assertEqual(prompt["usage_count"], 1)
        self.assertEqual(prompt["success_count"], 1)
        self.assertEqual(prompt["failure_count"], 0)
        self.assertTrue(prompt["notes"])

    def test_record_selection_tracks_frequency_without_usage_outcome(self) -> None:
        prompt_id = self.library.save_mini_prompt("Choose deliberately", name="choose")

        self.library.record_selection(prompt_id)
        prompt = self.library.get_prompt(prompt_id)

        self.assertEqual(prompt["selection_count"], 1)
        self.assertEqual(prompt["usage_count"], 0)
        self.assertEqual(prompt["success_count"], 0)

    def test_export_and_import_round_trip(self) -> None:
        prompt_id = self.library.save_mini_prompt("Keep scope narrow", name="scope")
        export_path = Path(self.temp_dir.name) / "export.json"
        self.library.export_library(export_path)

        imported = MiniPromptLibrary(Path(self.temp_dir.name) / "imported.json")
        self.assertEqual(imported.import_library(export_path), 1)
        self.assertEqual(imported.get_prompt(prompt_id)["prompt_text"], "Keep scope narrow")

    def test_direct_cli_save_and_get_use_supplied_storage(self) -> None:
        root = Path(__file__).resolve().parents[1]
        save = subprocess.run(
            [
                sys.executable,
                "cli.py",
                "--storage",
                str(self.storage),
                "save",
                "Use a temporary test store.",
                "--name",
                "temporary",
            ],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
        )
        get = subprocess.run(
            [sys.executable, "cli.py", "--storage", str(self.storage), "get", "temporary"],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(save.returncode, 0, save.stderr)
        self.assertEqual(get.returncode, 0, get.stderr)
        self.assertIn("Use a temporary test store.", get.stdout)
