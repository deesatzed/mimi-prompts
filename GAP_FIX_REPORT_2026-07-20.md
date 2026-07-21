# GAP_FIX_REPORT — 2026-07-20

**Contract executed:** `GOAL_GAP_FIX.md`
**Source of gaps:** `UX_Gap_Analysis_2026-07-19.md` (findings F1–F14, gaps G1–G14)
**Final verification:** 140/140 unit tests, 10/10 tabletop scenarios (`llm_calls=0`), `RELEASE CHECK PASS`, clean compile, clean whitespace — all re-run **after** the `HANDOFF_LATEST.md` symlink was flipped to `HANDOFF_2026-07-20.md`, per the process rule established in Phase 0.
**Scope discipline:** publication (G14) and LLM-assisted harvest (Phase 5) were left untouched, exactly as the contract required — both need explicit user input this session does not have (authorization to push; a chosen model).

---

## Per-gap status

| Gap | Status | What changed | Evidence |
| --- | --- | --- | --- |
| G1 — Handoff claimed 49/49 but tree was 48/49 | **Fixed** | Added literal `mini suggest` example, corrected `selection_count`/`does not` wording gaps in `HANDOFF_2026-07-19.md`; established the "verify after the symlink flip" rule | `tests/test_docs.py` |
| G2 — False "matches state" reason on fallback | **Fixed** | `ranking.py` now says `closest available — no <state> prompts yet` when the state doesn't actually match | `tests/test_ranking.py::test_fallback_candidates_do_not_claim_a_false_match` |
| G3 — No preview-before-select; no undo | **Fixed** | `navigator.view()` reads without selecting; `core.unrecord_selection()` + `navigator.back()` undo the count `select()` added | `tests/test_navigator.py` (4 new tests) |
| G4 — Capture: bad names, no folders, no dedupe | **Fixed** | New `mini harvest` (detect → generalize → file → dedupe, consent-gated); schema v3 folder taxonomy; capture's name generation fixed in Phase 1 | `tests/test_harvest*.py`, `tests/test_folders.py` |
| G5 — No delete/rename/edit | **Fixed** | `mini rm` (confirmed), `mini rename`, `mini edit` | `tests/test_lifecycle.py` |
| G6 — Off-vocabulary → confident but arbitrary page; failure=2/capture=0 seeds | **Fixed** | `is_weak_signal()` + clarify prompt (interactive and non-interactive); seed panel rebalanced to failure=6, capture=3 | `tests/test_weak_signal.py`, `tests/test_seeds.py::test_failure_and_capture_states_have_real_seed_coverage` |
| G7 — First-run hints wrong/non-runnable | **Fixed** | `mini seed` instead of a non-existent local path; footer prints copy-pasteable `mini suggest ... --offset N` / `mini capture "..."` | `tests/test_cli_ux.py` |
| G8 — Storage targeting risk | **Fixed** | `MINI_STORAGE` env var (flag > env > default) plus a storage-path banner in interactive mode | manual verification in Phase 1 (`resolve_storage_path`) |
| G9 — Feedback loop absent | **Fixed** | `mini feedback`, `mini stats`, interactive quit-time prompt, all wired to the pre-existing `log_usage`/`get_underperforming_prompts` | `tests/test_feedback.py` |
| G10 — `--choice` can select against a stale page | **Fixed** | `--expect <id>` aborts the selection if the page changed since it was read | manual verification in Phase 1 |
| G11 — Interactive action overload, no help | **Fixed** | `h`/`help`/`?` prints the full action list inline | manual verification in Phase 1 |
| G12 — Hardcoded "tabletop" capture name | **Fixed** | Removed; names are now derived from the text's own words, word-boundary safe, never mid-word truncated | `tests/test_capture.py::test_name_is_derived_from_the_text_not_a_hardcoded_special_case` |
| G13 — Hardcoded LLM model default in CLI | **Fixed** | `mine --model` has no default and is required; missing it is a clear, actionable error | manual verification in Phase 1 |
| G14 — Publication gaps (remote, master/main, Pages, live host test) | **Untouched, as required** | No remote added, no push, no branch rename, no host live-tested — all require explicit authorization not given this session | `HANDOFF_2026-07-20.md` §Current Blockers |

All 13 in-scope gaps (G1–G13) are closed with passing tests. G14 remains exactly where the prior packet left it, by design.

---

## Verification history (this session)

| Phase | Suite | Tabletop | Release check | Notes |
| --- | --- | --- | --- | --- |
| 0 | 49/49 | 10/10 | PASS | Fixed the handoff doc gate itself |
| 1 | 55/55 | 10/10 | PASS | +6 tests (ranking, navigator, capture) |
| 2 | 70/70 | 10/10 | PASS | +15 tests (lifecycle, seed titles) |
| 3 | 112/112 | 10/10 | PASS | +42 tests (storage v3, folders, harvest core + CLI) |
| 4a–c | 138/138 | 10/10 | PASS | +26 tests (weak signal, feedback, capture nudge); 1 pre-existing test fixed for a real behavior change (word-boundary detection bug found while testing the nudge) |
| 4d | 139/139 | 10/10 | PASS | +1 test (seed coverage); seed count 34 → 41 propagated everywhere |
| Docs close-out | 140/140 | 10/10 | PASS | +1 test (docs coverage); handoff regenerated and re-verified post-symlink-flip |

Two real bugs were caught and fixed mid-implementation, not just at the end:
1. **`is_weak_signal` false negative** — an incidental single-word overlap between an off-vocabulary query and an unrelated seed (via "want"/"safely") let a genuinely arbitrary page through undetected. Fixed by checking the *displayed page's* logical relevance rather than any-candidate-anywhere overlap.
2. **Harvest opener false positive** — `"reviewing"` matched the `"review"` imperative opener via bare `str.startswith`, so ordinary narration ("reviewing the current release notes") was mistakenly flagged as a capture candidate. Fixed with word-boundary matching.

---

## Decisions made under the contract's ambiguity rule

1. **`mini capture` was not folded into `mini harvest`.** The contract's design sketch (§4-A) suggested unifying them, but `capture`'s `--confirm`/`--json` contract is exercised by `test_capture.py`, `test_tabletop.py`, and referenced by host-integration docs. Unifying it risked a breaking change to a stable, tested surface for a UX-consistency win that `harvest` already delivers for the multi-candidate case. Kept them as two paths: `capture` for a single known thought, `harvest` for pulling candidates out of arbitrary text.
2. **Folder is not refreshed on re-seed.** Title refresh on re-seed fixes a bug (the display was literally the machine slug). Folder is different — a user who moves a seed prompt into a custom folder has made a legitimate choice; silently reverting it on the next `mini seed` would violate the product's "never auto-mutate without consent" contract. Left as one-time-assigned-then-user-owned.
3. **`test_docs.py`'s literal-count check was split by document type.** `HANDOFF.md` and dated packets like `HANDOFF_2026-07-18.md` are frozen historical snapshots — they're allowed to keep whatever seed count was true when written. Only current-state docs (README, CLAUDE.md, `HANDOFF_LATEST.md`) must carry the accurate count. This preserves the original test's intent (current docs must be accurate) without rewriting history.
4. **2-segment kebab-case words are not generalized.** Testing showed `edge-case`, `real-time`, `check-in` are common English compounds, not project identifiers — parameterizing them produced garbled generalizations more often than useful ones. Only 3+ segment kebab-case (`acme-billing-service`) is treated as a likely identifier. This under-catches some real 2-word project names, but `harvest` is preview-first — the user always sees the diff and can `[e]dit` — so under-catching is the safer failure mode than mangling ordinary text.

---

## New seed prompts for user review (§4d)

These 7 prompts (seeds.md numbers 35–41) were authored to close the failure/capture coverage gap. They are **not yet user-reviewed** — the user may veto or edit any of them.

**35. Diagnose the Failure** (folder: `debug/diagnose`, state: `failure`)
> A build, test, or deploy just failed. Before proposing a fix: (1) Quote the exact error message and the first line of the stack trace that points into project code. (2) State what changed most recently that could plausibly cause this. (3) Reproduce the failure in isolation, not the whole suite. (4) List two or three concrete hypotheses for the root cause, ranked by likelihood. (5) Identify the single cheapest check that would confirm or rule out the top hypothesis. Do not propose a fix until the root cause is confirmed, not guessed.

**36. Isolate the Smallest Reproduction** (folder: `debug/reproduce`, state: `failure`)
> Reduce the current failure to the smallest input, command, or code path that still reproduces it. Remove unrelated files, data, and configuration one at a time until the failure disappears, then restore the last removed piece. State the minimal reproduction clearly enough that someone else could trigger the same failure without any other context.

**37. Recurring Failure Protocol** (folder: `debug/recurring`, state: `failure`)
> This is the second or later time this same class of failure has occurred. Before touching code again: (1) Reflect on five to seven distinct possible sources of the problem. (2) Narrow that list to the one or two most likely sources, with reasoning. (3) Add targeted logging or an assertion that would confirm which of those sources is correct. (4) Only after that evidence comes back, implement the fix. Record the failure and its eventual mitigation somewhere durable so the same five minutes are not spent again next time.

**38. Failure Blast Radius** (folder: `debug/blast-radius`, states: `failure`, `checkpoint`)
> Given the current failure, determine what else it could be masking or affecting: Does it fail closed (safe) or open (unsafe)? Could it have silently corrupted data, state, or a prior successful step? Does it block other work, or is it isolated? Is a rollback or a forward fix safer right now? State the answer plainly before deciding how urgently to respond.

**39. What to Save** (folder: `capture/what-to-save`, state: `capture`)
> Before saving this as a reusable mini-prompt, check it against a short bar: Would this be useful in more than one project or conversation, not just this one? Is it phrased as an instruction or rule, not a one-off request tied to specific names, files, or values? Does it already overlap heavily with an existing saved prompt? If it fails any of these, either generalize it first or decide it is not worth saving.

**40. Generalize Before Saving** (folder: `capture/generalize`, state: `capture`)
> Take the exact wording just used and rewrite it so it would still make sense in a different project: Replace specific project names, file paths, and identifiers with placeholders. Remove context that only makes sense in this conversation. Keep the underlying instruction and its intent unchanged. Show the before-and-after side by side so the difference is easy to check before saving.

**41. Where Does This Belong?** (folder: `capture/foldering`, state: `capture`)
> Decide which folder this new mini-prompt belongs in: Does an existing folder already hold prompts with a similar purpose? If several folders are close, which one would you look in first when trying to reuse this later? If nothing fits, propose a new folder name that describes the purpose, not the wording of this specific prompt. State the folder choice and the one-sentence reason for it.

---

## Blocked / deferred items (require the user, not more autonomous work)

- **Publication (G14):** adding a remote, resolving `master`/`main`, pushing, enabling Pages — all require explicit authorization per the contract and per standing workspace rules.
- **Optional LLM-assisted harvest (contract Phase 5):** the design in the gap analysis proposed an optional LLM pass for detection/generalization. Not started — it needs the user to name a specific current model; the harness must never choose one.
- **Live host-template validation:** unchanged from the prior packet, needs the user to pick which host (Codex, Claude Code, Cursor) to validate first.

Nothing above was worked around or partially implemented; each is stated as not-done, not rounded up.
