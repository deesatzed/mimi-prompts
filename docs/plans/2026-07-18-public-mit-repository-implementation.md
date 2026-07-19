# Public MIT Repository Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Make MiniPromptLib a public MIT repository with portable installation/seeding, a static GitHub Pages landing page, and honest cross-host adapters.

**Architecture:** Keep the standard-library CLI as the product core. Package the reviewed seed panel with `importlib.resources`; use a dependency-free `site/` for GitHub Pages; make every host template call the same local JSON command. The site and adapters do not rank prompts, scrape conversations, or install global configuration.

**Tech Stack:** Python 3.11+, standard library, setuptools package data, HTML/CSS/vanilla JavaScript, GitHub Actions YAML, `unittest`.

---

### Task 1: Package the reviewed seed panel

**Files:**
- Create: `minipromptlib/data/seeds.md`
- Create: `minipromptlib/data/__init__.py`
- Modify: `pyproject.toml`, `minipromptlib/seeds.py`, `minipromptlib/cli.py`, `tests/test_seeds.py`, `scripts/release_check.py`

**Step 1: Write the failing test.** Add `default_seed_panel()` coverage proving that a target-installed package parses 34 seeds and that `mini --storage <tmp> seed` works from outside the checkout.

**Step 2: Verify RED.** Run `python3 -m unittest tests.test_seeds -v`; expect missing helper/default panel behavior.

**Step 3: Implement minimally.** Copy the protected panel unchanged as package data; implement `default_seed_panel()` using `importlib.resources.files("minipromptlib.data")`; make `seed --panel` default to it while preserving explicit panel paths; add `minipromptlib = ["data/*.md"]` package data in `pyproject.toml`.

**Step 4: Verify GREEN.** Run focused tests and the installed-style release check from an outside working directory.

**Step 5: Commit.** Stage only Task 1 files and commit `feat: package the authored seed panel`.

### Task 2: Rewrite public documentation around first use

**Files:**
- Modify: `README.md`, `tests/test_docs.py`
- Create: `docs/install.md`, `docs/ux-guide.md`

**Step 1: Write the failing test.** Assert the README contains venv install, `python -m pip install .`, `mini seed`, `mini suggest --interactive`, MIT/license link, and guide links.

**Step 2: Verify RED.** Run `python3 -m unittest tests.test_docs.DocumentationTests.test_public_readme_has_install_and_host_links -v`; expect failure because the current README is legacy-first.

**Step 3: Implement minimally.** Lead README with a three-command quickstart and terminal transcript; move LLM mining/improvement to an optional legacy section. `docs/install.md` covers clone, venv, install, upgrade, uninstall, data location, and recovery. `docs/ux-guide.md` covers number/more/nest/preview/compose/retry/capture/back and selection-count semantics.

**Step 4: Verify GREEN.** Run focused docs tests and all README shell commands using temporary storage.

**Step 5: Commit.** Stage Task 2 files and commit `docs: add public install and UX guides`.

### Task 3: Build the static GitHub Pages landing page

**Files:**
- Create: `site/index.html`, `site/styles.css`, `site/app.js`, `tests/test_site.py`

**Step 1: Write failing tests.** Assert product headline, interactive terminal transcript, installation command, JSON contract, MIT/source/guide links, host maturity labels, and no trackers/remote scripts.

**Step 2: Verify RED.** Run `python3 -m unittest tests.test_site -v`; expect missing `site/index.html`.

**Step 3: Implement minimally.** Create one semantic static page with hero, value explanation, terminal UX, install, integration cards, privacy boundary, and source links. CSS must support narrow viewports, visible focus, adequate contrast, and reduced motion. JavaScript may copy commands only; it must not contact a service or emulate the library.

**Step 4: Verify GREEN.** Run site tests, serve `site/` locally, and inspect desktop plus narrow viewport rendering.

**Step 5: Commit.** Stage Task 3 files and commit `feat: add static public landing page`.

### Task 4: Add truthful cross-host guides and templates

**Files:**
- Modify: `docs/integrations.md`, `integrations/codex/miniprompt-navigator/SKILL.md`, `tests/test_integrations.py`
- Create: `docs/hosts/codex.md`, `docs/hosts/claude-code.md`, `docs/hosts/cursor.md`, `docs/hosts/local-agents.md`, `docs/hosts/grok.md`, `integrations/claude/miniprompt-navigator/SKILL.md`, `integrations/cursor/miniprompt-navigator.mdc`

**Step 1: Write failing tests.** For every adapter/template, assert the shared `mini suggest --json` contract, bounded context, max-three rendering, and prohibitions on auto-save, external model use, deployment, and global mutation. Require explicit `manual fallback` wording for Grok.

**Step 2: Verify RED.** Run `python3 -m unittest tests.test_integrations -v`; expect missing guide/template failures.

**Step 3: Implement minimally.** Label each guide **verified**, **copyable project template**, or **manual fallback**. Codex and Claude are project-local templates. Cursor is a copyable rule—not a claimed native plugin. Local agents receive shell/Python examples. Grok remains manual until a native extension is independently verified.

**Step 4: Verify GREEN.** Run integration tests and manually inspect that every template calls the same JSON contract.

**Step 5: Commit.** Stage Task 4 files and commit `docs: add cross-host integration guides`.

### Task 5: Add public MIT and GitHub hygiene

**Files:**
- Create: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/workflows/verify.yml`, `.github/workflows/pages.yml`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/pull_request_template.md`, `tests/test_repository_hygiene.py`

**Step 1: Write failing tests.** Assert MIT header text, workflow existence, verification commands, Pages source `site`, and public safety guidance that forbids private prompt stores/sensitive conversations in issues.

**Step 2: Verify RED.** Run `python3 -m unittest tests.test_repository_hygiene -v`; expect missing files.

**Step 3: Implement minimally.** Add standard MIT text naming the owner. `verify.yml` runs Python 3.11 and unit/tabletop/release/compile checks. `pages.yml` deploys only `site/` on `main`, with least required permissions. Keep contribution/security scope narrow and maintainable.

**Step 4: Verify GREEN.** Run hygiene tests and structurally validate workflow YAML without assuming GitHub secrets or settings.

**Step 5: Commit.** Stage Task 5 files and commit `chore: prepare public MIT repository`.

### Task 6: Clean-install evidence and final truth artifacts

**Files:**
- Modify: `scripts/release_check.py`, `PROGRESS.md`, `DECISIONS.md`
- Create: `docs/reports/public-repository-readiness-YYYY-MM-DD.md`

**Step 1: Write failing release assertions.** Require target-installed `mini seed` without an external panel, docs/site/host/hygiene checks, and no broken local site links.

**Step 2: Verify RED.** Run `python3 scripts/release_check.py`; expect failure until Tasks 1–5 are complete.

**Step 3: Implement verification glue only.** Reuse existing tests/checks; do not reimplement product logic.

**Step 4: Verify the full proof surface.** Run `python3 -m unittest discover -s tests -v`; `python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json`; `python3 scripts/release_check.py`; `python3 -m py_compile core.py cli.py seeds.py minipromptlib/*.py scripts/*.py tests/*.py`; and `git diff --check`. Also prove a fresh clone/venv can run installed `mini seed` outside the source tree and inspect the site locally.

**Step 5: Commit.** Record only current successful evidence and GitHub-side deferred actions; commit `docs: record public repository readiness`.

### Task 7: Publish only after a separate explicit authorization

**Files:** none before authorization.

Inspect status, remote, branch, and commits. Only then add `origin`, push to `https://github.com/deesatzed/mimi-prompts.git`, enable Pages, and set remote metadata after the user explicitly authorizes those external changes. Verify the remote default branch, Actions, Pages URL, rendered landing page, and license metadata afterward.
