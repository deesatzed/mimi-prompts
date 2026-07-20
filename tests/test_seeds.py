"""Deterministic loading of the user-authored seed panel."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core import MiniPromptLibrary
from minipromptlib.seeds import default_seed_panel, load_seed_panel, seed_library


class SeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_every_numbered_seed_is_loaded_with_unique_metadata(self) -> None:
        source = (self.root / "seeds.md").read_text(encoding="utf-8")
        expected_count = len(re.findall(r"^###\s+[0-9]+\.", source, re.MULTILINE))

        seeds = load_seed_panel(self.root / "seeds.md")

        self.assertEqual(len(seeds), expected_count)
        self.assertEqual(len({seed["name"] for seed in seeds}), expected_count)
        self.assertTrue(all(seed["prompt_text"] for seed in seeds))
        self.assertTrue(all(seed["workflow_states"] for seed in seeds))

    def test_uncertainty_seed_preserves_authored_wording_and_state(self) -> None:
        seeds = load_seed_panel(self.root / "seeds.md")
        uncertainty = next(seed for seed in seeds if seed["number"] == 32)

        self.assertIn("user friendly", uncertainty["prompt_text"])
        self.assertIn("undecided", uncertainty["workflow_states"])

    def test_repeat_seeding_is_idempotent_without_overwrite(self) -> None:
        library = MiniPromptLibrary(self.storage)
        first = seed_library(library, self.root / "seeds.md")
        second = seed_library(library, self.root / "seeds.md")

        self.assertEqual(first, 34)
        self.assertEqual(second, 0)
        self.assertEqual(len(library), 34)

    def test_root_seed_script_loads_the_authored_panel(self) -> None:
        result = subprocess.run(
            [sys.executable, "seeds.py", "--storage", str(self.storage)],
            cwd=self.root,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Seeded 34 prompt(s).", result.stdout)

    def test_packaged_seed_panel_has_all_authored_prompts(self) -> None:
        panel = default_seed_panel()

        self.assertTrue(panel.is_file())
        self.assertEqual(len(load_seed_panel(panel)), 34)

    def test_seeded_prompts_display_their_authored_human_title(self) -> None:
        library = MiniPromptLibrary(self.storage)
        seed_library(library, self.root / "seeds.md")

        entry = library.get_prompt("seed-01-explain-it-simply")

        self.assertEqual(entry["name"], "Explain It Simply")
        self.assertNotEqual(entry["name"], entry["id"])

    def test_reseeding_refreshes_display_title_idempotently(self) -> None:
        library = MiniPromptLibrary(self.storage)
        seed_library(library, self.root / "seeds.md")
        library.prompts["seed-01-explain-it-simply"]["name"] = "Manually Renamed"
        library._save()

        inserted = seed_library(library, self.root / "seeds.md")

        self.assertEqual(inserted, 0)
        self.assertEqual(
            library.get_prompt("seed-01-explain-it-simply")["name"], "Explain It Simply"
        )
