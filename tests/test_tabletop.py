"""The approved UX tabletops execute without a model or live prompt store."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TabletopTests(unittest.TestCase):
    def test_tabletop_demo_records_ten_offline_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "tabletop-results.json"
            result = subprocess.run(
                [sys.executable, "scripts/tabletop_demo.py", "--assert", "--output", str(output)],
                cwd=root,
                check=False,
                text=True,
                capture_output=True,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["llm_calls"], 0)
        self.assertEqual(len(payload["scenarios"]), 10)
        self.assertTrue(all(item["status"] == "PASS" for item in payload["scenarios"]))
