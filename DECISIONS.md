# Decisions

## 2026-07-18 — Local JSON remains the v1 store

The prompt library remains a human-readable local JSON file. The persisted form is now a schema-versioned envelope (`schema_version: 2`, `prompts: {...}`), while legacy top-level prompt dictionaries remain readable.

## 2026-07-18 — Corrupt stores fail closed

Unreadable or structurally invalid JSON raises `StorageCorruptionError` and leaves the source bytes unchanged. Writes use a same-directory temporary file, `fsync`, and `os.replace` to avoid partial JSON files.

## 2026-07-18 — Packaging is incremental and compatible

`minipromptlib` is now importable and exposes an installable `mini` entry point. The original root modules remain compatibility surfaces during the workflow-navigator migration so documented direct commands continue to work.

## 2026-07-18 — Workflow state gates frequency

The navigator first limits candidates to matching workflow states when such prompts exist, then ranks text/tag relevance and a bounded logarithmic `selection_count` boost. This keeps familiar prompts helpful without allowing a popular completion prompt to outrank a relevant failure prompt.

## 2026-07-18 — Seed panel is executable source material

All 34 numbered `seeds.md` prompts are parsed deterministically at seed time. Their authored text is retained, while stable names, tags, and workflow states are derived in code. Instructions embedded in a prompt are content for the AI, not authorization for this application to push, deploy, clone, or mutate external state.

## 2026-07-18 — Integration remains local and opt-in

Codex and Claude reference adapters consume the versioned local JSON contract and pass bounded current context only. They do not scrape histories, auto-save, or call external models. No global integration was installed.

## 2026-07-18 — Terminal recovery must be explicit and non-mutating

An empty prompt library now points the user to the reviewed seed command instead of silently seeding or presenting an unexplained empty result. A final `more` state states that results are exhausted. Both are guidance only and do not mutate storage or preference data.

## 2026-07-18 — Nested composition is a visible session action

The interactive terminal loop exposes nest, preview, compose, and back as explicit actions. Composition prints selected prompt text only; it neither executes prompt content nor saves a prompt. Back removes the most recent session selection and re-ranks the normal candidate set while preserving the persisted count created by the original explicit selection.

## 2026-07-18 — The authored seed panel ships with the package

The reviewed Markdown panel is package data and is resolved with
`importlib.resources`, rather than relying on a repository-relative file at
runtime. An explicit `--panel` argument remains available for a user-owned
alternative panel. This keeps first-use installation portable while preserving
the local, inspectable seed source.

## 2026-07-18 — Public distribution is static, local-first, and MIT

The public landing page is plain HTML/CSS/JavaScript under `site/`; it has no
analytics, remote scripts, backend, or model call. GitHub Pages is configured
to deploy only that directory from `main` after publication is explicitly
authorized. The repository uses the MIT License, while prompt stores and
bounded context remain local by default.

## 2026-07-18 — Host integrations share one narrow contract

Every documented host integration calls `mini suggest --json` with bounded
current context and renders at most three choices. Codex, Claude Code, and
Cursor artifacts are copyable project-local templates; they are not claimed as
installed native extensions. Grok is documented as a manual fallback until a
native integration can be independently verified. No template may auto-save,
read full histories, call a model, deploy, publish, or change global settings.
