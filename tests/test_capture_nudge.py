"""Capture nudge: interactive loop asks about reusable-rule-shaped context, never saves."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CaptureNudgeCliTests(unittest.TestCase):
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

    def test_nudge_appears_for_rule_shaped_initial_context(self) -> None:
        result = self._run(
            "suggest", "--state", "checkpoint",
            "--context", "Always check for race conditions before approving async PRs",
            "--interactive", input_text="q\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reusable rule", result.stdout)

    def test_no_nudge_for_ordinary_context(self) -> None:
        result = self._run(
            "suggest", "--state", "checkpoint",
            "--context", "reviewing the current release notes",
            "--interactive", input_text="q\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("reusable rule", result.stdout)

    def test_nudge_never_saves_anything(self) -> None:
        before = self._run("folders", "--json").stdout

        self._run(
            "suggest", "--state", "checkpoint",
            "--context", "Always check for race conditions before approving async PRs",
            "--interactive", input_text="q\n",
        )

        after = self._run("folders", "--json").stdout
        self.assertEqual(before, after)

    def test_nudge_on_retry_appears_at_most_once_per_session(self) -> None:
        result = self._run(
            "suggest", "--state", "checkpoint", "--interactive",
            input_text=(
                "r\nAlways check for race conditions before approving PRs\n"
                "r\nNever skip the review step before merging\n"
                "q\n"
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("reusable rule"), 1)


if __name__ == "__main__":
    unittest.main()
