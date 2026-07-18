"""Persistence safety tests for the local prompt library."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core import MiniPromptLibrary
from minipromptlib.storage import StorageCorruptionError


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_corrupt_store_raises_without_replacing_source_bytes(self) -> None:
        source = "{broken"
        self.storage.write_text(source, encoding="utf-8")

        with self.assertRaises(StorageCorruptionError):
            MiniPromptLibrary(self.storage)

        self.assertEqual(self.storage.read_text(encoding="utf-8"), source)

    def test_legacy_prompt_dictionary_loads_and_upgrades_on_next_write(self) -> None:
        legacy = {
            "legacy": {
                "id": "legacy",
                "name": "legacy",
                "prompt_text": "Keep old prompts usable.",
                "tags": [],
                "category": "general",
            }
        }
        self.storage.write_text(json.dumps(legacy), encoding="utf-8")

        library = MiniPromptLibrary(self.storage)
        library.save_mini_prompt("A new prompt", name="new")

        self.assertEqual(library.get_prompt("legacy")["prompt_text"], "Keep old prompts usable.")
        saved = json.loads(self.storage.read_text(encoding="utf-8"))
        self.assertEqual(saved["schema_version"], 2)
        self.assertIn("legacy", saved["prompts"])

    def test_save_leaves_no_partial_json_or_temporary_file(self) -> None:
        library = MiniPromptLibrary(self.storage)
        library.save_mini_prompt("Atomically stored", name="atomic")

        saved = json.loads(self.storage.read_text(encoding="utf-8"))
        self.assertIn("atomic", saved["prompts"])
        self.assertEqual(list(self.storage.parent.glob(f".{self.storage.name}.*.tmp")), [])
