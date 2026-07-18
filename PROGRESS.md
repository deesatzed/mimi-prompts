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
