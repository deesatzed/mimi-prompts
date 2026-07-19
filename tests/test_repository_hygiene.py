"""Public repository artifacts are present and intentionally scoped."""

from __future__ import annotations

import unittest
from pathlib import Path


class RepositoryHygieneTests(unittest.TestCase):
    def test_public_mit_and_github_artifacts_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        required = {
            "LICENSE": "MIT License",
            "CONTRIBUTING.md": "private prompt stores",
            "SECURITY.md": "security",
            ".github/workflows/verify.yml": "python3 -m unittest discover",
            ".github/workflows/pages.yml": "site",
            ".github/ISSUE_TEMPLATE/bug_report.md": "sensitive",
            ".github/pull_request_template.md": "Verification",
        }

        for relative, expected in required.items():
            content = (root / relative).read_text(encoding="utf-8")
            self.assertIn(expected.lower(), content.lower(), relative)
