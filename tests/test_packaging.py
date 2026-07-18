"""Packaging and compatibility contracts for MiniPromptLib."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class PackagingTests(unittest.TestCase):
    def test_package_and_legacy_core_export_the_same_class(self) -> None:
        from core import MiniPromptLibrary as LegacyLibrary
        from minipromptlib import MiniPromptLibrary as PackageLibrary

        self.assertIs(PackageLibrary, LegacyLibrary)

    def test_direct_and_module_cli_help_succeed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        commands = [
            [sys.executable, "cli.py", "--help"],
            [sys.executable, "-m", "minipromptlib.cli", "--help"],
        ]

        for command in commands:
            result = subprocess.run(
                command,
                cwd=root,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("MiniPromptLib", result.stdout)
            self.assertIn("mine", result.stdout)
