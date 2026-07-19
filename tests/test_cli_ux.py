"""User-visible small-page CLI workflow tests."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliUxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        seeded = subprocess.run(
            [
                sys.executable,
                "-m",
                "minipromptlib.cli",
                "--storage",
                str(self.storage),
                "seed",
                "--panel",
                "seeds.md",
            ],
            cwd=self.root,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(seeded.returncode, 0, seeded.stderr)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_suggest_renders_at_most_three_numbered_choices(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "minipromptlib.cli",
                "--storage",
                str(self.storage),
                "suggest",
                "--context",
                "Not sure, lets run through scenarios before deciding.",
            ],
            cwd=self.root,
            check=False,
            text=True,
            capture_output=True,
        )

        numbered = [line for line in result.stdout.splitlines() if line[:2] in {"1.", "2.", "3."}]
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreaterEqual(len(numbered), 1)
        self.assertLessEqual(len(numbered), 3)
        self.assertIn("State: undecided", result.stdout)

    def test_choice_returns_prompt_and_records_selection(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "minipromptlib.cli",
                "--storage",
                str(self.storage),
                "suggest",
                "--context",
                "Not sure, lets run through scenarios before deciding.",
                "--choice",
                "1",
            ],
            cwd=self.root,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Selected:", result.stdout)
        self.assertIn("not sure", result.stdout)

    def test_interactive_more_uses_a_second_small_page(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "minipromptlib.cli",
                "--storage",
                str(self.storage),
                "suggest",
                "--state",
                "checkpoint",
                "--interactive",
            ],
            cwd=self.root,
            check=False,
            text=True,
            input="m\nq\n",
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Page 2", result.stdout)

    def test_empty_store_suggests_seed_without_mutating_storage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Path(temp_dir) / "empty.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "minipromptlib.cli",
                    "--storage",
                    str(storage),
                    "suggest",
                    "--context",
                    "I am not sure what to do next",
                ],
                cwd=self.root,
                check=False,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No saved prompts yet", result.stdout)
            self.assertIn("mini seed --panel seeds.md", result.stdout)
            self.assertFalse(storage.exists())

    def test_interactive_more_reports_when_results_are_exhausted(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "minipromptlib.cli",
                "--storage",
                str(self.storage),
                "suggest",
                "--state",
                "failure",
                "--interactive",
            ],
            cwd=self.root,
            check=False,
            text=True,
            input="m\nq\n",
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No more matching prompts", result.stdout)

    def test_interactive_nesting_exposes_preview_compose_and_back(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "minipromptlib.cli",
                "--storage",
                str(self.storage),
                "suggest",
                "--state",
                "checkpoint",
                "--interactive",
            ],
            cwd=self.root,
            check=False,
            text=True,
            input="1\nn\n1\np\nb\nc\nq\n",
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[n] nest", result.stdout)
        self.assertIn("Composition preview:", result.stdout)
        self.assertIn("Composed mini-prompt:", result.stdout)
        self.assertIn("Backed out of", result.stdout)
