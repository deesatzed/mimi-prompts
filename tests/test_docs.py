"""Public and continuity documentation must match the workflow navigator."""

from __future__ import annotations

import unittest
from pathlib import Path


class DocumentationTests(unittest.TestCase):
    def test_current_docs_describe_verified_workflow_and_limits(self) -> None:
        # HANDOFF.md and dated packets like HANDOFF_2026-07-18.md are frozen
        # historical snapshots -- they are allowed to name whatever seed count
        # was true when they were written. Only files that describe *current*
        # state (README, CLAUDE.md, and the HANDOFF_LATEST.md pointer target)
        # must carry the current, accurate seed count.
        root = Path(__file__).resolve().parents[1]
        historical_paths = [root / "HANDOFF.md", root / "HANDOFF_2026-07-18.md"]
        current_paths = [root / "README.md", root / "CLAUDE.md", root / "HANDOFF_LATEST.md"]
        shared_required = ["mini suggest", "selection_count", "offline", "does not"]

        for path in historical_paths + current_paths:
            text = path.read_text(encoding="utf-8").lower()
            for term in shared_required:
                self.assertIn(term, text, f"{path.name} is missing {term!r}")

        for path in current_paths:
            text = path.read_text(encoding="utf-8").lower()
            self.assertIn("41", text, f"{path.name} is missing the current seed count '41'")

    def test_ux_guide_documents_the_phase_1_through_4_commands(self) -> None:
        root = Path(__file__).resolve().parents[1]
        guide = (root / "docs" / "ux-guide.md").read_text(encoding="utf-8")

        for term in (
            "mini rm",
            "mini rename",
            "mini edit",
            "mini folders",
            "mini harvest",
            "mini feedback",
            "mini stats",
            "clarifying question",
        ):
            self.assertIn(term, guide, f"docs/ux-guide.md is missing {term!r}")

    def test_public_readme_has_install_and_host_links(self) -> None:
        root = Path(__file__).resolve().parents[1]
        readme = (root / "README.md").read_text(encoding="utf-8")

        for term in (
            "python3 -m venv .venv",
            "python -m pip install .",
            "mini seed",
            "mini suggest --interactive",
            "LICENSE",
            "docs/install.md",
            "docs/ux-guide.md",
            "docs/hosts/",
        ):
            self.assertIn(term, readme)
