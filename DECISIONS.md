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
