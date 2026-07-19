# UX Analysis — Workflow Prompt Navigator

**Date:** 2026-07-18
**Method:** Code-and-command audit. This analysis distinguishes verified local behavior from expected product experience and does not infer real-user satisfaction from automated tests.

## Post-audit update — 2026-07-18

The P0 implementation findings below are historical: the current CLI now guides an empty store to the reviewed seed action, exposes nested `n` / `p` / `c` / `b` actions, and explains exhausted `more`. The verified follow-up transcript is `docs/reports/terminal-workflow-update-2026-07-18.md`. The analysis still correctly identifies unvalidated real-user onboarding, accessibility, and long-term frequency-control evidence as follow-up work.

## 1. Executive assessment

The app is a local, installable terminal workflow navigator for semi-technical AI-tool users. Its strongest interaction decision is correct: it narrows a moment of uncertainty to a maximum of three numbered prompts instead of presenting an exhaustive library. The interaction is technically real and verified: state is inferred from bounded context, ranked prompts are paged in threes, and an explicit choice alone increments the frequency signal [minipromptlib/classifier.py:L8-L34] [minipromptlib/ranking.py:L40-L77] [minipromptlib/navigator.py:L38-L47].

The product is **not yet frictionless for a new user**. A first-run user must know to seed the library. The interactive terminal loop exposes `more`, retry, add, back, and quit, but the promised nested composition is not visibly completed as a preview/compose/back flow [minipromptlib/cli.py:L168-L208]. There is no graphical screen, route, authentication flow, responsive web layout, or persistent live conversation integration; this is a CLI by design, not a missing web implementation [GOAL.md:L7-L11].

**UX health:** yellow — strong workflow core, incomplete first-run and advanced-flow discoverability.

## 2. Product model and intended user

### What the code actually delivers

| User need | Verified delivery | Evidence |
| --- | --- | --- |
| “I am not sure what to do next.” | `undecided` state, followed by no more than three suggestions. | [minipromptlib/classifier.py:L18-L19], [minipromptlib/ranking.py:L73-L77]. |
| “The build failed; help me recover.” | Failure language yields `failure`, then state-matched seed prompts. | [minipromptlib/classifier.py:L20-L23]; fresh CLI result returned two failure prompts. |
| “Let me use the second option.” | `--choice` and interactive numeric choices return the prompt and record selection once. | [minipromptlib/cli.py:L141-L149], [minipromptlib/navigator.py:L38-L47]. |
| “That was not right; show a little more / retry.” | Offset page and revised context reset the session. | [minipromptlib/navigator.py:L26-L36]. |
| “Save this thought for later.” | Capture creates a draft; persistence requires `--confirm` or a terminal confirmation. | [minipromptlib/capture.py:L25-L57], [minipromptlib/cli.py:L211-L227]. |
| “Use it from an agent.” | A versioned JSON command contract plus repository-local templates. | [docs/integrations.md:L3-L11]. |

### Primary persona

The primary persona is an AI-assisted builder who can run terminal commands and wants repeatable process prompts without giving a tool their whole conversation. This is supported by the product’s local JSON storage and its bounded context fields [core.py:L34-L46] [minipromptlib/models.py:L20-L26].

The product does **not** currently serve a non-technical person who expects point-and-click discovery, automatic installation into an agent, mobile access, collaboration, cloud recovery, or plain-language onboarding. Those are out of scope, rather than silently unsupported capabilities [GOAL.md:L109-L122].

## 3. Surface inventory and information architecture

### Actual user-facing surfaces

| Surface | Purpose | State / persistence | UX implication |
| --- | --- | --- | --- |
| `mini seed` | Load the authored seed panel. | Local JSON. | Necessary bootstrap, but currently undiscoverable from an empty `suggest`. |
| `mini suggest` | Return a numbered small page. | Reads local store; selection may mutate only when selected. | Main value moment. |
| `mini suggest --interactive` | Terminal loop. | In-memory navigation session; local mutation on selection/capture. | Discoverable keyboard actions, but complex nesting is incomplete. |
| `mini capture` | Draft then optional confirmation. | Local JSON only on confirmation. | Good protection against accidental prompt mutation. |
| `mini list/get/search` | Library management. | Local JSON. | Secondary expert surface; could tempt catalog-first behavior. |
| JSON adapter contract | Host integration. | No installation or scraping by this app. | Useful for integrators, not turnkey for end users. |

There are no frontend routes, reusable visual components, design tokens, responsive breakpoints, browser states, or authentication screens. The architecture is intentionally terminal-first, as stated in the goal [GOAL.md:L7-L11]. Any UX evaluation should therefore judge command/terminal ergonomics rather than apply web-app expectations.

## 4. Core journey walkthroughs

### Journey A — uncertainty → tabletop prompts → choice

**Goal:** Convert “Not sure, lets run through scenarios or table tops and then decide” into a small decision-support surface.

1. User seeds once: `mini --storage <temporary-path> seed --panel seeds.md`.
2. User invokes `suggest --context` with the uncertainty statement.
3. Classifier recognizes `not sure`, `tabletop`, or `scenarios` in the user message and selects `undecided` [minipromptlib/classifier.py:L18-L19].
4. Ranker retains only prompts tagged for `undecided` if any exist, then applies text overlap and bounded frequency [minipromptlib/ranking.py:L40-L64].
5. CLI returns three numbered choices with IDs, rationale, and count [minipromptlib/cli.py:L109-L165].
6. A number returns the exact prompt and increments only that prompt’s `selection_count` [minipromptlib/navigator.py:L38-L47].

**Fresh faux-result from the verified command:**

| Number | Returned seed | Why it is a reasonable small set |
| ---: | --- | --- |
| 1 | `seed-32-not-sure` | Direct uncertainty cohort. |
| 2 | `seed-07-alien-goggles-brainstorm` | Divergent reframing. |
| 3 | `seed-17-compare-three-solution-levels` | Comparison before commitment. |

**What works:** The response respects the user’s request for “not an extensive list.” The result is explainable rather than opaque.

**Friction:** Before the seed step, the experience has no local prompts. The only fallback output is “No matching prompts. Try again with more context or add a thought” [minipromptlib/cli.py:L155-L165], which does not tell a new user how to unlock the authored seed panel. This is the largest first-run gap.

### Journey B — failed build → recover → more/retry

**Goal:** Help a builder regain orientation after `pytest failed with a traceback`.

1. The failure terms in build status or context classify the packet as `failure` [minipromptlib/classifier.py:L20-L23].
2. The ranker returns only matching failure prompts when available [minipromptlib/ranking.py:L42-L46].
3. In the verified fresh command, the two returned prompts were `seed-05-interactive-terminal-guide` and `seed-25-edge-case-review`.
4. The user can enter a displayed number, press `m` for the next small page, or press `r` and type revised context [minipromptlib/cli.py:L177-L208].

**What works:** Recovery is proportional: an error does not force the user to catalog search or hand a model their transcript. State gating prevents a highly selected completion prompt from winning merely through frequency [minipromptlib/ranking.py:L44-L64].

**Friction:** Failure is not differentiated further (test failure vs dependency failure vs conceptual dead end). The result may be safe but generic. “More” does nothing visibly if there are fewer than four matching results because `more` leaves the offset unchanged [minipromptlib/navigator.py:L26-L30]; the interface does not tell the user that they are at the end.

### Journey C — thought → mini-prompt capture

**Goal:** Preserve a useful sentence without silently changing the library.

1. User runs `capture "..."` or selects `[a] add thought` in interactive mode.
2. A draft gets a derived name, tags, and workflow state but is not persisted [minipromptlib/capture.py:L25-L42].
3. The CLI prints the draft and tells the user to rerun with `--confirm`; interactive mode asks “Save this draft?” [minipromptlib/cli.py:L191-L197], [minipromptlib/cli.py:L211-L227].
4. Only confirmation saves the original wording and then applies metadata [minipromptlib/capture.py:L45-L57].

**What works:** This honors user authorship and removes an especially damaging failure mode: accidental or opaque prompt mutation.

**Friction:** The draft is only lightly editable at the terminal surface. A user cannot easily adjust generated tags/state/name before confirmation except by changing the underlying wording or using the Python API. This is acceptable for v1 but reduces the value of “reviewed capture.”

### Journey D — selection → learned preference

**Goal:** Make real explicit choices improve future tie-breaking without creating an echo chamber.

1. User selects a number.
2. `record_selection` is called from the navigator, and the selected ID is added to the session [minipromptlib/navigator.py:L38-L47].
3. Frequency is normalized logarithmically against candidates and contributes at most two points [minipromptlib/ranking.py:L49-L66].
4. A later same-state, similarly relevant result can move upward; a different-state favorite is excluded when matching candidates exist [minipromptlib/ranking.py:L40-L46].

**What works:** The logic directly implements the user’s requirement: frequency as well as logic, not frequency instead of logic.

**Friction:** The user can see `used Nx` in the JSON/terminal reason but cannot inspect a history, reset it, or understand the exact effect without reading documentation/code. A personal learning system needs an obvious “undo/reset/export” story before broad adoption.

## 5. Interaction-state analysis

| State | Entry | Exit / recovery | Persistence | Risk |
| --- | --- | --- | --- | --- |
| Empty store | New `--storage` file. | Must independently discover `seed` or `save`. | No data. | High abandonment risk. |
| Seeded browse | `seed` succeeds. | `suggest`, list/search, or exit. | 34 source prompts stored. | Low. |
| Suggested page | `navigator.start` and `current_page`. | Choose, more, retry, add, back, quit. | In-memory offset/session. | Low. |
| Chosen prompt | Numeric choice. | Optionally ask for another nested prompt. | Selection count persists. | Medium: no clear composition completion. |
| Nested prompt page | User answers yes to “Add another nested prompt?” | A new page excludes chosen IDs. | Session path. | Medium: UI does not show composition preview/confirm. |
| Capture draft | `capture`/`add`. | Confirm/save or abandon. | Nothing until confirmation. | Low. |
| Corrupt store | JSON cannot be parsed/validated. | Program raises clear error; source untouched. | Source unchanged. | Safe but no user-facing repair flow. |

The visible interactive action prompt is concise and keyboard friendly: `[1-3] use [m] more [r] retry [a] add thought [b] back [q] quit` [minipromptlib/cli.py:L177-L178]. However, action labels do not include `preview` or `compose`, even though the navigator exposes `composition_preview` [minipromptlib/navigator.py:L65-L68]. This creates an expectation/implementation mismatch at the most differentiated advanced interaction.

## 6. Onboarding, discoverability, and error handling

### Onboarding

| Expectation | Reality | Consequence | Priority |
| --- | --- | --- | --- |
| “Install and ask for a prompt.” | User must know installation and run `seed` first. | The first value moment is delayed or missed. | P0 |
| “I can see what the tool needs.” | `--help` lists commands, but empty suggestion does not point to seed. | Help-dependent discovery. | P0 |
| “I can safely try it.” | Temporary storage is supported via `--storage`; default points to a personal path [minipromptlib/cli.py:L230-L233]. | Technically safe, but docs must foreground temp/backup practice. | P1 |

### Errors and recovery

| Situation | Current behavior | Assessment |
| --- | --- | --- |
| Invalid number | Raises/prints `Choose a number from 1 to N.` and keeps loop alive. | Good local recovery [minipromptlib/navigator.py:L38-L47], [minipromptlib/cli.py:L198-L203]. |
| No matching prompt | Tells user to try more context or add a thought. | Incomplete for an empty store; does not explain seed. |
| Corrupt JSON | Raises `StorageCorruptionError` and leaves bytes unchanged. | Strong integrity behavior [minipromptlib/storage.py:L19-L41]. |
| Optional mining unavailable | Shows a clear message that local Ollama is optional. | Honest separation from core [minipromptlib/cli.py:L79-L101]. |
| End of results | `more` does not advance, without an end-of-list message. | Needs explicit exhaustion feedback. |

## 7. Accessibility and responsiveness

This is a terminal application, so conventional responsive browser requirements do not apply. The relevant questions are terminal/keyboard accessibility, legibility, and assistive compatibility.

| Dimension | Evidence | Assessment | Improvement |
| --- | --- | --- | --- |
| Keyboard operation | Every primary interactive action is typed. | Strong. | Preserve non-color text labels. |
| Color dependence | CLI output uses text labels and numbering, not color coding [minipromptlib/cli.py:L155-L165]. | Strong. | Keep it that way. |
| Screen-reader / semantic output | Plain stdout is promising; no accessibility evaluation or alternate verbosity mode exists. | Unknown. | Test with a terminal screen reader; add `--json`/plain output examples. |
| Narrow terminals | Fixed, long prompt names/reasons may wrap unpredictably; no width management exists. | Weak/unknown. | Test at 80 and 40 columns; truncate with a way to reveal full text. |
| Motor/cognitive load | Single-letter shortcuts are efficient but not self-explanatory. | Mixed. | Add a one-line first-run legend and clear end states. |

## 8. AI integration readiness

The agent-facing design is intentionally bounded: integrations can send current user/agent/build fields, must show no more than three returned choices, preserve numbering, and use the same command on selection [docs/integrations.md:L3-L11]. The JSON payload includes state, offset, suggestion number, ID, reason, and selection count [minipromptlib/cli.py:L109-L129]. This is a good thin contract.

What is not present: streaming, tool schemas, event callbacks, host installation, state correction UI, prompt injection defenses beyond bounded context, or a cross-agent session identifier. Those omissions are appropriate for a local v1, but they mean “responsive to the last question the AI asked” is verified only when an adapter actively passes `--agent-message`; it is not automatic conversation awareness [minipromptlib/cli.py:L277-L285].

## 9. Quantified friction register

Scores use 1 (minor) to 5 (blocking). They are audit estimates, not collected usability metrics.

| ID | Friction | Affected journey | Severity | Evidence | Fix |
| --- | --- | --- | ---: | --- | --- |
| F1 | Empty library does not route user to seed. | First-run | 5 | Suggest’s empty state [minipromptlib/cli.py:L155-L165]. | Offer `mini seed --panel seeds.md` guidance without auto-seeding. |
| F2 | Nested composition lacks a visible preview/confirm action. | Advanced choice | 4 | Prompt only asks to add another nested prompt [minipromptlib/cli.py:L204-L206]; preview API is unused [minipromptlib/navigator.py:L65-L68]. | Add `p` preview and `c` compose, with tests. |
| F3 | End of `more` has no explanation. | Recovery | 3 | Offset changes only when another page exists [minipromptlib/navigator.py:L26-L30]. | Print “No more matching prompts; retry or capture.” |
| F4 | Captured metadata cannot be edited in the standard CLI before save. | Capture | 3 | Draft has generated name/tags/state [minipromptlib/capture.py:L36-L42]. | Add optional edit flags or an interactive edit step. |
| F5 | Frequency has no reset/history control. | Long-term use | 3 | Ranking reads `selection_count` [minipromptlib/ranking.py:L49-L66]. | Add inspect/reset/export with confirmation. |
| F6 | Terminal width and assistive behavior untested. | Accessibility | 3 | No width/screen-reader handling in CLI render [minipromptlib/cli.py:L155-L208]. | Manual 40/80-column and assistive test. |
| F7 | Agent adapter is a template rather than live integration. | In-conversation use | 2 | Explicitly documented as copy-only [docs/integrations.md:L9-L11]. | Pilot one explicit, user-installed host integration. |

## 10. Recommendations and acceptance tests

### P0 — solve before a public-facing release

1. **First-run recovery.** When a library has no prompts, say exactly how to seed the included panel and how to use a custom store.
   - Acceptance: a fresh temp storage `suggest` command prints a seed action; it performs no mutation without confirmation.
2. **Finish the nested interaction.** Expose preview, compose, and back actions in the terminal loop.
   - Acceptance: a user can select first prompt, obtain a second small nonrepeating page, preview the composition, explicitly compose it, or back out; only numbered selections change frequency.
3. **Make `more` finite.** Explain exhaustion and direct the user to retry/capture.
   - Acceptance: at final page, `more` produces an unambiguous message and does not change selection counts.

### P1 — validate with observed use

1. Run three to five 10-minute usability sessions with the uncertainty and failed-build scenarios.
2. Measure: time to first successful suggestion, number of retries, whether user finds `more`, whether they understand `used Nx`, and capture completion/abandonment.
3. Add a local selection-history/reset command only if operators ask for control or frequency behavior confuses them.
4. Validate one opt-in Codex or Claude adapter against the versioned JSON contract without scraping or global installation.

## 11. UX verdict

The core experience is valuable and differentiated enough to justify an internal pilot: it gives a fast, workflow-aware, small answer to a large “what prompt now?” problem, while retaining local ownership and deterministic behavior. The exact user wording about tabletop scenarios produces an `undecided` state, three relevant suggestions, and a preview-only capture draft in the fresh audit run.

It is not yet a polished default tool for new users. The most valuable next work is not a broader prompt catalog, model integration, or GUI. It is completing the small interaction contract already promised: guided first run, visible nested composition, and explicit end-of-results feedback.

```json
{
  "date": "2026-07-18",
  "app": "MiniPromptLib Workflow Prompt Navigator",
  "surface": "local terminal CLI with JSON adapter contract",
  "ux_health": "yellow",
  "verified_strengths": [
    "workflow-first deterministic classification",
    "at-most-three numbered choices",
    "logical relevance gated before bounded selection frequency",
    "preview-first capture",
    "offline local persistence with corrupt-store protection"
  ],
  "p0_gaps": [
    "no guided empty-library/first-run recovery",
    "nested composition preview and confirmation are not exposed in the interactive CLI",
    "more has no explicit exhaustion message"
  ],
  "non_goals_confirmed": [
    "no standalone web UI",
    "no hosted account or sync",
    "no automatic conversation scraping",
    "no automatic global agent installation"
  ],
  "release_recommendation": "conditional internal pilot after P0 interaction fixes; not a public-finished release yet",
  "evidence": {
    "tests": 40,
    "tabletop_scenarios": 10,
    "llm_calls": 0,
    "release_check": "pass"
  }
}
```
