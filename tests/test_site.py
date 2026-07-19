"""Static public landing page contract."""

from __future__ import annotations

import unittest
from pathlib import Path


class SiteTests(unittest.TestCase):
    def test_landing_page_explains_local_workflow_and_links_to_guides(self) -> None:
        root = Path(__file__).resolve().parents[1]
        page = (root / "site" / "index.html").read_text(encoding="utf-8")

        for term in (
            "Local workflow prompt navigator",
            "mini suggest --json",
            "python -m pip install .",
            "MIT License",
            "docs/install.md",
            "docs/ux-guide.md",
            "Copyable project template",
            "Manual fallback",
            "No tracking",
        ):
            self.assertIn(term, page)
        self.assertNotIn("google-analytics", page.lower())
        self.assertNotIn("https://cdn", page.lower())
