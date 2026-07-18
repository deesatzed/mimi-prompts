# MiniPromptLib Workflow Prompt Navigator Design

**Date:** 2026-07-18

**Status:** Approved direction for the next implementation goal

**Product type:** Local-first workflow copilot for reusable AI instructions

## Product Definition

MiniPromptLib should become a quick, context-aware prompt navigator that helps a person choose and reuse the right process guidance while working with an AI agent. It should not behave like a large prompt catalog. It should recognize the current workflow state, show only two or three logically relevant choices, weight those choices with the person's actual selection frequency, and let the person retrieve a choice by number, ask for more, try again, nest another prompt, or save a useful thought with very little friction.

The first user is the repository owner working across Codex, Claude Code, Grok, and local agents. The underlying engine should remain portable enough for other developers, but multi-user and hosted-product concerns must not shape the first release.

## Problem and Job to Be Done

The recurring problem is not merely that prompts are forgotten. During AI-assisted work, the user repeatedly reaches workflow transitions where a familiar instruction would help:

- an AI asks a question and the user wants to reason through it;
- a design section ends and needs review before continuing;
- a task list is claimed complete and needs evidence;
- a build fails and needs a disciplined recovery process;
- a feature is proposed and may be scope drift;
- the user naturally writes a useful instruction worth saving.

At those moments, browsing dozens of stored prompts is slower than rewriting one from memory. The job to be done is therefore:

> When an AI conversation or build reaches a meaningful workflow state, help me retrieve or create the most useful next instruction in seconds, without leaving the flow or scanning a large list.

## Approaches Considered

### 1. Expanded prompt-library CLI

Keep the current CRUD/search interface and improve filtering. This is inexpensive and preserves the current architecture, but it still makes the user remember the library, formulate a query, and browse results. It does not solve choice overload or respond naturally to workflow transitions.

### 2. Standalone local web workbench

Add a graphical library browser, editor, analytics view, and contextual search box. This could eventually make curation pleasant, but it creates a second workspace and adds dependencies before the core habit is validated. It is not the right first surface.

### 3. Workflow Prompt Navigator — selected

Build a small context-and-state engine behind an interactive `mini` command and thin agent-specific adapters. The engine receives a bounded context packet, recognizes the workflow state, ranks prompt candidates using logic plus personal frequency, and drives a progressive two-or-three-choice interaction. This directly addresses the observed need while keeping the implementation local, portable, and testable.

## Core Interaction

The normal interaction is deliberately small:

```text
The AI is asking you to make a design decision.

1. Walk through scenarios before deciding                 used 12x
2. Clarify the user need before choosing a feature        used 8x
3. Compare three solution levels                          used 5x

[1-3] use  [m] more  [r] try again  [a] add thought  [q] quit
```

The commands mean:

- entering a number retrieves that exact mini-prompt and records one explicit selection;
- `more` returns the next small, non-repeating page from the same ranking;
- `try again` accepts revised context and recomputes the ranking;
- `add thought` turns the current user wording into a reviewed draft with a proposed name, tags, and workflow states;
- after selection, `add another` may open a nested recommendation layer; prompts are combined only after an explicit preview and confirmation;
- `back` returns to the prior layer without losing the current session path.

Full-library listing remains available as an administrative command, but it is never the default suggestion experience.

## Workflow-State Model

The engine classifies the immediate situation before it considers subject matter. Version one supports these workflow states:

| Workflow state | Typical evidence | High-value prompt families |
|---|---|---|
| `question` | The latest agent turn asks for clarification or a decision | scenario walkthrough, sync check, user need, options |
| `checkpoint` | A section, phase, or design slice just finished | critique, friction audit, assumption audit |
| `completion` | A task, list, fix, or build is claimed complete | verification, test gaps, handoff, clean-clone proof |
| `failure` | Tests, builds, commands, or tools fail | systematic debugging, edge cases, rescue path |
| `proposal` | A new feature or direction is introduced | necessity, scope drift, job to be done, falsification |
| `undecided` | The user says they are unsure or asks to explore | scenarios/tabletops, alternatives, decision memo |
| `capture` | The user identifies their own wording as reusable | review-and-save flow |
| `general` | No state has adequate evidence | frequent general workflow prompts plus one short context question |

Classification must work offline using explicit state, lightweight deterministic rules, and prompt metadata. An optional LLM may improve classification or reranking, but the main workflow cannot depend on a provider, API key, network connection, or successful JSON generation.

## Logic and Frequency Ranking

Frequency is a first-class personalization signal, but relevance remains the gatekeeper.

1. Generate candidates whose workflow states and text/tags plausibly match the context.
2. Score logical relevance using workflow-state match and deterministic text/tag overlap.
3. Add a bounded frequency boost based on `selection_count`, using a logarithmic or normalized function so early popular prompts do not permanently dominate.
4. Optionally add a small feedback signal when real success/failure history exists.
5. Return at most three results with a short reason and the visible selection count.

The initial scoring policy should be configurable constants near the ranking implementation, with approximately 80–85% of available weight assigned to logical relevance and 15–20% to selection frequency/feedback. Tests, rather than the exact first constants, define the invariant:

- among similarly relevant prompts, the more frequently selected prompt ranks higher;
- a frequently selected but irrelevant prompt cannot outrank a clearly relevant prompt;
- a new highly relevant prompt can appear in the first page;
- repeated `more` pages are stable and contain no duplicates.

An explicit selection increments `selection_count`. Merely displaying a prompt does not. Existing `usage_count`, success, and failure data remain available for outcome tracking and must not be silently conflated with selection frequency.

## Nesting and Composition

Nesting is a session path, not a rigid permanent tree. Once a prompt is selected, the engine uses the original context, selected prompt, and current workflow state to rank possible next-layer prompts. This permits sequences such as:

```text
undecided
└── Walk through scenarios before deciding
    └── First-time-user friction audit
        └── Define success before building
```

Version one should preserve both individual selections and the session path. It must preview the assembled instruction before copying or emitting it. Automatic composition remains off until tabletop tests show that users prefer it.

## Fast Capture

Useful natural language should be easy to retain. For example:

> Not sure. Let's run through scenarios or tabletops and then decide.

The capture flow proposes, but does not silently save:

- a concise name such as `tabletop-scenarios-before-deciding`;
- the cleaned prompt text while preserving the user's intent and voice;
- tags and applicable workflow states;
- optional parent/related prompts;
- a preview with confirm, edit, or cancel.

The authored `seeds.md` remains source material. Seed loading must be deterministic, idempotent, and capable of representing every authored seed plus newly approved workflow prompts without requiring a live LLM.

## Architecture

### Domain engine

The Python core owns persistence, workflow-state classification, deterministic ranking, pagination, selection recording, nesting sessions, capture drafts, and optional LLM extension points. It must remain usable without optional dependencies.

### Storage

The existing human-readable JSON model remains appropriate for the first release. The schema gains versioned, backward-compatible fields such as:

- `workflow_states`;
- `selection_count`;
- `last_selected`;
- optional `related_prompt_ids`;
- schema version information.

Writes must be atomic. Invalid or corrupt storage must produce a visible, actionable error and preserve the original file; the current behavior of silently replacing unreadable state with an empty in-memory library is not acceptable for a personal knowledge asset.

### Application service

A small navigator/session layer converts a context packet into a stable ranked session. A context packet may contain:

- the latest agent message;
- the latest user message;
- an explicit workflow state when supplied by an adapter;
- build/test status text;
- already selected prompt IDs.

Adapters send only the bounded context needed for ranking. They do not scrape entire histories by default.

### User surfaces

The primary surface is an installable `mini` command with interactive and scriptable modes. Scriptable JSON input/output lets Codex, Claude Code, Grok-oriented wrappers, and future integrations call the same engine. Initial repository integrations should be thin instruction/command adapters and documented examples, not separate implementations of ranking logic.

### Packaging

The project should become installable with a standard Python package manifest and console entry point while retaining compatibility for documented direct-script usage during migration. Runtime behavior remains standard-library-only unless a dependency is separately justified.

## Error Handling and Safety

- Empty or inadequate context falls back to a small frequent-workflow menu or one concise request for context.
- Invalid numeric choices preserve the current page and show valid actions.
- Exhausted `more` results say so and offer `try again` or `add thought`.
- Missing related prompts are skipped with a recoverable diagnostic.
- Storage corruption never causes automatic destructive overwrite.
- Optional LLM failures fall back to deterministic behavior and remain observable in diagnostics.
- Context and prompt content remain local by default. Sending content to an external model requires an explicitly configured adapter.
- Imports validate schema and present a dry-run summary before overwriting or merging data.

## Tabletop Acceptance Scenarios

The design is not accepted merely because unit tests pass. A scripted demonstration must cover at least these scenarios:

1. **AI asks a product question:** top choices are process prompts relevant to deciding, not topic-specific clutter.
2. **User is unsure:** `tabletop-scenarios-before-deciding` is available; selecting its number returns it and increments its count once.
3. **AI finishes a section:** checkpoint/review prompts replace question-answer prompts.
4. **AI claims a task list complete:** verification and evidence prompts appear.
5. **Build fails:** debugging/recovery prompts appear even if an unrelated prompt has a much higher frequency.
6. **None are right:** `more` shows a new small page; `try again` accepts updated context.
7. **Nested choice:** the user selects a process prompt, previews a compatible second prompt, and explicitly composes or backs out.
8. **Quick capture:** the user's natural-language thought becomes an editable draft and is saved only after confirmation.
9. **Corrupt storage:** the app explains recovery without erasing the source file.
10. **Offline use:** the complete interaction works without an LLM, credentials, or network.

## Testing Strategy

Use the standard-library `unittest` framework initially to preserve zero mandatory runtime dependencies. Cover:

- schema migration and round-trip persistence;
- atomic writes and corrupt-file preservation;
- workflow-state classification fixtures;
- ranking invariants for logic plus frequency;
- stable pagination and no duplicate suggestions;
- exact selection-count semantics;
- nesting and composition preview;
- idempotent seed loading;
- CLI interaction and machine-readable output;
- optional-LLM failure fallback;
- the ten tabletop scenarios through a deterministic demo/smoke command.

A temporary storage path must be used for every automated test and demo. Verification must never mutate `~/.miniprompts/prompts.json`.

## Delivery Phases

1. Establish packaging, tests, safe storage, and schema migration.
2. Add workflow metadata and deterministic state classification.
3. Add logic-plus-frequency ranking and progressive pagination.
4. Add interactive selection, quick capture, nesting, and composition preview.
5. Convert authored seeds and add the workflow prompts discovered during design.
6. Add scriptable adapter contracts and one thin reference integration.
7. Run tabletop, fresh-install, and compatibility verification; update documentation and handoff truth.

Each phase must leave the repository passing its nearest tests. Later UI or integration work cannot compensate for an unverified core.

## Explicit Non-Goals for This Goal

- hosted service, accounts, teams, or synchronization;
- standalone web or desktop UI;
- vector database or mandatory embeddings;
- automatic scraping of private conversation history;
- automatic external-model calls;
- passive sentiment surveillance or inferred success scoring;
- autonomous prompt rewriting or saving without review;
- broad clinical, HIPAA, or medical-decision logic;
- production deployment.

## Success Definition

The release is successful when a fresh local installation can run the scripted tabletop and interactive workflow entirely offline; every suggestion page contains at most three numbered choices; ranking demonstrably combines workflow logic and explicit selection frequency; the user can retrieve, page, retry, nest, and safely capture prompts; persistence is backward compatible and corruption safe; and the full automated verification suite passes without touching the user's real prompt library.
