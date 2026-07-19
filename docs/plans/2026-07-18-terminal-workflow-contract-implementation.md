# Terminal Workflow Contract Implementation Plan

> **For Codex:** Execute task-by-task using test-first development.

**Goal:** Close the three P0 terminal UX gaps: empty-store guidance, visible nesting composition actions, and explicit `more` exhaustion feedback.

**Architecture:** Keep workflow state and selection-path behavior in `WorkflowNavigator`; add narrow query/mutation methods there. Keep CLI rendering and stdin routing in `minipromptlib/cli.py`. No data schema or dependency changes are needed.

**Tech Stack:** Python 3.11 standard library, `unittest`, local JSON storage.

---

### Task 1: Empty-store guidance

**Files:** `tests/test_cli_ux.py`, `minipromptlib/cli.py`

1. Add a failing test for `suggest` on a fresh storage path: success, a no-saved-prompts message, the exact `mini seed --panel seeds.md` action, and no file mutation.
2. Run `python3 -m unittest tests.test_cli_ux.CliUxTests.test_empty_store_suggests_seed_without_mutating_storage -v`; observe failure.
3. Add the smallest noninteractive CLI branch that prints guidance without calling `seed_library`.
4. Re-run the focused test; observe pass.

### Task 2: Finite `more`

**Files:** `tests/test_navigator.py`, `tests/test_cli_ux.py`, `minipromptlib/navigator.py`, `minipromptlib/cli.py`

1. Add failing tests for `can_more(session)` and an interactive final-page `m` message.
2. Run those focused tests; observe failure.
3. Add `can_more`; render `No more matching prompts` when false without mutating session or counts.
4. Re-run focused tests; observe pass.

### Task 3: Visible nest / preview / compose / back

**Files:** `tests/test_navigator.py`, `tests/test_cli_ux.py`, `minipromptlib/navigator.py`, `minipromptlib/cli.py`

1. Add a failing navigator test for back restoration after a nested page and no extra selection mutation.
2. Add a failing scripted CLI test for `1 → n → 1 → p → b → c → q`, asserting visible action labels and output headings.
3. Run focused tests; observe failure.
4. Implement `n`, `p`, `c`, and back re-ranking with concise no-selection feedback.
5. Re-run focused tests; observe pass.

### Task 4: Full verification and truth docs

**Files:** `PROGRESS.md`, `DECISIONS.md`, and `README.md` only if command wording becomes stale.

1. Run full unit, tabletop, release-check, compile, temporary-store transcript, and diff-check commands.
2. Record exact outcomes, scope boundary, and preserved unrelated file.
3. Do not commit or stage without an explicit request; do not include `idea2_app_directions.md`.
