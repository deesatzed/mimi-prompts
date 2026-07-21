"""Folder taxonomy: assignment, filtering, and the folders CLI surface."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core import MiniPromptLibrary
from minipromptlib.seeds import default_folder_for_seed, seed_library


class FolderCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        self.library = MiniPromptLibrary(self.storage)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_save_defaults_folder_to_category_when_unspecified(self) -> None:
        prompt_id = self.library.save_mini_prompt("Text", name="p1", category="planning")

        self.assertEqual(self.library.get_prompt(prompt_id)["folder"], "planning")

    def test_save_accepts_an_explicit_folder(self) -> None:
        prompt_id = self.library.save_mini_prompt("Text", name="p1", folder="review/async")

        self.assertEqual(self.library.get_prompt(prompt_id)["folder"], "review/async")

    def test_edit_prompt_updates_folder(self) -> None:
        prompt_id = self.library.save_mini_prompt("Text", name="p1", folder="general")

        updated = self.library.edit_prompt(prompt_id, folder="ship/handoff")

        self.assertEqual(updated["folder"], "ship/handoff")

    def test_edit_prompt_rejects_empty_folder(self) -> None:
        prompt_id = self.library.save_mini_prompt("Text", name="p1")

        with self.assertRaises(ValueError):
            self.library.edit_prompt(prompt_id, folder="   ")

    def test_list_folders_counts_by_folder(self) -> None:
        self.library.save_mini_prompt("A", name="a", folder="review/async")
        self.library.save_mini_prompt("B", name="b", folder="review/async")
        self.library.save_mini_prompt("C", name="c", folder="ship/handoff")

        counts = self.library.list_folders()

        self.assertEqual(counts, {"review/async": 2, "ship/handoff": 1})

    def test_list_prompts_folder_filter_matches_exact_and_nested(self) -> None:
        self.library.save_mini_prompt("A", name="a", folder="review/async")
        self.library.save_mini_prompt("B", name="b", folder="review")
        self.library.save_mini_prompt("C", name="c", folder="ship/handoff")

        under_review = self.library.list_prompts(folder="review")

        self.assertEqual({p["id"] for p in under_review}, {"a", "b"})

    def test_seed_folders_are_all_assigned_and_no_seed_falls_back_to_general(self) -> None:
        for number in range(1, 42):
            self.assertNotEqual(default_folder_for_seed(number), "general", f"seed {number} has no authored folder")

    def test_seeding_assigns_the_authored_folder(self) -> None:
        root = Path(__file__).resolve().parents[1]
        seed_library(self.library, root / "seeds.md")

        entry = self.library.get_prompt("seed-01-explain-it-simply")

        self.assertEqual(entry["folder"], "explain/simplify")


class FolderCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "minipromptlib.cli", "--storage", str(self.storage), *args],
            cwd=self.root, check=False, text=True, capture_output=True,
        )

    def test_folders_on_empty_store_guides_to_seed(self) -> None:
        result = self._run("folders")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mini seed", result.stdout)

    def test_folders_json_reports_counts_after_seeding(self) -> None:
        self._run("seed", "--panel", "seeds.md")

        result = self._run("folders", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        counts = json.loads(result.stdout)
        self.assertEqual(sum(counts.values()), 41)
        self.assertIn("explain/simplify", counts)

    def test_list_folder_filter_narrows_results(self) -> None:
        self._run("seed", "--panel", "seeds.md")

        result = self._run("list", "--folder", "review", "--limit", "50")

        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertGreater(len(lines), 0)


if __name__ == "__main__":
    unittest.main()
