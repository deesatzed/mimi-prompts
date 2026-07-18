"""Public and continuity documentation must match the workflow navigator."""

from __future__ import annotations

import unittest
from pathlib import Path


class DocumentationTests(unittest.TestCase):
    def test_current_docs_describe_verified_workflow_and_limits(self) -> None:
        root = Path(__file__).resolve().parents[1]
        paths = [
            root / "README.md",
            root / "CLAUDE.md",
            root / "HANDOFF.md",
            root / "HANDOFF_2026-07-18.md",
            root / "HANDOFF_LATEST.md",
        ]
        required = ["mini suggest", "selection_count", "34", "offline", "does not"]

        for path in paths:
            text = path.read_text(encoding="utf-8").lower()
            for term in required:
                self.assertIn(term, text, f"{path.name} is missing {term!r}")
