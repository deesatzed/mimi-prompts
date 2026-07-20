# UX Critical Review, Gap Analysis, and Smart-Feature Proposal

**Date:** 2026-07-19
**Method:** Handoff audit plus live CLI probes executed against temporary storage only
(`scratchpad/ux_probe.json`). No user prompt store was read or modified. No LLM was invoked
(`llm_calls=0` for this review). Every finding cites code or a reproduced command result.
**Scope:** (1) review of `HANDOFF_LATEST.md`, (2) critical UX/workflow review, (3) gap analysis,
(4) proposed "smart" features — centered on context-entry harvesting with generalization,
consent, and folder recommendation. Section 5 is a proposed build checklist that requires
explicit approval before any implementation.

---

## 1. Handoff review (`HANDOFF_LATEST.md` → `HANDOFF_2026-07-19.md`)

The packet is unusually good: evidence-linked claims, machine-readable summary, explicit
blockers, and honest separation of "artifact exists" from "deployed and proven". Structure,
continuity checklist, and publication-authorization gating all check out.

**One material discrepancy found by re-running verification:**

| Handoff claim | Re-verified result | Evidence |
| --- | --- | --- |
| "49 passed, 0 failed, 0 skipped on 2026-07-19" | **48 passed, 1 FAILED** on the current tree | `tests/test_docs.py:24` — `AssertionError: 'mini suggest' not found in HANDOFF_LATEST.md` |

Root cause: `test_docs.py` requires key docs (including `HANDOFF_LATEST.md`) to contain the
literal phrase `mini suggest`. The new packet only shows
`mini --storage "$PWD/..." suggest --interactive`, so the literal substring is absent. The
handoff that asserts a fresh full pass is itself the file that broke the doc gate — the
verification run predates (or excluded) the symlink flip to the new packet.

**Action plan (required by workspace rule: any <100% test result needs one):**

1. Add one literal `mini suggest --context "..."` example line to `HANDOFF_2026-07-19.md`
   (e.g., in the Quick Resume Checklist or How to Run section).
2. Re-run `python3 -m unittest discover -s tests -v`; confirm 49/49.
3. Adopt a standing rule: regenerate a handoff **then** run the suite before updating the
   `HANDOFF_LATEST.md` symlink, because the doc tests read through the symlink.

Minor handoff nits: the "49 offline regression/behavior tests" figure is embedded in three
places (prose, checklist, JSON) and will drift; consider referencing the suite instead of the
count. Everything else in the packet matched what I could re-verify (branch `master`, no
remote, 34 seeds, tabletop/release scripts present).

---

## 2. Critical UX and workflow review

The core interaction bet — never show a catalog, show at most three explainable choices — is
right, implemented, and tested. The critique below is about what happens at the edges of that
happy path, verified against the real CLI.

### 2.1 Suggestion honesty and quality

**F1 — The explanation string can lie.** `ranking.py:64` builds
`reason=f"matches {state}; used {count}x"` for *every* candidate, including fallback
candidates that do **not** carry the state (`candidates = matching or prompts` at
`ranking.py:44-45`). A user in a state with no tagged prompts is told each suggestion
"matches" their state. For a product whose differentiator is explainable ranking, this is the
single most important credibility defect.

**F2 — Off-vocabulary contexts degrade to an alphabetical shelf.** Probe:
`suggest --context "I want to refactor the payment module safely"` → state `general`, and the
three suggestions were `seed-01`, `seed-03`, `seed-05` — i.e., ID order, because only 3 of 34
seeds are tagged `general` and token overlap was zero. The classifier
(`classifier.py:18-33`) is a small hardcoded keyword list; anything outside it ("refactor",
"migrate", "optimize", "security") gets generic suggestions with a confident-looking
explanation. State coverage in the seed panel is also lopsided: proposal 17, checkpoint 13,
completion 6, question 5, undecided 4, general 3, **failure 2, capture 0** — so the "build
failed" journey, a headline scenario, can only ever offer the same two prompts.

**F3 — Reading a prompt costs a selection.** In the interactive loop there is no way to view
a *candidate's* full text before choosing it: `p`/`c` preview only already-selected prompts
(`cli.py:201-214`), and choosing a number immediately calls `record_selection`
(`navigator.py:48`). Curious reading permanently inflates the frequency signal the ranker
uses. `b` (back) pops the selection list but does not decrement `selection_count`
(`navigator.py:64-69`), so there is no undo. This quietly corrupts the product's second
ranking input.

**F4 — Two-step non-interactive selection can shift under the user.** `suggest` then
`suggest --choice 2` re-ranks from scratch on the second invocation (`cli.py:142-147`).
Today ranking is deterministic, but any interleaved selection changes counts and can reorder
the page between the invocation the user *read* and the one they *chose from*.

### 2.2 First-run and discoverability

**F5 — The empty-store hint teaches the wrong command.** Probe on an empty store printed
`Seed the included panel with: mini seed --panel seeds.md` (`cli.py:138,161`). For an
installed user, `seeds.md` does not exist in their CWD; plain `mini seed` works and uses the
packaged panel. Already logged as debt in the handoff; confirmed live.

**F6 — The footer hint is not runnable syntax.** Non-interactive footer:
`[1-3] use  [--offset 3] more  [new context] try again  [capture] add thought`
(`cli.py:171`). `--offset 3` and `capture` are fragments, not commands a user can copy; the
actual invocations are `mini suggest --context "..." --offset 3` and `mini capture "..."`.
The interactive loop is where `[m]`-style hints belong; the one-shot surface should print
copy-pasteable commands.

**F7 — Nine single-letter actions, no help key.** The interactive prompt crams
`1-3 m n p c r a b q` into one line (`cli.py:183-186`). `m` (more) vs `n` (nest) is a
memory test, and there is no `h`/`?` action to re-explain; the error line just re-lists the
letters (`cli.py:243`).

**F8 — Storage targeting is easy to get wrong.** `--storage` is a global pre-subcommand flag
defaulting to the real library (`cli.py:267`). Experimenting safely requires typing the flag
on every call; there is no environment-variable override and no visible indicator of which
store a session is mutating. A mistyped experiment lands in the user's real library.

### 2.3 Library lifecycle

**F9 — There is no way out.** The CLI has save/list/get/search/capture but no `delete`,
`rename`, or `edit`. A bad capture (see F10) is permanent from the CLI surface; the user must
hand-edit JSON, which the atomic-storage design otherwise tries to protect them from.

**F10 — Capture output is low quality, verified.** Probe:
`mini capture "Always check for race conditions in my async FastAPI handlers before approving the PR for the acme-billing repo"` produced:

- name `always-check-for-race-conditions-in-my-async-fastapi-handlers-be` — mid-word 64-char
  truncation (`capture.py:22`);
- prompt text stored verbatim with project-specific nouns (`acme-billing`) that make it
  useless outside one repo;
- tags `captured, workflow, general` and category `workflow` — the same category as all 34
  seeds, so the taxonomy dimension carries zero information (verified: every stored prompt
  has `category: workflow`);
- no duplicate check against the existing panel.

**F11 — Test-fit special case in production code.** `capture.py:32-34` hardcodes: if the text
contains "scenario" or "tabletop", the draft is named `tabletop-scenarios-before-deciding`.
Any unrelated capture mentioning "scenario" silently gets this name, and because capture
names collide it auto-versions confusingly. This is demo-shaped logic in a codebase whose
contract forbids demo behavior; it should be removed.

**F12 — `mini list` shows `id | name` where they are identical.** All seeds have
`name == id` (verified in the store), while human titles ("Explain It Simply") exist in
`seeds.md` headers and are discarded by the slug. The catalog surface reads as machine noise.

### 2.4 Abandoned feedback loop

**F13 — Success/failure plumbing is dead in the new UX.** `core.py` still carries
`log_usage`, `success_count`/`failure_count`, and `get_underperforming_prompts`, but no CLI
or navigator path ever asks "did that prompt help?" or surfaces underperformers. The
"self-improving" half of the original product idea currently has no user-facing loop at all —
only `selection_count` moves.

**F14 — Hardcoded model default.** `mine` defaults to `--model qwen2.5-coder:32b`
(`cli.py:303`). Workspace rule: the user selects all model versions. The default should be
required-from-user (or config-file supplied), never baked into the code.

---

## 3. Gap analysis

| # | Gap | Severity | Evidence | Direction |
| --- | --- | --- | --- | --- |
| G1 | Handoff verification claim vs actual 48/49 | High (process integrity) | §1 | Action plan in §1; re-run before symlink flip |
| G2 | Untruthful "matches state" reason on fallback | High (product credibility) | F1 | Honest reasons: "closest available; no <state> prompts yet" |
| G3 | Selection-count pollution: no preview-before-select, no undo | High (data integrity) | F3 | `?N` read-only view; `b` decrements the count it added |
| G4 | Capture keeps specifics, bad names, no dedupe, flat taxonomy | High (core loop value) | F10, F12 | §4 Smart Capture Advisor |
| G5 | No delete/rename/edit | Medium-High | F9 | `mini rm/rename/edit` with confirmation |
| G6 | Off-vocabulary → generic page; failure=2, capture=0 seed coverage | Medium | F2 | Clarify-question fallback (§4-E); rebalance seed panel |
| G7 | First-run hints wrong/non-runnable | Medium | F5, F6 | Print exact installed-form commands |
| G8 | Storage targeting risk | Medium | F8 | `MINI_STORAGE` env var + store path banner in interactive mode |
| G9 | Feedback loop absent (self-improvement promise) | Medium | F13 | §4-D outcome capture |
| G10 | Two-step `--choice` page drift | Low | F4 | Echo page fingerprint; warn if it changed |
| G11 | Interactive action overload, no help key | Low | F7 | `h` help; group hints; two-line menu |
| G12 | Test-fit hardcoded capture name | Low (but contract-relevant) | F11 | Delete the special case; fix affected test honestly |
| G13 | Hardcoded LLM model default | Low | F14 | Require user-supplied model |
| G14 | Publication gaps (remote, master/main, Pages, live host test) | Known | Handoff §Next Steps | Unchanged; awaiting authorization |

---

## 4. Proposed smart features

Design constraints honored throughout: **no history scraping** (input is only what the user
pastes or pipes), **no auto-save** (every write is previewed and confirmed), **no mandatory
LLM** (every feature has a deterministic path; the optional LLM path uses the existing
`chat_completion_fn` convention and a user-chosen model). These match the current
CLAUDE.md/GOAL contract, so none of this requires a contract change — only checklist
approval.

### 4-A. Smart Capture Advisor — `mini harvest` (the requested centerpiece)

Turns "things I just told my AI tool" into generalized, well-filed library entries — with the
user approving every step.

```
$ mini harvest --file session_notes.md        # or --text "...", or stdin
Found 2 reusable instruction candidates in the supplied context:

[1/2] Original (yours):
  "Always check for race conditions in my async FastAPI handlers before
   approving the PR for the acme-billing repo"
Generalized (proposed):
  "Before approving a PR that touches async handlers, explicitly check for
   race conditions: shared state, awaited ordering, and cancellation paths."
  changes: dropped 'acme-billing', 'FastAPI' → 'async handlers'   [kept intent]
Suggested name:   review-async-race-conditions
Suggested folder: review/async        (reason: imperative review rule; matches
                  tags of 3 existing review/ prompts; confidence: medium)
Similar existing: seed-25-edge-case-review (41% overlap) — not a duplicate
Save [g]eneralized / [o]riginal / [e]dit / change [f]older / [s]kip?
```

Pipeline (each stage independently testable):

1. **Detect** — deterministic candidate extraction from the supplied text only: sentences
   with imperative openings, rule markers ("always", "never", "before X do Y", "make sure"),
   length bounds, and instruction-vs-narration filtering. Optional LLM pass may *add*
   candidates; it can never bypass the preview.
2. **Generalize** — deterministic pass strips or parameterizes specifics (repo/project
   names, file paths, versions, personal names → `{project}`, `{file}`, …) and shows an
   original-vs-generalized diff. Optional LLM rewrite ("generalize, preserve intent, add
   nothing") is displayed the same way; the user can always keep the original verbatim.
3. **Ask** — per-candidate consent, exactly as capture does today but at batch scale.
   Nothing persists without an explicit keypress; `--json` mode emits drafts for host
   adapters and never saves.
4. **File** — recommend a folder (see 4-B) with a stated reason and confidence; the user
   confirms, overrides, or creates a new folder inline.
5. **Dedupe** — token-Jaccard against the store; above a threshold, offer
   *update existing / save as variant / skip* instead of silently minting near-duplicates.

This also replaces today's weak single-shot capture path: `mini capture` becomes
`harvest` with one candidate, fixing F10/F11 (real names from the instruction's verb-object
core, no mid-word truncation, no hardcoded special cases).

### 4-B. Folder taxonomy (currently a dead dimension)

`category` becomes a path (`review/async`, `decide/tradeoffs`, `ship/release`), stored in the
same JSON — folders are logical, not directories. Storage bumps to schema v3 with a trivial
migration (`workflow` → seed-appropriate folders, mapped once from the existing
`_STATE_BY_NUMBER` table plus seed titles). New commands: `mini folders` (tree with counts)
and folder filters on `list`/`suggest`. Folder recommendation scoring: token overlap with
each folder's member prompts + workflow-state affinity; below threshold it proposes a new
folder name instead of forcing a bad fit.

### 4-C. In-context capture nudges (asking, never taking)

During `suggest --interactive`, when the retry/context text itself looks like a reusable rule
(capture-style language, imperative rule shape), the loop appends one line:
`That reads like a reusable rule — press [a] to review it as a capture draft.` It points at
the existing consent flow; it never saves and never fires more than once per session.

### 4-D. Outcome feedback that closes the loop

After a selection, the interactive loop's exit (and the next `suggest` in one-shot mode)
asks once: `Did 'review-async-race-conditions' help? [y/n/skip]` wiring the already-present
`log_usage`. `mini stats` surfaces `get_underperforming_prompts` with a nudge toward
`improve`. This makes the "self-improving" claim real instead of latent.

### 4-E. Honest, self-aware ranking

- Fix F1: fallback candidates say `closest available — no <state> prompts in your library`,
  which doubles as an organic nudge to capture/harvest for that state.
- When state is `general` **and** token overlap is zero (the F2 degenerate case), replace the
  false-confidence page with one clarifying keypress:
  `No strong signal. Is this about [d]eciding, [r]eviewing, [s]hipping, or [x] just show something?`
  — one deterministic question, no LLM required.
- Add `?N` (view candidate N without selecting, F3) and make `b` decrement the
  `selection_count` its own `select` added (G3).

### 4-F. Explicitly out of scope without new approval

Automatic conversation-history scraping, background daemons, auto-save of any draft, network
services, and any bundled/default model choice. These would violate the standing contract;
none of the above features need them.

---

## 5. Proposed build checklist (requires approval before any implementation)

Gate for every phase: full unittest suite 100%, tabletop `--assert` 10/10 with `llm_calls=0`,
`release_check` PASS, compile + `git diff --check` clean. No phase starts before the previous
phase's gate passes.

- **Phase 0 — Restore verification integrity**
  - [ ] Apply the §1 action plan (handoff doc fix); suite back to 49/49.
- **Phase 1 — Truthfulness and safety fixes (G2, G3, G7, G8, G10, G12, G13)**
  - [ ] Honest fallback reasons; `?N` preview; `b` count-undo; runnable hint text;
        `MINI_STORAGE` env var + store banner; remove capture special case; require
        user-supplied model for `mine`.
  - [ ] New/updated tests for each behavior.
- **Phase 2 — Library lifecycle (G5, F12)**
  - [ ] `mini rm` / `rename` / `edit` with confirmation; human titles in `list`; seed titles
        preserved from `seeds.md` headers.
- **Phase 3 — Smart Capture Advisor, deterministic core (G4) + folders (4-B)**
  - [ ] Schema v3 migration with fail-closed tests; `harvest` detect/generalize/ask/file/
        dedupe pipeline; `folders` command; capture unified into harvest.
- **Phase 4 — Feedback loop + clarify fallback (G6, G9; 4-C/D/E)**
  - [ ] Outcome prompt wiring `log_usage`; `stats`; clarify-question fallback; seed-panel
        rebalance for `failure`/`capture` states (authored, reviewed prompts only).
- **Phase 5 — Optional LLM enhancement (only if scope approved)**
  - [ ] LLM generalization/detection passes behind `chat_completion_fn`; model chosen by the
        user at invocation; deterministic behavior unchanged when absent.

Publication next steps (remote, master/main, Pages, live host validation) remain exactly as
sequenced in `HANDOFF_LATEST.md` and still await explicit authorization.
