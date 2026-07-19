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
            root / "integrations/claude/miniprompt-navigator/SKILL.md",
            root / "integrations/cursor/miniprompt-navigator.mdc",
        ]

        for path in paths:
            content = path.read_text(encoding="utf-8")
            self.assertIn("mini suggest --json", content)
            self.assertIn("at most three", content.lower())
            self.assertIn("bounded context", content.lower())
            self.assertIn("must not", content.lower())

    def test_public_host_guides_label_adapter_maturity(self) -> None:
        root = Path(__file__).resolve().parents[1]
        expected = {
            "codex.md": "copyable project template",
            "claude-code.md": "copyable project template",
            "cursor.md": "copyable project template",
            "local-agents.md": "verified",
            "grok.md": "manual fallback",
        }

        for name, label in expected.items():
            content = (root / "docs/hosts" / name).read_text(encoding="utf-8").lower()
            self.assertIn(label, content)
            self.assertIn("mini suggest --json", content)
            self.assertIn("bounded context", content)
