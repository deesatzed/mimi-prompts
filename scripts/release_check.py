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


def run(
    command: list[str], *, env: dict[str, str] | None = None, cwd: Path = ROOT
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=env, check=False)
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
        outside = temp / "outside-source-tree"
        outside.mkdir()
        installed_storage = temp / "installed-prompts.json"
        run([str(mini), "--storage", str(installed_storage), "seed"], env=environment, cwd=outside)
        seeded = run(
            [str(mini), "--storage", str(installed_storage), "suggest", "--context", "not sure", "--json"],
            env=environment,
            cwd=outside,
        )
        assert len(json.loads(seeded.stdout)["suggestions"]) >= 1
        checks.append("packaged seed outside source tree")

    tabletop = ROOT / "docs/reports/tabletop-results.json"
    payload = json.loads(tabletop.read_text(encoding="utf-8"))
    assert payload["llm_calls"] == 0
    assert len(payload["scenarios"]) == 10
    assert all(item["status"] == "PASS" for item in payload["scenarios"])
    checks.append("saved tabletop evidence")

    public_paths = [
        ROOT / "LICENSE",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        ROOT / "site/index.html",
        ROOT / "site/styles.css",
        ROOT / "site/app.js",
        ROOT / ".github/workflows/verify.yml",
        ROOT / ".github/workflows/pages.yml",
        ROOT / "docs/install.md",
        ROOT / "docs/ux-guide.md",
    ]
    assert all(path.is_file() for path in public_paths)
    site = (ROOT / "site/index.html").read_text(encoding="utf-8")
    assert 'href="styles.css"' in site and 'src="app.js"' in site
    assert "No tracking" in site and "mini suggest --json" in site
    for guide in ("codex.md", "claude-code.md", "cursor.md", "local-agents.md", "grok.md"):
        assert (ROOT / "docs/hosts" / guide).is_file()
    assert "python3 -m unittest discover" in (ROOT / ".github/workflows/verify.yml").read_text()
    assert "path: site" in (ROOT / ".github/workflows/pages.yml").read_text()
    checks.append("public repository artifacts")
    print("RELEASE CHECK PASS: " + "; ".join(checks))


if __name__ == "__main__":
    main()
