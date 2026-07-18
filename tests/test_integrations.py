"""Reference adapters must use the shared bounded JSON contract."""

from __future__ import annotations

import unittest
from pathlib import Path


class IntegrationTests(unittest.TestCase):
    def test_reference_adapters_use_json_suggest_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        paths = [
            root / "integrations/codex/miniprompt-navigator/SKILL.md",
            root / "integrations/claude/mini.md",
        ]

        for path in paths:
            content = path.read_text(encoding="utf-8")
            self.assertIn("mini suggest --json", content)
            self.assertIn("at most three", content.lower())
            self.assertIn("bounded context", content.lower())
            self.assertIn("must not", content.lower())
