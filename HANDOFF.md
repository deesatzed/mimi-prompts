# MiniPromptLib — Agent Handoff Document

**Project:** MiniPromptLib  
**Owner:** Wayne A. Satz, MD (O2Satz)  
**Date:** July 18, 2026  
**Status:** v1 complete + mining feature added  
**Purpose of this document:** Give any SWE AI agent (Grok Build, Claude Code, local Codex/Ollama agent, CAM-PULSE, etc.) full context so it can understand, extend, integrate, or improve this library without losing intent.

---

## 1. Project Mission

MiniPromptLib turns the repetitive mini-prompts that software engineering AI agents (and their human users) use constantly into a **persistent, searchable, versioned, and self-improving personal asset**.

**Core problem it solves:**
- Users repeatedly paste the same 4–10 short instructions ("act as senior Python reviewer...", "focus on async + race conditions...", "HIPAA-aware clinical data handling...", etc.).
- These instructions evolve in the user's head but are never captured systematically.
- Different AI tools (Grok, Claude, Codex, CAM-PULSE) have no shared memory of what works well for *this specific user*.

**Goal:** A lightweight library that any coding agent can use as a tool/skill so that:
1. Mini-prompts are saved with rich metadata.
2. They can be quickly retrieved and chosen.
3. The underlying LLM can improve/generalize them.
4. The agent can intelligently select the best ones for the current task/context.
5. Prior conversations can be mined to rapidly bootstrap the library.

This creates a **living, personalized prompt knowledge base** that gets better the more it is used.

---

## 2. Current Status (July 18, 2026)

**Fully implemented:**
- Core `MiniPromptLibrary` class with JSON persistence (`~/.miniprompts/prompts.json`)
- CRUD + rich metadata (tags, category, usage stats, success/failure tracking, notes, versioning)
- `save_mini_prompt()`, `get_prompt()`, `list_prompts()`, `keyword_search()`
- `select_best_for_context()` — hybrid keyword + LLM reranking with explanations
- `get_context_injection()` — returns ready-to-prepend string for agent system prompts
- `improve_prompt()` — LLM-powered improvement that creates a new versioned copy
- `log_usage()` + success tracking for self-improvement signals
- `mine_prompts_from_conversation()` — NEW: LLM-powered extraction of reusable mini-prompts from prior chat history
- Full CLI (`python -m minipromptlib.cli`) with `save`, `list`, `get`, `search`, `improve`, `mine`
- Zero mandatory dependencies (optional Ollama/OpenAI-compatible wrappers provided)
- Comprehensive README + this handoff doc

**Storage:** Single human-readable JSON file. Easy to git, backup, rsync, or edit manually.

**Tested:** Basic smoke tests pass. The library is ready for real use and integration.

---

## 3. Core Requirements (What Any Extension Must Preserve)

1. **Save** — Easy to capture a mini-prompt with name, tags, category, description.
2. **Retrieve & Browse** — Fast listing, searching, and getting full text (CLI + Python).
3. **Improve / Generalize** — The LLM can rewrite a prompt to be more robust, general, or specialized, creating a new version.
4. **Contextual Selection** — Given a task description + optional context, return the most relevant mini-prompt(s) with reasoning. Support injection into agent context.
5. **Conversation Mining** — Given prior chat history (text or message list), extract high-value reusable mini-prompt candidates with suggested metadata.
6. **Self-Improvement Loop** — Track usage + success/failure so the system (and future agents) can identify weak prompts and improve them over time.
7. **LLM Agnostic** — Must work with any backend via a simple `chat_completion_fn` callable. Never hardcode a specific provider.

---

## 4. Architecture & Key Design Decisions

**Storage Strategy**
- Single `prompts.json` file (deliberately simple).
- Each entry contains: `id`, `name`, `prompt_text`, `description`, `tags`, `category`, `created_at`, `last_used`, `usage_count`, `success_count`, `failure_count`, `notes`, `version`.
- Why: Trivial to inspect, version with git, sync across machines, and recover from corruption. No database dependency for v1.

**Selection Strategy (Requirement 4)**
- Two-stage: Fast keyword pre-filter → LLM reranking (when `chat_completion_fn` is provided).
- Returns enriched candidates with `relevance_reason` and `relevance_score`.
- `get_context_injection()` produces a clean block ready to prepend to any system prompt.

**Improvement Strategy (Requirement 3)**
- `improve_prompt()` never mutates the original in place.
- It creates a new versioned entry (`_improved_YYYYMMDD_HHMM`) with the improved text.
- Preserves usage history on the parent.

**Conversation Mining (New Requirement)**
- Accepts raw text or structured message list.
- LLM is prompted as a "prompt archaeologist" to find repeated/high-signal instructional blocks.
- Outputs structured candidates with `suggested_name`, `suggested_prompt_text`, `suggested_tags`, `suggested_category`, `why_recommended`, `original_snippet`.
- Post-processing deduplicates and filters by length.

**Self-Improvement Data**
- Every prompt accumulates `usage_count`, `success_count`, `failure_count`.
- `log_usage(prompt_id, success=bool, notes=...)` is the hook for agents to feed back outcomes.
- `get_underperforming_prompts()` helper exists for future automation.

**LLM Integration Pattern**
- All intelligent features require the caller to pass a `chat_completion_fn(messages, model=..., temperature=...) -> str`.
- Helper factories provided: `make_ollama_chat_fn()` and `make_openai_compatible_chat_fn(client)`.
- This keeps the core library completely backend-agnostic.

**Philosophy**
- Mini-prompts are first-class assets, not throwaway text.
- The library + the LLM collaborate on curation.
- Keep the core extremely lightweight so it can be dropped into any agentic workflow (including resource-constrained local setups).

---

## 5. Codebase Layout

```
/home/workdir/artifacts/minipromptlib/
├── __init__.py          # Public exports
├── core.py              # Main MiniPromptLibrary class + all logic + helper factories
├── cli.py               # Command-line interface (save, list, get, search, improve, mine)
├── README.md            # User-facing documentation + examples
└── HANDOFF.md           # This document (for AI agents)
```

**Key classes/methods to understand first:**
- `MiniPromptLibrary` (core.py) — the single source of truth.
- `mine_prompts_from_conversation()` — newest and most powerful for bootstrapping.
- `select_best_for_context()` + `get_context_injection()` — the heart of agent integration.
- `improve_prompt()` — the self-improvement engine.

---

## 6. How to Use (Quick Reference)

**Python (recommended for agents):**
```python
from minipromptlib import MiniPromptLibrary, make_ollama_chat_fn

lib = MiniPromptLibrary(storage_path="~/.miniprompts/prompts.json")
chat_fn = make_ollama_chat_fn(default_model="qwen2.5-coder:32b")

# Save, improve, select, mine, log usage...
```

**CLI (for human + quick ops):**
```bash
python -m minipromptlib.cli save "..." --name foo --tags python review
python -m minipromptlib.cli mine --file conversation.md
python -m minipromptlib.cli list --tags python
```

Full examples live in `README.md`.

---

## 7. Integration Guidance for Different SWE AI Tools

**Local Ollama / LM Studio / Custom Codex-style Agent**
- Import `MiniPromptLibrary`.
- Before main LLM call: `injection = lib.get_context_injection(task, chat_completion_fn=...)`
- Prepend `injection` to system prompt.
- After task: `lib.log_usage(used_id, success=build_passed, notes=...)`

**Grok Build / xAI sessions**
- Keep the library on disk.
- In long sessions, ask Grok to use `mine_prompts_from_conversation` on recent context or call `improve_prompt` on specific IDs.
- Or run Python snippets in a parallel terminal.

**Claude Code / Projects / Artifacts**
- Upload `prompts.json` as project knowledge.
- Or paste `get_context_injection()` output at the start of a chat.
- Use Artifacts to maintain an evolving "Prompt Curator" that calls the improve/mining logic.

**CAM-PULSE (your self-improving Grok-powered coder)**
- Expose `MiniPromptLibrary` methods as tools.
- Before a build: call `select_best_for_context` or `get_context_injection`.
- After successful/failed build: call `log_usage(...)`.
- Periodically: run `get_underperforming_prompts()` and auto-improve.
- This creates a powerful meta self-improvement loop on top of CAM-PULSE's existing scoring.

---

## 8. Known Limitations & Technical Debt (Be Honest With Future Agents)

- No vector embeddings yet (keyword + LLM rerank works well for small libraries < 200 prompts).
- No built-in web UI or multi-user support (single-user local focus).
- Mining quality depends heavily on the quality of the `chat_completion_fn` model.
- CLI `improve` command is currently a helper that prints instructions (full auto-improve requires Python API).
- No automatic variable substitution (`{language}`, `{framework}`) yet.
- Success/failure tracking is manual — agents must remember to call `log_usage()`.
- No git-like diff view for prompt versions (yet).

**Do not over-engineer v2 without clear user request.** Keep the "lightweight and immediately useful" spirit.

---

## 9. Recommended Next Steps / Roadmap (Prioritized)

**High value / low effort:**
1. Pre-seed the library with 10–15 excellent starter prompts (Python review, async, FastAPI, HIPAA/clinical data, testing, security, error handling, etc.).
2. Add a small set of high-quality seed prompts directly in `core.py` or a `seeds.py` module.
3. Improve the mining prompt (make it even better at detecting repeated patterns).
4. Add `bulk_save_candidates(candidates, auto_improve=False)` helper.

**Medium effort:**
5. True semantic search using embeddings (Ollama `nomic-embed-text` or `sentence-transformers`).
6. Variable substitution support in prompts.
7. `optimize_library()` method that reviews underperforming prompts and proposes improvements.
8. Tiny FastAPI wrapper so remote agents (or CAM-PULSE running elsewhere) can call the library over HTTP.

**Longer term (only if user asks):**
- Git-backed versioning with proper diffs.
- Team/shared library mode.
- Web UI (Streamlit or similar) for browsing/improving prompts.
- Integration as a native skill inside this Grok instance.

---

## 10. Development Guidelines (For Any Agent Working on This Code)

- **Keep it lightweight.** Resist adding heavy dependencies unless the user explicitly wants a feature that requires them.
- **Preserve LLM agnosticism.** Never hardcode a provider.
- **Every intelligent feature must support being called without an LLM** (graceful fallback or clear error).
- **Write clear docstrings.** Future agents (and the user) will read them.
- **Update this HANDOFF.md and README.md** when making significant changes.
- **Test changes** with the existing smoke-test pattern in `core.py`.
- **Respect the self-improvement data model** — usage/success tracking is sacred for long-term value.
- **Healthcare / clinical context:** Many of the user's prompts involve medical data, privacy (HIPAA), clinical logic, and precision medicine. When improving or mining, be sensitive to these domains.
- **User context:** The owner is a busy emergency physician transitioning to health IT/AI, sole caretaker for aging parent (recent loss), building DNAsedLongevity.com and CAM-PULSE. Respect his time — deliver high-signal, low-friction changes.

---

## 11. Quick Start for You (The Receiving Agent)

If you are Grok Build, Claude Code, a local Codex agent, or CAM-PULSE receiving this handoff:

1. Read this entire `HANDOFF.md` + the `README.md`.
2. Explore the code in `core.py` (start with `__init__`, `save_mini_prompt`, `select_best_for_context`, `mine_prompts_from_conversation`, and `improve_prompt`).
3. Run the CLI smoke test:
   ```bash
   python -m minipromptlib.cli list
   python -m minipromptlib.cli save "You are a senior reviewer..." --name test-review --tags review python
   ```
4. Ask the user (Wayne) what he wants to do next:
   - Seed the library with good starter prompts?
   - Mine a specific conversation?
   - Integrate into CAM-PULSE?
   - Add embeddings / semantic search?
   - Something else?

You now have full context. You can pick up development, answer questions about the design, propose improvements, or implement new features while staying true to the original intent.

---

**This library is meant to be a long-term companion that gets smarter alongside Wayne's AI work across every tool he uses.**

If anything in this handoff is unclear, or if you need clarification on requirements before coding, ask the user directly. Do not guess on core behavior.

Welcome to the project. Let's make his prompt workflow dramatically better.

---

## Current Workflow Navigator Update — 2026-07-18

The current implementation is an offline workflow prompt navigator rather than only a CRUD library. The primary command is `mini suggest --context "..."`. It classifies workflow state, returns at most three choices, supports a numbered selection and small-page retry, and uses bounded `selection_count` frequency only after logical relevance.

`seeds.md` now contains 34 authored prompts and the seed loader preserves each prompt's text with workflow metadata. The core flow does not require an LLM and does not scrape history, auto-save drafts, auto-compose prompts, push, publish, or alter global configuration.

Verification is maintained by `python3 -m unittest discover -s tests -v`, `python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json`, and `python3 scripts/release_check.py`.
