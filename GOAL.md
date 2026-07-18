/goal

# Build MiniPromptLib into the Workflow Prompt Navigator

## OUTCOME

Turn the current MiniPromptLib prototype into an installable, offline-first app that helps a user choose and reuse the right workflow mini-prompt during an AI conversation or software build.

The finished app must recognize the immediate workflow state, show only two or three numbered suggestions, rank them using both logical relevance and the user's explicit selection frequency, and support choosing by number, `more`, `try again`, nesting, composition preview, and reviewed capture of new prompts. It must work without an LLM, API key, network service, hosted account, or access to the user's real prompt library.

The primary implementation surface is a fast `mini` command backed by a reusable Python engine and a versioned scriptable contract for thin agent adapters. A standalone web/desktop UI is not part of this goal.

## AUTHORITY AND STARTING TRUTH

Use this authority order when sources disagree:

1. `GOAL.md` — completion contract and boundaries.
2. `docs/plans/2026-07-18-workflow-prompt-navigator-design.md` — approved product and architecture design.
3. `docs/plans/2026-07-18-workflow-prompt-navigator-implementation.md` — test-first execution sequence.
4. `seeds.md` — user-authored seed source; determine its actual numbered count from the file.
5. Current code and actual command output — implementation truth.
6. `HANDOFF_2026-07-18.md`, `HANDOFF.md`, `README.md`, `CLAUDE.md`, `idea1.md`, and `idea2_app_directions.md` — useful historical context that may contain stale claims.

Current verified starting facts:

- The repository is on `master`; the approved design was committed as `d5f2fbb`.
- The current implementation is root-level `core.py`, `cli.py`, and `__init__.py` with standard-library-only runtime behavior.
- There was no automated test suite or package manifest at goal creation time.
- The current storage loader silently treats unreadable JSON as an empty library; this is a data-safety gap to repair.
- Existing LLM-backed selection, improvement, and mining paths have not been proven against a live backend and cannot be required for core completion.
- `seeds.py` contains two entries while `seeds.md` currently contains 34 numbered source prompts; derive the count from the live file rather than trusting the older handoff's 30-prompt claim or a stale snapshot.
- Pre-existing untracked files include `HANDOFF_2026-07-18.md`, `HANDOFF_LATEST.md`, `idea2_app_directions.md`, `seeds.md`, and `seeds.py`. Preserve ownership and do not normalize or discard them. Modify only those explicitly placed in scope below.

## SEED PANEL INTEGRATION (REVIEWED)

`seeds.md` is not merely a future idea list. It is reviewed source material for the first useful library and must be represented in the actual seed catalog during this goal.

- Preserve the authored text of every current numbered item (1 through 34) as the source prompt text; derive names, tags, categories, and `workflow_states` in code without silently rewriting the author's intent.
- Make the process-first cohort immediately useful for the navigator: #2 Required or Scope Drift, #4 Work Backward from Real Problems, #5 Interactive Terminal Guide, #6 Confirm We Are in Sync, #9 Contrarian Product Review, #14–19 planning/UX prompts, #21–22 minimum/necessity prompts, #25–31 edge-case/safety/handoff/clone prompts, and #32–34 uncertainty, documentation, and status prompts.
- Map that cohort to workflow states. For example: #32 supports `undecided`; #4, #7–8, #11–17, and #21–24 support `proposal` or `question`; #9, #14–15, #19, #25–29 support `checkpoint`; #10, #30–31, #33–34 support `completion`; #5 and #25 support `failure`/recovery; and #26 provides reversible-operation guidance.
- Treat #31's clone-test text and #10's commit/push wording as reusable prompt content only. The app must never automatically push, publish, clone external repositories, or perform destructive work merely because a saved prompt contains those words.
- Seed conversion is deterministic and offline. Newly captured prompts may be added only after preview and confirmation; they must not overwrite or deduplicate away an authored source prompt without an explicit reviewed migration.

## PROOF OF DONE

All of the following must be true using fresh command output and saved evidence:

1. `python3 -m unittest discover -s tests -v` exits 0 with every test passing.
2. `python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json` exits 0 and the artifact records all ten approved tabletop scenarios as `PASS` with `llm_calls: 0`.
3. `python3 scripts/release_check.py` exits 0 and proves package import, root compatibility imports, direct CLI use, installed-style `mini` behavior, isolated persistence, seed completeness/idempotence, documentation commands, and artifact validity.
4. `python3 -m py_compile core.py cli.py seeds.py minipromptlib/*.py scripts/*.py tests/*.py` exits 0.
5. A temporary-storage CLI demonstration proves all of these observable UX conditions:
   - the first page contains no more than three numbered suggestions;
   - entering a number returns the selected mini-prompt;
   - `more` returns the next non-repeating small page;
   - `try again` recomputes suggestions from revised context;
   - a nested prompt can be previewed, explicitly composed, or backed out;
   - prompt capture requires preview/confirmation before saving.
6. Ranking tests prove both required invariants:
   - when logical relevance is comparable, the higher `selection_count` ranks higher;
   - a very frequent but irrelevant prompt cannot outrank a clearly relevant low-frequency or new prompt.
7. Selection semantics are proven: an explicit selection increments `selection_count` exactly once; display, paging, preview, and cancellation do not increment it; existing usage/success/failure signals remain separate.
8. Storage tests prove backward-compatible legacy loading, schema migration, atomic writes, and preservation of the exact source bytes when storage is corrupt. No recovery path silently overwrites an unreadable library.
9. Every numbered entry found in `seeds.md` has a deterministic, uniquely named, workflow-aware seed representation; repeat seeding without overwrite is idempotent.
10. `mini --help`, `python3 -m minipromptlib.cli --help`, and `python3 cli.py --help` exit 0 after the packaging migration.
11. The core suggest/select/more/retry/nest/capture workflow completes without a configured LLM, network, credentials, or optional package.
12. `README.md`, `CLAUDE.md`, `HANDOFF.md`, the current dated/latest handoff surface, `PROGRESS.md`, and `DECISIONS.md` describe actual implemented behavior, actual verification output, remaining limitations, and dirty-state truth without overstating automatic agent integration.
13. `git diff --check` exits 0.
14. `git status --short --branch` is inspected at completion; the final report separates goal changes from pre-existing/unrelated files and lists every changed file, verification result, deferred item, and remaining risk.

## SCOPE

### Modify or create

- Root control and compatibility files: `GOAL.md`, `PROGRESS.md`, `DECISIONS.md`, `pyproject.toml`, `core.py`, `cli.py`, `__init__.py`, `seeds.py`.
- Canonical package: `minipromptlib/**`.
- Automated verification: `tests/**`, `tests/fixtures/**`, `scripts/tabletop_demo.py`, `scripts/release_check.py`.
- Approved product artifacts: `docs/plans/2026-07-18-workflow-prompt-navigator-design.md`, `docs/plans/2026-07-18-workflow-prompt-navigator-implementation.md`, `docs/integrations.md`, `docs/reports/tabletop-results.json`.
- Thin, repo-local reference adapters only: `integrations/codex/**`, `integrations/claude/**`.
- Truthful user/agent documentation: `README.md`, `CLAUDE.md`, `HANDOFF.md`, `HANDOFF_2026-07-18.md`, `HANDOFF_LATEST.md`.
- User-authored source `seeds.md` only if a minimal correction is necessary to make its own numbering/format internally valid; otherwise treat its wording as protected input.

### Read/reference

- `idea1.md` and `idea2_app_directions.md`.
- Git history and current worktree status.
- Existing code paths and documented examples.

### Do not modify or access

- The user's live `~/.miniprompts/prompts.json` or any other real prompt store.
- Global Codex, Claude, Grok, shell, IDE, or operating-system configuration.
- Files outside `/Volumes/WS4TB/mimi_prompt` except temporary test/install directories.
- Unrelated user work or untracked files not explicitly in the modification list.

## FUNCTIONAL REQUIREMENTS

1. **Workflow first:** classify `question`, `checkpoint`, `completion`, `failure`, `proposal`, `undecided`, `capture`, or `general` from a bounded context packet before topic-level ranking. Explicit adapter state wins over inference.
2. **Progressive choice:** show at most three numbered suggestions by default. Never replace the primary UX with a full prompt catalog.
3. **Logic plus frequency:** use deterministic workflow/text/tag relevance plus a bounded, inspectable frequency boost derived from explicit selections. Return score components or a concise selection reason.
4. **Progressive recovery:** support `more`, `try again`, exhaustion messaging, invalid-choice recovery, and one concise context request when evidence is inadequate.
5. **Number retrieval:** selecting `1`, `2`, or `3` returns the exact corresponding prompt and records one selection.
6. **Nesting:** allow a selected prompt to influence a second small recommendation layer. Preserve the session path, support `back`, and require preview/confirmation before composition.
7. **Quick capture:** turn user wording into an editable draft with proposed name, tags, and workflow states. Never save, rewrite, or overwrite automatically.
8. **Local-first:** all required behavior works offline with the Python standard library. Optional LLM behavior must degrade visibly and safely to deterministic behavior.
9. **Portable surface:** provide an installable `mini` console command, direct/module compatibility, versioned JSON input/output, and thin reference adapters that call the shared engine.
10. **Safe personal asset:** keep JSON human-readable and backward compatible, add schema versioning and atomic writes, and fail closed on corruption without destroying recoverable data.

## CONSTRAINTS

- Follow the approved design and execute the implementation plan in order unless fresh evidence requires a documented deviation.
- Preserve current public CRUD/search/import/export/LLM-callable behavior or provide tested compatibility shims and migration notes.
- Keep core runtime dependencies at zero. Do not add embeddings, a vector database, a web framework, or a mandatory LLM SDK.
- Do not weaken, skip, delete, or rewrite tests merely to make the goal pass.
- Do not use the real default prompt path in tests, demos, release checks, or screenshots. Every verification path must supply a temporary storage location.
- Do not conflate `selection_count` with `usage_count`, success, or failure. Historical fields remain intact.
- Do not let optional LLM output become the source of truth for workflow classification, seed conversion, persistence, or completion evidence.
- Do not implement hosted accounts, multi-user sync, passive surveillance, automatic conversation scraping, autonomous prompt mutation, or production deployment.
- Do not introduce clinical recommendations, medical logic, HIPAA claims, or patient-specific behavior. Healthcare-related prompt text is inert user-authored content only.
- Preserve user voice in seed/capture text. Any cleanup must be previewable and reversible.
- Make local commits in small, scoped batches if useful; do not push, publish, deploy, install global integrations, or alter remotes without separate user authorization.
- Keep unrelated dirty/untracked work visible. Never use destructive reset/checkout/cleanup operations.

## SAFETY / PROVENANCE

- Treat prompts and conversation context as potentially private. Pass only bounded context supplied to the app; never scrape full histories by default.
- Keep external-model use opt-in and explicitly configured. Never search for, print, copy, or persist credentials.
- Distinguish deterministic offline results from optional LLM-assisted results in outputs and docs.
- Preserve authored prompt provenance through stable IDs and source metadata where practical.
- Treat saved test reports as evidence only for the exact code and fixtures tested; do not relabel tabletop or synthetic results as real-world adoption evidence.
- Preserve corrupt or legacy storage before migration/recovery and provide an actionable error or dry-run preview.

## ITERATION

1. Before editing implementation code, reread this goal, the design, the implementation plan, current git status, and the relevant current module.
2. Create or update `PROGRESS.md` immediately with the baseline state, assumptions, pre-existing dirty files, and first verification result.
3. Follow test-driven development for each task: write the nearest failing test, run it and confirm the expected failure, implement the smallest coherent change, then rerun focused tests.
4. Work through the implementation plan in small batches. Do not start a later UX/integration phase while the underlying storage, classifier, or ranking phase is failing.
5. After each batch, record changed files, exact commands/results, decisions, and remaining risks in `PROGRESS.md`. Record architecture, schema, ranking, privacy, compatibility, and scope decisions in `DECISIONS.md`.
6. On a failed check, diagnose the root cause and repair it before expanding scope. After a second consecutive failure, change strategy and document the mitigation. Stop after three distinct unsuccessful repair attempts on the same blocker.
7. Use temporary directories and fixtures for all mutation-heavy tests. Keep demos deterministic and network-free.
8. Rerun the focused suite after each task and the full proof surface before claiming completion.
9. When implementation evidence contradicts a handoff or README claim, preserve the live evidence and update the stale documentation.
10. Defer attractive adjacent ideas explicitly in `PROGRESS.md` rather than partially implementing them.

## STOP

Stop implementation, preserve the worktree, and provide a concise blocker report if:

- any step requires credentials, API keys, paid model calls, user accounts, or external private data;
- completing the goal would require accessing or mutating the user's live prompt library;
- a destructive migration cannot be made previewable, atomic, and recoverable;
- the same blocking failure remains after three distinct, documented repair attempts;
- a required change would violate the two-or-three-choice UX, deterministic offline completion, bounded frequency invariant, privacy boundary, or protected scope;
- a product decision would materially add hosted services, a standalone GUI, passive monitoring, automatic prompt mutation, or another deferred capability;
- production deployment, publishing, pushing, global installation, or global agent configuration becomes necessary;
- legal, privacy, clinical, or sensitive-data uncertainty appears that cannot be resolved from local inert fixtures and existing requirements.

Do not stop for ordinary implementation uncertainty when a safe, reversible assumption can be made. Record the assumption in `PROGRESS.md` and continue.

## COMPLETE

Mark this goal complete only when every `PROOF OF DONE` item passes with current command output or file-inspection evidence, the tabletop artifact is saved and valid, documentation matches behavior, and the final dirty-state report is truthful.

Implemented code, a passing subset, an attractive demo, or a locally successful manual interaction is not sufficient by itself. If any required proof remains unavailable or failing, report the goal as incomplete or blocked rather than redefining success.
