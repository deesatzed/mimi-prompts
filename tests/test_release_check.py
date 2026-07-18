"""Release verifier validates the full local delivery surface."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class ReleaseCheckTests(unittest.TestCase):
    def test_release_check_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "scripts/release_check.py"],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RELEASE CHECK PASS", result.stdout)
        self.assertIn("installed mini console", result.stdout)
