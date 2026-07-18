# Workflow Prompt Navigator Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Turn MiniPromptLib into an installable, offline-first workflow prompt navigator that shows at most three contextually relevant, frequency-weighted choices and supports selection, paging, retry, nesting, and reviewed prompt capture.

**Architecture:** Migrate the implementation into a real `minipromptlib` package while keeping root-level compatibility shims. Keep persistence and ranking deterministic and standard-library-only; layer optional LLM behavior behind existing callables. Put workflow classification, ranking, and session behavior in separate modules so the CLI and future agent adapters use the same tested engine.

**Tech Stack:** Python 3.13, standard library, `unittest`, JSON storage, `argparse`, `pyproject.toml`/setuptools console entry point.

---

### Task 1: Freeze Current Behavior with Regression Tests

**Files:**

- Create: `tests/__init__.py`
- Create: `tests/test_core_regression.py`
- Reference: `core.py`
- Reference: `cli.py`

**Step 1: Write failing/characterization tests**

Cover save/get/list/search, duplicate naming, overwrite stat preservation, usage logging, export/import, deterministic fallback selection, and the direct CLI entry point. Every test creates a `TemporaryDirectory` and an isolated `prompts.json`.

```python
class CoreRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        self.lib = MiniPromptLibrary(self.storage)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_round_trip(self):
        prompt_id = self.lib.save_mini_prompt(
            "Walk through scenarios before deciding.",
            name="tabletop-first",
            tags=["decision", "workflow"],
        )
        reloaded = MiniPromptLibrary(self.storage)
        self.assertEqual(reloaded.get_prompt(prompt_id)["prompt_text"],
                         "Walk through scenarios before deciding.")
```

**Step 2: Run the characterization suite**

Run: `python3 -m unittest tests.test_core_regression -v`

Expected: existing supported behavior passes; any genuine current discrepancy is documented in `PROGRESS.md` before changing semantics.

**Step 3: Record baseline truth**

Create `PROGRESS.md` with the current branch, dirty/untracked-state note, command result, and discovered risks. Do not absorb unrelated files.

**Step 4: Commit**

```bash
git add tests/__init__.py tests/test_core_regression.py PROGRESS.md
git commit -m "test: characterize miniprompt core behavior"
```

### Task 2: Create an Installable Package Without Breaking Direct Use

**Files:**

- Create: `pyproject.toml`
- Create: `minipromptlib/__init__.py`
- Create: `minipromptlib/core.py`
- Create: `minipromptlib/cli.py`
- Modify: `core.py`
- Modify: `cli.py`
- Modify: `__init__.py`
- Modify: `tests/test_core_regression.py`
- Create: `tests/test_packaging.py`

**Step 1: Write packaging/import tests**

Test that these all resolve to the same public class:

```python
from minipromptlib import MiniPromptLibrary as PackageLibrary
from core import MiniPromptLibrary as LegacyLibrary

self.assertIs(PackageLibrary, LegacyLibrary)
```

Add a subprocess assertion that `python3 cli.py --help` and `python3 -m minipromptlib.cli --help` both exit 0.

**Step 2: Run tests and confirm the package import fails**

Run: `python3 -m unittest tests.test_packaging -v`

Expected: FAIL because `minipromptlib/` does not exist yet.

**Step 3: Add the package and compatibility shims**

Move canonical implementation into `minipromptlib/core.py` and `minipromptlib/cli.py`. Root modules become narrow compatibility entry points:

```python
# core.py
from minipromptlib.core import *  # noqa: F401,F403
```

```python
# cli.py
from minipromptlib.cli import main

if __name__ == "__main__":
    main()
```

Define an installable `mini` console script in `pyproject.toml`. Do not add runtime dependencies.

**Step 4: Run regression and packaging tests**

Run: `python3 -m unittest tests.test_core_regression tests.test_packaging -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml minipromptlib core.py cli.py __init__.py tests/test_core_regression.py tests/test_packaging.py
git commit -m "build: package minipromptlib with compatible entry points"
```

### Task 3: Make Persistence Versioned, Atomic, and Corruption Safe

**Files:**

- Create: `minipromptlib/storage.py`
- Modify: `minipromptlib/core.py`
- Create: `tests/test_storage.py`
- Modify: `DECISIONS.md`

**Step 1: Write failing persistence tests**

Test legacy dictionary loading, schema-versioned loading, atomic replace, defaulting new fields, invalid JSON, invalid entry shapes, and import dry-run behavior. Assert corrupt source bytes remain unchanged.

```python
def test_corrupt_store_is_not_replaced(self):
    self.storage.write_text("{broken", encoding="utf-8")
    with self.assertRaises(StorageCorruptionError):
        MiniPromptLibrary(self.storage)
    self.assertEqual(self.storage.read_text(encoding="utf-8"), "{broken")
```

**Step 2: Confirm the safety test fails against current behavior**

Run: `python3 -m unittest tests.test_storage -v`

Expected: FAIL because `_load()` currently swallows parse errors.

**Step 3: Implement storage boundaries**

Use a schema envelope such as:

```json
{"schema_version": 2, "prompts": {}}
```

Read legacy top-level dictionaries for backward compatibility. Write to a sibling temporary file, flush and `fsync`, then use `os.replace`. Raise actionable typed exceptions rather than silently returning an empty library.

**Step 4: Document the decision**

Record JSON retention, schema versioning, atomic writes, and the no-silent-reset rule in `DECISIONS.md`.

**Step 5: Verify and commit**

Run: `python3 -m unittest tests.test_storage tests.test_core_regression -v`

Expected: PASS.

```bash
git add minipromptlib/storage.py minipromptlib/core.py tests/test_storage.py DECISIONS.md
git commit -m "feat: add corruption-safe versioned prompt storage"
```

### Task 4: Import the Authored Seed Panel Deterministically

**Files:**

- Create: `minipromptlib/seeds.py`
- Modify: `seeds.py`
- Reference: `seeds.md`
- Create: `tests/test_seeds.py`

**Step 1: Write failing seed tests**

Assert every numbered prompt in `seeds.md` is represented, identifiers are unique, required metadata is present, repeat seeding is idempotent, and user-edited prompts are not overwritten without `--overwrite`.

```python
def test_seed_panel_is_complete(self):
    headings = re.findall(r"^###\s+(\d+)\.", Path("seeds.md").read_text(), re.MULTILINE)
    self.assertEqual(len(SEEDS), len(headings))
```

The expected authored count must be derived from the file rather than copied from the stale handoff claim of 30; at planning time the live panel contains 34 numbered entries. The test must derive the current count at runtime, so later user additions are detected rather than silently omitted.

**Step 2: Confirm completeness fails**

Run: `python3 -m unittest tests.test_seeds -v`

Expected: FAIL because only two seeds currently exist in `seeds.py`.

**Step 3: Implement the canonical seed module**

Represent all authored entries as data with `name`, `prompt_text`, `tags`, `category`, and `workflow_states`. Preserve authored prompt text, including the current #32–34 workflow prompts, and map the process-first cohort to `question`, `proposal`, `checkpoint`, `completion`, `failure`, or `undecided` as appropriate. Do not treat wording inside a seed (for example, #10's push instruction) as authority to perform that action. Keep root `seeds.py` as the executable compatibility wrapper.

**Step 4: Verify idempotence and commit**

Run: `python3 -m unittest tests.test_seeds -v`

Expected: PASS.

```bash
git add minipromptlib/seeds.py seeds.py seeds.md tests/test_seeds.py
git commit -m "feat: add complete workflow-aware seed panel"
```

### Task 5: Add Context Packets and Workflow-State Classification

**Files:**

- Create: `minipromptlib/models.py`
- Create: `minipromptlib/classifier.py`
- Create: `tests/fixtures/workflow_states.json`
- Create: `tests/test_classifier.py`

**Step 1: Write fixture-driven classification tests**

Include positive and ambiguous cases for `question`, `checkpoint`, `completion`, `failure`, `proposal`, `undecided`, `capture`, and `general`. Explicit state supplied by an adapter takes precedence.

```python
packet = ContextPacket(
    last_agent_message="Which direction should we choose?",
    last_user_message="Not sure. Let's run through scenarios first.",
)
self.assertEqual(classify_workflow_state(packet), WorkflowState.UNDECIDED)
```

**Step 2: Confirm the classifier does not exist**

Run: `python3 -m unittest tests.test_classifier -v`

Expected: FAIL on import.

**Step 3: Implement typed context and deterministic rules**

Use dataclasses and enums. Keep rules ordered, inspectable, and bounded to the latest messages plus optional build status. Return classification evidence for display and debugging.

**Step 4: Verify and commit**

Run: `python3 -m unittest tests.test_classifier -v`

Expected: PASS.

```bash
git add minipromptlib/models.py minipromptlib/classifier.py tests/fixtures/workflow_states.json tests/test_classifier.py
git commit -m "feat: classify prompt workflow state from bounded context"
```

### Task 6: Implement Logic-Plus-Frequency Ranking and Progressive Pages

**Files:**

- Create: `minipromptlib/ranking.py`
- Modify: `minipromptlib/models.py`
- Modify: `minipromptlib/core.py`
- Create: `tests/test_ranking.py`
- Create: `tests/test_pagination.py`

**Step 1: Write ranking-invariant tests**

Tests must prove:

- state and contextual logic determine candidate eligibility;
- frequency breaks close relevance ties;
- a very frequent irrelevant prompt cannot outrank a highly relevant new prompt;
- three or fewer suggestions are returned by default;
- reasons and selection counts are present;
- `more` is stable, non-repeating, and exhaustible.

```python
def test_frequency_breaks_relevance_tie(self):
    low = prompt("low", states=["question"], selection_count=1)
    high = prompt("high", states=["question"], selection_count=12)
    ranked = rank_prompts(self.packet, [low, high])
    self.assertEqual(ranked[0].prompt_id, "high")

def test_frequency_cannot_defeat_clear_relevance(self):
    irrelevant = prompt("popular", states=["completion"], selection_count=1000)
    relevant = prompt("new", states=["failure"], selection_count=0)
    ranked = rank_prompts(self.failure_packet, [irrelevant, relevant])
    self.assertEqual(ranked[0].prompt_id, "new")
```

**Step 2: Confirm tests fail**

Run: `python3 -m unittest tests.test_ranking tests.test_pagination -v`

Expected: FAIL on missing ranking module.

**Step 3: Implement bounded scoring**

Keep scoring weights named and configurable. Use deterministic state/text/tag scores plus a logarithmically bounded selection-frequency boost. Do not require embeddings or an LLM. Return score components so a suggestion can explain why it appeared.

**Step 4: Add selection semantics**

Add `record_selection(prompt_id)` that increments `selection_count` and `last_selected` exactly once. Displaying candidates and paging must never increment the count. Preserve `log_usage()` as separate outcome tracking.

**Step 5: Verify and commit**

Run: `python3 -m unittest tests.test_ranking tests.test_pagination tests.test_storage -v`

Expected: PASS.

```bash
git add minipromptlib/ranking.py minipromptlib/models.py minipromptlib/core.py tests/test_ranking.py tests/test_pagination.py
git commit -m "feat: rank workflow prompts with bounded frequency weighting"
```

### Task 7: Add Navigator Sessions, Nesting, and Explicit Composition

**Files:**

- Create: `minipromptlib/navigator.py`
- Modify: `minipromptlib/models.py`
- Create: `tests/test_navigator.py`

**Step 1: Write session tests**

Cover start, select by number, invalid selection, `more`, exhausted pages, `try_again`, nested recommendations, `back`, composition preview, confirm, and cancel. Assert selection is recorded once even when previewed repeatedly.

```python
session = navigator.start(packet)
chosen = navigator.select(session, 1)
self.assertEqual(chosen.prompt_id, session.page.items[0].prompt_id)
self.assertEqual(library.get_prompt(chosen.prompt_id)["selection_count"], 1)
```

**Step 2: Confirm session tests fail**

Run: `python3 -m unittest tests.test_navigator -v`

Expected: FAIL on missing navigator module.

**Step 3: Implement ephemeral session paths**

Keep session state in memory for interactive use and support JSON serialization for adapters. Nest dynamically using the original packet plus selected prompt IDs. Do not introduce a rigid prompt tree or auto-compose without preview.

**Step 4: Verify and commit**

Run: `python3 -m unittest tests.test_navigator tests.test_ranking tests.test_pagination -v`

Expected: PASS.

```bash
git add minipromptlib/navigator.py minipromptlib/models.py tests/test_navigator.py
git commit -m "feat: add nested prompt navigation sessions"
```

### Task 8: Add Reviewed Quick Capture

**Files:**

- Create: `minipromptlib/capture.py`
- Modify: `minipromptlib/navigator.py`
- Create: `tests/test_capture.py`

**Step 1: Write capture tests**

Cover draft creation from natural language, deterministic name proposal, inferred workflow states, edit, confirm, cancel, duplicate handling, and the guarantee that an unconfirmed draft never changes storage.

```python
draft = create_capture_draft(
    "Not sure, let's run through scenarios or tabletops and then decide."
)
self.assertEqual(draft.name, "tabletop-scenarios-before-deciding")
self.assertFalse(library.get_prompt(draft.name))
```

**Step 2: Confirm tests fail**

Run: `python3 -m unittest tests.test_capture -v`

Expected: FAIL on missing capture module.

**Step 3: Implement deterministic draft/review/save**

Preserve user wording by default. Optional LLM cleanup may create a second preview but must never be required or automatically accepted.

**Step 4: Verify and commit**

Run: `python3 -m unittest tests.test_capture tests.test_navigator -v`

Expected: PASS.

```bash
git add minipromptlib/capture.py minipromptlib/navigator.py tests/test_capture.py
git commit -m "feat: add reviewed in-flow prompt capture"
```

### Task 9: Build the Fast Interactive and Scriptable CLI

**Files:**

- Modify: `minipromptlib/cli.py`
- Create: `tests/test_cli_ux.py`
- Create: `tests/test_cli_json.py`

**Step 1: Write CLI contract tests**

Add tests for:

- `mini suggest --context ...` rendering at most three numbered items;
- commands `1`, `m`, `r`, `a`, `back`, and `q`;
- stdin context and build-status input;
- `--json` request/response schema;
- nonzero exits and clear messages for corrupt storage or invalid input;
- legacy `save`, `list`, `get`, `search`, `improve`, and `mine` commands.

**Step 2: Confirm tests fail**

Run: `python3 -m unittest tests.test_cli_ux tests.test_cli_json -v`

Expected: FAIL because `suggest` and session actions do not exist.

**Step 3: Implement a thin CLI over Navigator**

Keep business logic out of `cli.py`. Default output shows state, up to three numbered choices, a short relevance reason, visible use count, and the compact action line. Machine-readable mode emits versioned JSON and never includes decorative output.

**Step 4: Verify and commit**

Run: `python3 -m unittest tests.test_cli_ux tests.test_cli_json tests.test_core_regression -v`

Expected: PASS.

```bash
git add minipromptlib/cli.py tests/test_cli_ux.py tests/test_cli_json.py
git commit -m "feat: add interactive workflow prompt navigator CLI"
```

### Task 10: Add One Reference Agent Adapter and Portable Contracts

**Files:**

- Create: `integrations/codex/miniprompt-navigator/SKILL.md`
- Create: `integrations/claude/mini.md`
- Create: `docs/integrations.md`
- Create: `tests/test_integrations.py`

**Step 1: Write adapter-content tests**

Verify both adapters invoke the scriptable `mini suggest --json` contract, pass only bounded context, present no more than three choices, and never silently send data to an external LLM.

**Step 2: Confirm tests fail**

Run: `python3 -m unittest tests.test_integrations -v`

Expected: FAIL because integration files are absent.

**Step 3: Implement thin adapters**

Adapters should translate the latest question/status into the common context packet and render returned choices. They must not duplicate classifier or ranking rules. Document install/copy steps without mutating the user's global Codex or Claude configuration.

**Step 4: Verify and commit**

Run: `python3 -m unittest tests.test_integrations tests.test_cli_json -v`

Expected: PASS.

```bash
git add integrations docs/integrations.md tests/test_integrations.py
git commit -m "docs: add portable agent navigator adapters"
```

### Task 11: Prove the Ten Tabletop Scenarios

**Files:**

- Create: `scripts/tabletop_demo.py`
- Create: `tests/fixtures/tabletop_scenarios.json`
- Create: `tests/test_tabletop.py`
- Create: `docs/reports/tabletop-results.json`

**Step 1: Encode design scenarios as deterministic fixtures**

Include the ten scenarios from `docs/plans/2026-07-18-workflow-prompt-navigator-design.md`, expected workflow state, required prompt family, forbidden prompt family where relevant, and expected interaction outcome.

**Step 2: Write the end-to-end assertion test**

The demo uses a temporary library, seeds it, applies scenario actions, and emits JSON evidence. It must assert the three-choice ceiling, correct state, bounded frequency behavior, no duplicate pages, selection count, capture confirmation, corruption safety, and offline execution.

**Step 3: Run the tabletop and repair failures at their source**

Run: `python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json`

Expected: exit 0 with all ten scenarios marked `PASS` and `llm_calls: 0`.

**Step 4: Verify and commit**

Run: `python3 -m unittest tests.test_tabletop -v`

Expected: PASS.

```bash
git add scripts/tabletop_demo.py tests/fixtures/tabletop_scenarios.json tests/test_tabletop.py docs/reports/tabletop-results.json
git commit -m "test: prove workflow navigator tabletop scenarios"
```

### Task 12: Finish Documentation, Fresh-Install Proof, and Handoff Truth

**Files:**

- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `HANDOFF.md`
- Modify or create: `HANDOFF_LATEST.md`
- Modify: `PROGRESS.md`
- Modify: `DECISIONS.md`
- Create: `scripts/release_check.py`
- Create: `tests/test_docs.py`

**Step 1: Write release-check and docs tests**

Assert documented commands exist, examples use temporary storage, old feature claims match implementation, and `HANDOFF_LATEST.md` points to or reproduces the current dated handoff convention selected during implementation.

**Step 2: Update user documentation**

Lead with the workflow:

```bash
mini suggest --context "The AI asked whether we should add a web UI"
```

Explain numbered selection, `more`, `try again`, nesting, capture, frequency semantics, privacy defaults, installation, integrations, data recovery, and limitations. Do not claim automatic access to conversation context where only adapters supply it.

**Step 3: Run the entire verification surface**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests PASS.

Run: `python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json`

Expected: ten tabletop scenarios PASS, zero LLM calls.

Run: `python3 scripts/release_check.py`

Expected: package import, legacy entry point, installed-style CLI, isolated persistence, seed count, docs checks, and artifact validation all PASS.

Run: `python3 -m py_compile core.py cli.py seeds.py minipromptlib/*.py scripts/*.py tests/*.py`

Expected: exit 0.

Run: `git diff --check`

Expected: no whitespace errors.

**Step 4: Inspect scope and dirty-state truth**

Run: `git status --short --branch`

Confirm unrelated pre-existing files were neither overwritten nor silently included. Record any remaining untracked or environment-specific state in `PROGRESS.md`.

**Step 5: Commit the release-ready implementation**

```bash
git add README.md CLAUDE.md HANDOFF.md HANDOFF_LATEST.md PROGRESS.md DECISIONS.md scripts/release_check.py tests/test_docs.py docs/reports/tabletop-results.json
git commit -m "docs: finish workflow navigator release evidence"
```

Do not push, publish, deploy, or change global agent configuration without separate user authorization.
