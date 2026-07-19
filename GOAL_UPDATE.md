# GOAL UPDATE — Complete the Terminal Workflow Contract

## Why this update exists

The SOTAppR and UX audits found that the Workflow Prompt Navigator's core recommendation engine is verified, but three P0 interaction gaps keep it from being a credible public-facing pilot:

1. An empty library does not guide a new user to the reviewed seed panel.
2. The interactive terminal loop does not visibly expose nested prompt preview and composition, even though the navigator can create a preview.
3. `more` does not explain when no further matching prompt page exists.

This update closes only those gaps. It does not add a web UI, hosted account, sync, automatic conversation scraping, automatic prompt mutation, model requirement, or global agent installation.

## Outcome

A new or returning terminal user can reach a useful next action without a long catalog:

- an empty store tells them how to seed the included panel, without changing storage;
- every interactive session visibly offers `n` (next prompt layer), `p` (preview selected composition), `c` (print/compose the selected prompt text), and `b` (back out);
- `more` reports that the current result set is exhausted and suggests retry/capture rather than silently re-rendering the same page.

The existing constraints remain controlling: at most three numbered choices; explicit numeric choices alone increment `selection_count`; composition, preview, paging, retry, and back never increment frequency; all required behavior remains offline and standard-library-only.

## Authority

1. This update for the P0 UX implementation scope.
2. `GOAL.md` for existing product boundaries and safety constraints.
3. `docs/reports/SOTAPPR_2026-07-18.md` and `UX_Analysis_2026-07-18.md` for the audit findings.
4. Existing implementation, tests, and fresh command output for behavior truth.

## Chosen design

Use a small terminal state-machine extension rather than a GUI or host-specific integration:

```
empty store -> seed guidance (no mutation)
seeded page -> [1-3] select | [m] more | [r] retry | [a] capture
selected path -> [n] nested layer | [p] preview | [c] compose | [b] back
final page -> clear exhaustion message -> retry or capture
```

The navigator remains the source of truth for session selection/path behavior. The CLI only renders state and routes user actions. `back` must restore an ordinary full ranked page for the remaining selected path so a user can change direction safely.

## Required behaviors

1. A noninteractive `suggest` on an empty store exits successfully, prints a concise no-saved-prompts message, and includes the exact reviewed seed action `mini seed --panel seeds.md`. It must not create, seed, or mutate the supplied storage file.
2. In the interactive loop, the action prompt includes `n`, `p`, `c`, and `b` with plain-language labels.
3. `n` opens a new page excluding currently selected IDs. It performs no selection mutation.
4. `p` prints the current composition preview. It performs no selection mutation.
5. `c` prints the current selected prompt composition. It performs no selection mutation and does not execute prompt text.
6. `b` removes the most recent selected prompt from the current session path, restores normal ranked candidates for the remaining path, and does not change any persisted frequency count.
7. On the final page, `m` reports that there are no more matching prompts and directs the user to retry or add a thought. It does not change page, selection path, or frequency.
8. Existing direct/module CLI compatibility, JSON suggestion schema, seed idempotence, capture confirmation, ranking invariants, atomic storage, and reference adapters remain intact.

## Test-first execution and proof

Before implementation code, add focused failing tests for:

- empty-store seed guidance and no storage mutation;
- exhausted `more` messaging;
- visible interactive nesting actions and a scripted select → nest → preview → compose → back flow;
- navigator back restoration and no extra selection-count mutation.

For each test, run the focused test to observe the expected failure, then make the smallest change to pass it. Completion requires fresh passing output for:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json
python3 scripts/release_check.py
python3 -m py_compile core.py cli.py seeds.py minipromptlib/*.py scripts/*.py tests/*.py
git diff --check
```

Also save a temporary-storage CLI transcript proving all three P0 behaviors. Update `PROGRESS.md`, `DECISIONS.md`, README/help text if behavior wording changes, and the dated audit reports only if their claims become stale.

## Stop rules

Stop and report rather than expanding scope if completing the update would require credentials, a live prompt library, a hosted service, global agent configuration, destructive storage changes, or a GUI. Preserve the existing untracked `idea2_app_directions.md` and the audit reports as separate work.
