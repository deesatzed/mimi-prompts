# Progress

## 2026-07-18 — Workflow Prompt Navigator implementation started

- Authority: `GOAL.md`, approved design, and the 12-task implementation plan.
- Starting branch: `master` at `d5f2fbb`.
- Pre-existing untracked files preserved: `GOAL.md`, `HANDOFF_2026-07-18.md`, `HANDOFF_LATEST.md`, `idea2_app_directions.md`, `seeds.md`, `seeds.py`, and the uncommitted implementation plan.
- The live `seeds.md` panel currently has 34 numbered prompts; `seeds.py` contains two starter entries.
- Baseline automated regression coverage has been added and will run against temporary JSON storage only.
- Known starting risks: no package manifest, no test suite before this run, unsafe corrupt-JSON fallback, and LLM paths not live-verified. Core completion remains deterministic and offline.

## 2026-07-18 — Batch 1: baseline, packaging, and storage

- Added 6 regression tests covering current CRUD, CLI, usage, export/import, duplicate-ID, and deterministic fallback behavior.
- Added a standard-library package surface (`minipromptlib`) and `pyproject.toml` with the future `mini` entry point; direct and module CLI help both pass locally.
- Added schema-v2 atomic JSON storage with legacy-dictionary loading and `StorageCorruptionError`. Corrupt source files are preserved rather than silently reset.
- Verification: `python3 -m unittest tests.test_storage tests.test_packaging tests.test_core_regression -v` — 11 tests passed.
- Known compatibility note: package CLI currently delegates to the legacy root CLI while the new navigator CLI is built in later tasks.

## 2026-07-18 — Workflow Navigator implementation evidence

- Implemented deterministic workflow classification (`question`, `checkpoint`, `completion`, `failure`, `proposal`, `undecided`, `capture`, `general`), workflow-first ranking, a bounded logarithmic `selection_count` boost, stable three-item pages, and a session navigator with selection, more, retry, back, nesting preview, and reviewed capture.
- Added the installable `mini` console surface, direct/module compatibility, a JSON adapter contract, and a small interactive terminal loop (`m`, `r`, `a`, `b`, `q`).
- Converted the actual 34-item authored Markdown panel into deterministic, idempotent workflow-aware seeds. The root `seeds.py` now loads that panel rather than a two-prompt subset.
- Added reference Codex/Claude adapter templates that pass bounded context only and do not duplicate ranking logic or call external models.
- Added a schema-v2 JSON envelope, legacy loading, atomic writes, and corrupt-file preservation.
- Saved offline tabletop evidence at `docs/reports/tabletop-results.json`.
- Fresh verification on 2026-07-18:
  - `python3 -m unittest discover -s tests -v` — 40 tests passed.
  - `python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json` — 10 scenarios passed; `llm_calls=0`.
  - `python3 scripts/release_check.py` — package/legacy imports, direct/module CLI, isolated workflow, fresh target install, installed `mini` console, and tabletop artifact all passed.
  - `python3 -m py_compile core.py cli.py seeds.py minipromptlib/*.py scripts/*.py tests/*.py` — passed.
  - `git diff --check` — passed.
- Remaining limitation: adapters are repository-local templates. Installing a global Codex/Claude integration remains an explicit user action and was intentionally not performed.

## 2026-07-18 — P0 terminal workflow contract update

- Created `GOAL_UPDATE.md` from the SOTAppR and UX audit findings, plus a test-first implementation plan at `docs/plans/2026-07-18-terminal-workflow-contract-implementation.md`.
- A fresh empty store now gives non-mutating seed guidance. The interactive loop now makes nesting (`n`), preview (`p`), composition (`c`), and back (`b`) explicit; final-page `more` explains exhaustion and offers recovery.
- Selection integrity is retained: only a number calls `record_selection`; nesting, preview, composition, back, retry, and exhausted `more` do not add frequency. Back restores the normal ranked page after removing the latest session selection.
- Fresh verification: `python3 -m unittest discover -s tests -v` — 44 tests passed; tabletop — 10 passes and `llm_calls=0`; release check — passed; `py_compile` and `git diff --check` — passed.
- Saved temporary-storage UX transcript: `docs/reports/terminal-workflow-update-2026-07-18.md`.
- Preserved unrelated untracked file: `idea2_app_directions.md`. The prior audit reports remain untracked review artifacts; no global integration or real prompt store was accessed.
- Completion audit reran the complete proof surface and directly inspected a temporary store: nest/preview/compose/back produced exactly the two explicit numeric selections, and exhausted `more` left those counts unchanged. Added post-audit status notes to the dated UX and SOTAppR reports so their historical P0 findings are not read as current defects.

## 2026-07-18 — Public MIT repository implementation ready locally

- Packaged the reviewed 34-prompt seed panel as `minipromptlib.data`; `mini seed` now works from an installed package outside this checkout without an external panel path.
- Rewrote the README around local first use and added installation, terminal UX, and truthful host-integration guides. Added a dependency-free `site/` landing page plus copyable Codex, Claude Code, and Cursor templates; Grok remains explicitly manual.
- Added MIT licensing, contribution/security guidance, GitHub verification and Pages workflow definitions, and public-report templates that prohibit private stores, conversation transcripts, credentials, and sensitive data.
- Fresh full verification: `python3 -m unittest discover -s tests -v` — 49 tests passed; tabletop — 10 scenarios passed with `llm_calls=0`; release check, Python compilation, and `git diff --check` — passed. Detailed evidence: `docs/reports/public-repository-readiness-2026-07-18.md`.
- Publication is deferred by design: `git remote -v` is empty, no GitHub push has occurred, and Pages has not been enabled. The current evidence proves a target-installed package, not a clone from a populated remote.
- Preserved unrelated untracked file: `idea2_app_directions.md`.
