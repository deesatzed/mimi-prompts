"""Prompt lifecycle: delete, rename, and edit — both the core API and the CLI."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core import MiniPromptLibrary


class LifecycleCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        self.library = MiniPromptLibrary(storage_path=self.storage)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_delete_prompt_removes_it_and_returns_the_removed_entry(self) -> None:
        prompt_id = self.library.save_mini_prompt("Delete me", name="doomed")

        removed = self.library.delete_prompt(prompt_id)

        self.assertEqual(removed["id"], "doomed")
        self.assertIsNone(self.library.get_prompt("doomed"))
        self.assertEqual(len(self.library), 0)

    def test_delete_unknown_prompt_returns_none(self) -> None:
        self.assertIsNone(self.library.delete_prompt("does-not-exist"))

    def test_rename_prompt_changes_display_name_not_id(self) -> None:
        prompt_id = self.library.save_mini_prompt("Some text", name="original-id")

        updated = self.library.rename_prompt(prompt_id, "A Nicer Title")

        self.assertEqual(updated["id"], "original-id")
        self.assertEqual(updated["name"], "A Nicer Title")
        self.assertEqual(self.library.get_prompt("original-id")["name"], "A Nicer Title")

    def test_rename_refuses_collision_without_overwrite(self) -> None:
        self.library.save_mini_prompt("First", name="first-id")
        self.library.prompts["first-id"]["name"] = "Shared Title"
        self.library._save()
        self.library.save_mini_prompt("Second", name="second-id")

        with self.assertRaises(ValueError):
            self.library.rename_prompt("second-id", "Shared Title")

        self.library.rename_prompt("second-id", "Shared Title", overwrite=True)
        self.assertEqual(self.library.get_prompt("second-id")["name"], "Shared Title")

    def test_edit_prompt_mutates_only_supplied_fields(self) -> None:
        prompt_id = self.library.save_mini_prompt(
            "Original text", name="editable", tags=["a"], category="general", description="orig"
        )

        updated = self.library.edit_prompt(prompt_id, tags=["b", "c"])

        self.assertEqual(updated["prompt_text"], "Original text")
        self.assertEqual(updated["description"], "orig")
        self.assertEqual(updated["tags"], ["b", "c"])
        self.assertEqual(updated["version"], 2)

    def test_edit_prompt_rejects_empty_text(self) -> None:
        prompt_id = self.library.save_mini_prompt("Original text", name="editable2")

        with self.assertRaises(ValueError):
            self.library.edit_prompt(prompt_id, prompt_text="   ")

    def test_edit_unknown_prompt_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.library.edit_prompt("nope", description="x")


class LifecycleCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        subprocess.run(
            [
                sys.executable, "-m", "minipromptlib.cli", "--storage", str(self.storage),
                "save", "Keep or remove me", "--name", "target",
            ],
            cwd=self.root, check=True, text=True, capture_output=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run(self, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "minipromptlib.cli", "--storage", str(self.storage), *args],
            cwd=self.root, check=False, text=True, capture_output=True, input=input_text,
        )

    def test_rm_requires_confirmation_by_default(self) -> None:
        result = self._run("rm", "target", input_text="n\n")
        still_there = self._run("get", "target")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Not deleted", result.stdout)
        self.assertEqual(still_there.returncode, 0)

    def test_rm_yes_deletes_without_prompting(self) -> None:
        result = self._run("rm", "target", "--yes")
        gone = self._run("get", "target")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Deleted: target", result.stdout)
        self.assertNotEqual(gone.returncode, 0)

    def test_rm_unknown_id_fails_clearly(self) -> None:
        result = self._run("rm", "missing", "--yes")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr)

    def test_rename_updates_display_name(self) -> None:
        result = self._run("rename", "target", "A Better Title")
        listing = self._run("list")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("A Better Title", result.stdout)
        self.assertIn("A Better Title", listing.stdout)

    def test_edit_updates_text(self) -> None:
        result = self._run("edit", "target", "--text", "New text entirely")
        fetched = self._run("get", "target")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(fetched.stdout.strip(), "New text entirely")

    def test_edit_with_no_fields_fails_clearly(self) -> None:
        result = self._run("edit", "target")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Nothing to edit", result.stderr)


if __name__ == "__main__":
    unittest.main()
