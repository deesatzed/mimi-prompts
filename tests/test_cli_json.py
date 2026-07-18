"""Versioned machine-readable navigator contract tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliJsonTests(unittest.TestCase):
    def test_json_suggestions_are_bounded_and_explain_selection(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Path(temp_dir) / "prompts.json"
            subprocess.run(
                [sys.executable, "-m", "minipromptlib.cli", "--storage", str(storage), "seed", "--panel", "seeds.md"],
                cwd=root,
                check=True,
                text=True,
                capture_output=True,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "minipromptlib.cli",
                    "--storage",
                    str(storage),
                    "suggest",
                    "--context",
                    "pytest failed with a traceback",
                    "--json",
                ],
                cwd=root,
                check=False,
                text=True,
                capture_output=True,
            )

        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["state"], "failure")
        self.assertLessEqual(len(payload["suggestions"]), 3)
        self.assertTrue(all("reason" in item for item in payload["suggestions"]))
