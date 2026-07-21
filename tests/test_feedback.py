"""Outcome feedback loop: mini feedback, mini stats, and the interactive quit prompt."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class FeedbackCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        subprocess.run(
            [sys.executable, "-m", "minipromptlib.cli", "--storage", str(self.storage), "seed", "--panel", "seeds.md"],
            cwd=self.root, check=True, text=True, capture_output=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run(self, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "minipromptlib.cli", "--storage", str(self.storage), *args],
            cwd=self.root, check=False, text=True, capture_output=True, input=input_text,
        )

    def test_feedback_requires_a_direction(self) -> None:
        result = self._run("feedback", "seed-09-contrarian-product-review")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--helped or --not-helped", result.stderr)

    def test_feedback_rejects_both_directions_at_once(self) -> None:
        result = self._run("feedback", "seed-09-contrarian-product-review", "--helped", "--not-helped")

        self.assertNotEqual(result.returncode, 0)

    def test_feedback_unknown_prompt_fails_clearly(self) -> None:
        result = self._run("feedback", "does-not-exist", "--helped")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr)

    def test_helped_and_not_helped_both_record(self) -> None:
        self._run("feedback", "seed-09-contrarian-product-review", "--helped")
        result = self._run("feedback", "seed-09-contrarian-product-review", "--not-helped")

        self.assertEqual(result.returncode, 0, result.stderr)
        fetched_stats = self._run("stats")
        self.assertIn("total feedback: 2", fetched_stats.stdout)

    def test_stats_on_empty_store_guides_to_seed(self) -> None:
        empty_dir = tempfile.TemporaryDirectory()
        try:
            empty_storage = Path(empty_dir.name) / "empty.json"
            result = subprocess.run(
                [sys.executable, "-m", "minipromptlib.cli", "--storage", str(empty_storage), "stats"],
                cwd=self.root, check=False, text=True, capture_output=True,
            )
            self.assertIn("mini seed", result.stdout)
            self.assertFalse(empty_storage.exists())
        finally:
            empty_dir.cleanup()

    def test_stats_surfaces_underperforming_prompts_with_a_hint(self) -> None:
        for _ in range(3):
            self._run("feedback", "seed-09-contrarian-product-review", "--not-helped")

        result = self._run("stats")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Underperforming", result.stdout)
        self.assertIn("seed-09-contrarian-product-review", result.stdout)
        self.assertIn("mini improve seed-09-contrarian-product-review", result.stdout)

    def test_stats_reports_no_underperformers_when_none_qualify(self) -> None:
        result = self._run("stats")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No underperforming prompts", result.stdout)

    def test_interactive_quit_asks_feedback_for_each_selection(self) -> None:
        result = self._run(
            "suggest", "--state", "checkpoint", "--interactive",
            input_text="1\nq\ny\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("help? [y/n/skip]", result.stdout)
        stats = self._run("stats")
        self.assertIn("total feedback: 1", stats.stdout)

    def test_interactive_quit_skip_records_nothing(self) -> None:
        result = self._run(
            "suggest", "--state", "checkpoint", "--interactive",
            input_text="1\nq\nskip\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        stats = self._run("stats")
        self.assertIn("total feedback: 0", stats.stdout)

    def test_interactive_quit_without_any_selection_asks_nothing(self) -> None:
        result = self._run(
            "suggest", "--state", "checkpoint", "--interactive",
            input_text="q\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("help? [y/n/skip]", result.stdout)


if __name__ == "__main__":
    unittest.main()
