# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MiniPromptLib is a personal, self-improving library for managing "mini-prompts" (reusable
instructional snippets like "act as senior Python reviewer" or "focus on async race conditions")
across different SWE AI tools (Claude Code, Grok Build, local Ollama/Codex agents, etc.).

It is a single-file-module Python library with **zero mandatory dependencies**. All state lives in
one JSON file (default `~/.miniprompts/prompts.json`) — no database, no server.

There is a git repository (initialized after the v1/v2 consolidation below) but no test suite and
no package manifest (`pyproject.toml`/`setup.py`) yet — this is early-stage/prototype code (see
idea1.md for the original design brief).

`core.py`/`cli.py` were previously duplicated as `core.py`/`cli.py` (v1) and `core2.py`/`cli2.py`
(v2, which added `mine_prompts_from_conversation`). These have been consolidated: the v2 files were
promoted to the canonical `core.py`/`cli.py` names (superset of v1's functionality), and the old v1
files and `README2.md` were removed. `README.md` is now the single source of user-facing docs. If
you ever see a `core2.py`/`cli2.py`/`README2.md` reappear, treat it as an in-progress fork, not a
prior duplication that has already been resolved.

## Running It

No install step is required — it's meant to be dropped into `PYTHONPATH` or used in place.

```bash
# Run CLI directly from this directory
python3 cli.py save "Your mini-prompt text" --name my-prompt --tags python review
python3 cli.py list --tags python
python3 cli.py search "async race condition"
python3 cli.py get my-prompt
python3 cli.py mine --file conversation_export.md   # needs Ollama installed

# Or as a package (requires being importable as `minipromptlib`, e.g. one directory up)
python3 -m minipromptlib.cli save "..." --name foo --tags python review
```

There are no lint/test/build commands configured — no `pytest`, `ruff`, or `pyproject.toml` exist
in this repo.

## Architecture

Everything revolves around one class, `MiniPromptLibrary` (defined in `core.py`):

- **Storage**: `self.prompts: Dict[str, Dict[str, Any]]`, loaded from and flushed to a single JSON
  file on every mutation (`_load`/`_save`). No caching layer, no migrations — the JSON file *is*
  the schema.
- **Prompt entry shape**: id, name, prompt_text, description, tags, category, created_at,
  last_used, usage_count, success_count, failure_count, notes, version (see README.md's "Data
  Model" section for the canonical example).
- **CRUD**: `save_mini_prompt` (auto-versions on name collision instead of overwriting, unless
  `overwrite=True`), `get_prompt` (exact ID or fuzzy name match), `list_prompts` (filter by
  tags/category/substring, sorted by usage then recency).
- **Search/selection pipeline** (`keyword_search` → `select_best_for_context` →
  `get_context_injection`): keyword overlap scoring is the cheap first pass; if a
  `chat_completion_fn` is supplied, the candidates are re-ranked by an LLM call that must return a
  JSON array (`[{"id", "why", "score"}, ...]`) — parsed defensively with a regex fallback, and any
  parse failure silently falls back to the keyword-ranked list rather than raising.
- **Improvement** (`improve_prompt`): sends the existing prompt + user instructions to an LLM,
  which must return the improved prompt text as raw output (no JSON). Always creates a **new**
  versioned entry (`{id}_improved_{timestamp}`) rather than mutating the original, so history is
  preserved.
  - `mine_prompts_from_conversation`: same LLM-call-then-parse-JSON pattern, but extracts
    *multiple* new candidate prompts from raw conversation text/export instead of improving one
    existing prompt. Candidates are dicts describing a suggested prompt, not yet saved — the
    caller decides which to `save_mini_prompt(...)`.
- **Feedback loop**: `log_usage()` increments usage/success/failure counters after the fact;
  `get_underperforming_prompts()` surfaces prompts below a success-rate threshold for improvement.
- **LLM wrapper convention**: every LLM-calling method takes a `chat_completion_fn` — a plain
  `Callable[[messages, model, temperature], str]` — rather than hardcoding a provider. Two factory
  helpers exist for wiring one up: `make_ollama_chat_fn()` (local Ollama, needs `pip install
  ollama`) and `make_openai_compatible_chat_fn(client)` (any OpenAI-compatible client, e.g. Grok/
  xAI, Together). All LLM integration is therefore bring-your-own — the library itself has no
  API keys and makes no network calls on its own.
- **All LLM-facing methods degrade gracefully without a `chat_completion_fn`**: e.g.
  `select_best_for_context` falls back to keyword ranking, `improve_prompt` returns the original
  entry annotated with an `improvement_suggestion` string instead of erroring.

## CLI Structure

`cli.py` is a thin `argparse` wrapper around `MiniPromptLibrary` — one subcommand per public
method (`save`, `list`, `get`, `search`, `improve`, `mine`). Note `cmd_improve` in the CLI is a
stub: it does not actually call an LLM (no `chat_completion_fn` is wired up from the command line)
— it just prints the current prompt text and instructions for the user to paste elsewhere. Real
LLM-driven improvement currently requires using the Python API directly. `cmd_mine` is further
along — it wires up `make_ollama_chat_fn` automatically, so it does call a real LLM as long as a
local Ollama instance is running.
