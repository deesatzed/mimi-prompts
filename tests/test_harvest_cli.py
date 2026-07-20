"""CLI surface for mini harvest: consent, no-scrape input, and dedupe offers."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class HarvestCliTests(unittest.TestCase):
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

    def test_json_mode_never_saves(self) -> None:
        before = json.loads(self._run("folders", "--json").stdout)

        result = self._run(
            "harvest", "--text",
            "Always check for race conditions before approving any async PR.",
            "--json",
        )
        after = json.loads(self._run("folders", "--json").stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["version"], 1)
        self.assertEqual(len(payload["candidates"]), 1)
        self.assertEqual(before, after)

    def test_no_content_provided_fails_clearly(self) -> None:
        result = self._run("harvest", "--text", "   ")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No content provided", result.stderr)

    def test_skip_saves_nothing(self) -> None:
        before = json.loads(self._run("folders", "--json").stdout)

        result = self._run(
            "harvest", "--text",
            "Always check for race conditions before approving any async PR.",
            input_text="s\n",
        )
        after = json.loads(self._run("folders", "--json").stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0 saved, 1 skipped", result.stdout)
        self.assertEqual(before, after)

    def test_save_generalized_persists_with_recommended_folder(self) -> None:
        result = self._run(
            "harvest", "--text",
            "Always check the acme-billing-service config before deploying it anywhere.",
            input_text="g\ny\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 saved, 0 skipped", result.stdout)
        listing = self._run("list", "--search", "config before deploying", "--limit", "10")
        self.assertIn("check", listing.stdout.lower())

    def test_save_original_keeps_verbatim_text(self) -> None:
        text = "Always check the acme-billing-service config before deploying it anywhere."
        result = self._run("harvest", "--text", text, input_text="o\ny\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        listing = self._run("list", "--search", "acme-billing-service", "--limit", "10")
        self.assertIn("acme-billing-service", listing.stdout)

    def test_edit_lets_user_override_the_saved_text(self) -> None:
        text = "Always check the acme-billing-service config before deploying it anywhere."
        result = self._run(
            "harvest", "--text", text,
            input_text="e\nA completely different final version\ny\n",
        )
        saved_id = result.stdout.split("Saved: ", 1)[1].splitlines()[0].strip()

        self.assertEqual(result.returncode, 0, result.stderr)
        fetched = self._run("get", saved_id)
        self.assertEqual(fetched.stdout.strip(), "A completely different final version")

    def test_duplicate_offers_update_or_variant_and_does_not_force_either(self) -> None:
        near_duplicate = (
            "Never skip this: Identify the most important edge cases for a workflow or feature, "
            "including incomplete data, incorrect permissions, unusual environments, "
            "interrupted operations, novice mistakes, and conflicting settings."
        )

        result = self._run("harvest", "--text", near_duplicate, input_text="s\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Similar existing", result.stdout)
        self.assertIn("pdate existing", result.stdout)
        self.assertIn("ariant", result.stdout)

    def test_folder_override_is_honored(self) -> None:
        text = "Always check the acme-billing-service config before deploying it anywhere."
        result = self._run(
            "harvest", "--text", text,
            input_text="f\ncustom/folder\ny\ny\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        listing = self._run("list", "--folder", "custom/folder", "--limit", "10")
        self.assertNotIn("No prompts found", listing.stdout)


if __name__ == "__main__":
    unittest.main()
