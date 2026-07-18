#!/usr/bin/env python3
"""Network-free release verification for MiniPromptLib."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=env, check=False)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}{result.stderr}"
        )
    return result


def main() -> None:
    checks: list[str] = []
    run([sys.executable, "-c", "from minipromptlib import MiniPromptLibrary; from core import MiniPromptLibrary as Legacy; assert MiniPromptLibrary is Legacy"])
    checks.append("package and legacy imports")
    run([sys.executable, "cli.py", "--help"])
    run([sys.executable, "-m", "minipromptlib.cli", "--help"])
    checks.append("direct and module CLI")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        storage = temp / "prompts.json"
        run([sys.executable, "-m", "minipromptlib.cli", "--storage", str(storage), "seed", "--panel", "seeds.md"])
        suggested = run(
            [
                sys.executable,
                "-m",
                "minipromptlib.cli",
                "--storage",
                str(storage),
                "suggest",
                "--context",
                "pytest failed with a traceback",
                "--json",
            ]
        )
        payload = json.loads(suggested.stdout)
        assert payload["state"] == "failure"
        assert 1 <= len(payload["suggestions"]) <= 3
        checks.append("isolated seed and suggestion workflow")

        installed = temp / "installed"
        run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--no-build-isolation",
                "--target",
                str(installed),
                ".",
            ]
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(installed)
        run([sys.executable, "-m", "minipromptlib.cli", "--help"], env=environment)
        checks.append("fresh target install")
        mini = installed / "bin" / "mini"
        if not mini.exists():
            raise RuntimeError(f"installed mini console script missing: {mini}")
        run([str(mini), "--help"], env=environment)
        checks.append("installed mini console")

    tabletop = ROOT / "docs/reports/tabletop-results.json"
    payload = json.loads(tabletop.read_text(encoding="utf-8"))
    assert payload["llm_calls"] == 0
    assert len(payload["scenarios"]) == 10
    assert all(item["status"] == "PASS" for item in payload["scenarios"])
    checks.append("saved tabletop evidence")
    print("RELEASE CHECK PASS: " + "; ".join(checks))


if __name__ == "__main__":
    main()
