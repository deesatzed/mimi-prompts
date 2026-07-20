# GOAL_GAP_FIX — Autonomous Gap-Remediation Contract

**Created:** 2026-07-19
**Source of gaps:** `UX_Gap_Analysis_2026-07-19.md` (findings F1–F14, gaps G1–G14)
**Authority:** This document is the user-approved build checklist authorizing autonomous
execution of the phases below. Work outside this checklist still requires new approval.
**Standing rules that always apply:** no mock/placeholder/simulation/demo/cached responses;
no time or cost estimates; every phase gate at 100% before the next phase starts; keep an
error log with mitigations; never call the state "complete" while any item remains.

---

## 1. Authorized scope

An autonomous session executing this contract MAY, without further approval:

- Modify code, tests, scripts, and docs inside `/Volumes/WS4TB/mimi_prompt`.
- Create local git commits on `master` at each phase gate (message pattern:
  `fix(gap): phase N — <summary>` plus the standard co-author trailer). **No push, no
  remote, no branch policy change** — those remain publication actions.
- Run the full verification suite and all CLI probes **against temporary storage only**
  (scratchpad paths). The user's real `~/.miniprompts/prompts.json` must never be read or
  written.
- Bump the storage schema to v3 with a tested, fail-closed migration.

An autonomous session MUST NOT:

- Push, add a remote, enable Pages/Actions, or resolve `master`/`main` (G14 — requires
  explicit authorization, unchanged from `HANDOFF_LATEST.md`).
- Invoke any LLM or choose any model. Phase 5 of the gap analysis (optional LLM
  enhancement) is **out of this contract** until the user selects a model.
- Add any dependency. The runtime stays standard-library only.
- Delete or rewrite `GOAL.md`, `DECISIONS.md`, or prior handoffs.

Decision rule for ambiguity: prefer the smallest change that satisfies the acceptance
criterion; if two readings conflict, choose the one consistent with the product contract in
`CLAUDE.md` (bounded context, preview-first, no auto-save) and record the decision in the
completion report.

---

## 2. Verification gate (run at the end of EVERY phase)

```bash
python3 -m unittest discover -s tests -v          # 100% pass required
python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json   # 10 PASS, llm_calls=0
python3 scripts/release_check.py                  # RELEASE CHECK PASS
python3 -m py_compile core.py cli.py seeds.py minipromptlib/*.py scripts/*.py tests/*.py
git diff --check
```

A phase is done only when: all five commands pass, new behavior has new tests, changed
behavior has honestly updated tests (never weakened to pass), and the phase commit is made.
If any command fails twice consecutively, stop and apply the error-analysis protocol
(5–7 candidate causes → narrow to 1–2 → add validation logging → then fix), recording it in
`ERROR_LOG.md` (create if absent) with the mitigation.

---

## 3. Phase 0 — Restore verification integrity (G1)

- [ ] Add one literal `mini suggest --context "..."` example line to
      `HANDOFF_2026-07-19.md` (Quick Resume Checklist or How to Run).
- [ ] Correct that packet's test-status line if it still asserts 49/49 for a tree state
      where that was false; state what was re-verified and when.
- [ ] Acceptance: `tests/test_docs.py` passes; full suite 49/49.
- [ ] Process note for future handoffs (add to the packet's continuity checklist): run the
      suite **after** updating the `HANDOFF_LATEST.md` symlink, not before.

## 4. Phase 1 — Truthfulness and safety fixes

### 1a. Honest ranking reasons (G2/F1) — `minipromptlib/ranking.py`
- [ ] `RankedPrompt.reason` says `matches <state>; used Nx` **only** when the prompt
      actually carries the state; fallback candidates say
      `closest available — no <state> prompts yet; used Nx`.
- [ ] Acceptance test: a packet whose state matches zero prompts yields pages containing no
      `matches <state>` reason. Update `tests/test_ranking.py`, tabletop fixtures, and any
      JSON-contract tests to the honest strings.

### 1b. Preview-before-select and count undo (G3/F3) — `navigator.py`, `cli.py`, `core.py`
- [ ] Interactive action `v` (view): `v 2` prints candidate 2's full `prompt_text` without
      calling `record_selection` and without altering session state.
- [ ] `core.py` gains `unrecord_selection(prompt_id)` clamping at 0; `navigator.back()`
      calls it for the id it pops (undoing only the count that `select` added).
- [ ] Acceptance tests: view leaves `selection_count` unchanged; select-then-back leaves
      `selection_count` at its pre-select value; back with nothing selected is a no-op.

### 1c. Runnable hints (G7/F5/F6) — `cli.py`
- [ ] Empty-store guidance becomes exactly: `No saved prompts yet. Run: mini seed`
- [ ] Non-interactive footer prints copy-pasteable commands, e.g.
      `More: mini suggest --context "<same context>" --offset 3` and
      `Capture a thought: mini capture "<your thought>"`.
- [ ] Acceptance: `tests/test_cli_ux.py` updated to assert the runnable forms.

### 1d. Storage safety (G8/F8) — `cli.py`
- [ ] Resolution order for the store path: `--storage` flag > `MINI_STORAGE` env var >
      default `~/.miniprompts/prompts.json`.
- [ ] Interactive mode's first line prints the resolved storage path.
- [ ] Acceptance tests: env var honored; flag overrides env; banner shows the path.

### 1e. Selection drift guard (G10/F4) — `cli.py`
- [ ] `suggest` gains optional `--expect <prompt-id>`; when provided with `--choice N`, the
      selection aborts (exit ≠ 0, nothing recorded) if candidate N's id differs.
- [ ] JSON payload for `--choice` already returns the selected id; document `--expect` in
      the subcommand help.
- [ ] Acceptance test: mismatched `--expect` records no selection.

### 1f. Remove test-fit capture code + real names (G12/F11, part of F10) — `capture.py`
- [ ] Delete the hardcoded `tabletop-scenarios-before-deciding` special case.
- [ ] Name generation: first ~8 meaningful tokens (stopwords dropped), joined as a slug,
      truncated at a word boundary, ≤ 64 chars, never mid-word.
- [ ] Honestly update `tests/test_capture.py` and the tabletop scenario that depended on
      the hardcoded name — they must assert the new rule, not be deleted.

### 1g. No baked-in model (G13/F14) — `cli.py`
- [ ] `mine --model` loses its default and becomes required; missing-model error tells the
      user to supply their chosen model id. Acceptance test: `mine` without `--model`
      exits with that actionable message and makes no network/client attempt.

- [ ] **Phase 1 gate + commit.**

## 5. Phase 2 — Library lifecycle

### 2a. Removal and editing (G5/F9) — `cli.py`, `core.py`
- [ ] `mini rm <id>` — interactive `y/N` confirmation, `--yes` for non-interactive; prints
      the removed prompt's name; unknown id exits non-zero with message.
- [ ] `mini rename <id> <new-name>` — refuses collisions unless `--overwrite`.
- [ ] `mini edit <id> [--text] [--description] [--tags ...] [--category]` — mutates only
      supplied fields; bumps the entry's `version`.
- [ ] Acceptance tests for all three, including refusal paths. All writes atomic via the
      existing storage layer.

### 2b. Human titles (F12) — `seeds.py`, `cli.py`
- [ ] Seeds keep their authored Markdown titles as `name` (e.g. `Explain It Simply`) while
      `id` stays the slug; re-seeding an existing store updates names idempotently.
- [ ] `mini list` prints `id | title`; suggestion lines show the title.
- [ ] Acceptance: `tests/test_seeds.py` asserts title preservation; list/suggest output
      tests updated.

- [ ] **Phase 2 gate + commit.**

## 6. Phase 3 — Folders and the Smart Capture Advisor

### 3a. Folder taxonomy, schema v3 (G4 / design 4-B) — `storage.py`, `seeds.py`
- [ ] `category` becomes a path string (`review/async`); schema version 3; migration maps
      every existing `workflow` category to a folder derived from the seed's
      `_STATE_BY_NUMBER` states and title (author the seed→folder map explicitly in
      `seeds.py`; non-seed entries map to `captured/<primary-state>`).
- [ ] Migration is fail-closed like current corrupt-store handling: on any anomaly, refuse
      to write and preserve the original file.
- [ ] `mini folders` prints the folder tree with per-folder counts.
- [ ] Acceptance: migration round-trip test on a v2 fixture; corrupt/ambiguous fixture
      refuses migration; `folders` output test.

### 3b. `mini harvest` deterministic pipeline (G4 / design 4-A) — new `minipromptlib/harvest.py`
- [ ] **Input:** `--file`, `--text`, or stdin only. No history access of any kind.
- [ ] **Detect:** extract instruction-like candidates via deterministic heuristics
      (imperative openings; rule markers `always` / `never` / `before … do …` /
      `make sure`; sentence length bounds; narration filtered out). Zero candidates is a
      valid, clearly-reported outcome.
- [ ] **Generalize:** deterministic parameterization of specifics — file paths, URLs,
      version strings, and Title/kebab/snake-case project identifiers → `{file}`,
      `{url}`, `{version}`, `{project}` — displayed as an original-vs-generalized diff.
      The user can always keep the original verbatim.
- [ ] **Ask:** per-candidate keypress consent:
      `[g]eneralized / [o]riginal / [e]dit / [f]older / [s]kip`. Nothing persists without
      an explicit save choice. `--json` emits the drafts (with recommendations) and never
      persists.
- [ ] **File:** folder recommendation scored by token overlap with folder members plus
      workflow-state affinity; always shown with reason and a confidence word
      (`high`/`medium`/`low`); below threshold, propose a new folder name instead.
- [ ] **Dedupe:** token-Jaccard against the store; at/above threshold (pick, state, and
      test one value) offer `update existing / save as variant / skip` — never silently
      mint a near-duplicate.
- [ ] `mini capture` becomes the single-candidate path through the same pipeline
      (same naming, generalization preview, folder recommendation, dedupe); its existing
      `--confirm` / `--json` contract keeps working.
- [ ] Acceptance: unit tests per stage (detect, generalize, recommend, dedupe) plus an
      end-to-end scripted-input test proving nothing is written on skip and exactly one
      entry is written per save, in the confirmed folder.

- [ ] **Phase 3 gate + commit.**

## 7. Phase 4 — Feedback loop and self-aware fallback

### 4a. Outcome feedback (G9/F13) — `cli.py`, `core.py`
- [ ] Interactive loop, on quit after ≥1 selection, asks once per selected prompt:
      `Did '<title>' help? [y/n/skip]` wiring the existing `log_usage`.
- [ ] New `mini feedback <id> --helped | --not-helped` for one-shot use.
- [ ] New `mini stats` — usage/success/failure table plus a section listing
      `get_underperforming_prompts` output with the hint `Consider: mini improve <id>`.
- [ ] Acceptance tests: counters move only on explicit feedback; `skip` moves nothing.

### 4b. Clarify-question fallback (G6/F2) — `cli.py`, `classifier.py`
- [ ] When state is `general` **and** context-token overlap with every candidate is zero,
      the interactive loop asks one deterministic question:
      `No strong signal. Is this about [d]eciding, [r]eviewing, [s]hipping, or [x] show anyway?`
      mapping d/r/s to `undecided`/`checkpoint`/`completion` re-ranks. Non-interactive
      mode prints the same options as runnable `--state ...` commands instead of asking.
- [ ] Acceptance test: the degenerate probe from the gap analysis
      (`"I want to refactor the payment module safely"`) triggers the clarify path.

### 4c. Capture nudge (design 4-C) — `cli.py`
- [ ] In `suggest --interactive`, when retry/context text itself matches capture-style
      language, append once per session:
      `That reads like a reusable rule — press [a] to review it as a capture draft.`
      Asks only; never saves.
- [ ] Acceptance test: nudge appears at most once per session and triggers no write.

### 4d. Seed-panel rebalance (G6) — `seeds.md`, `minipromptlib/data/seeds.md`
- [ ] Author 4 new `failure`-state and 3 new `capture`-state prompts in the established
      seed style; add them to the panel, the state map, and the folder map; seeding stays
      idempotent.
- [ ] **User-review flag:** list the new prompt texts verbatim in the completion report;
      the user may veto or edit any of them post-hoc. This is the only content-authoring
      item in the contract.

- [ ] **Phase 4 gate + commit.**

## 8. Documentation close-out (part of the final phase gate)

- [ ] Update `README.md`, `docs/ux-guide.md`, and `docs/integrations.md` for: `MINI_STORAGE`,
      `v`/`?`-style preview, `rm/rename/edit`, `folders`, `harvest`, `feedback`, `stats`,
      the honest fallback wording, and the v3 folder schema (JSON contract examples
      included).
- [ ] Update `CLAUDE.md`'s workflow-contract section to mention `harvest` with its
      no-scrape / no-auto-save guarantees.
- [ ] `tests/test_docs.py` extended so the new commands must appear in the docs.
- [ ] Regenerate `HANDOFF_LATEST.md` packet **after** all gates pass (suite run after the
      symlink flip, per Phase 0's process note).

## 9. Definition of done and completion report

The contract is complete only when all boxes above are checked, every phase gate passed at
100%, and a completion report (`GAP_FIX_REPORT_<date>.md`) records: per-gap status
(G1–G13; G14 explicitly untouched/awaiting authorization), verification outputs, decisions
taken under the ambiguity rule, the new seed prompts for user review (§4d), and any items
that were blocked rather than finished — stated plainly, never rounded up to "complete".

Out of contract, awaiting user input: publication (G14), LLM-assisted harvest/generalize
(needs the user's model choice), and any scope not written here.
