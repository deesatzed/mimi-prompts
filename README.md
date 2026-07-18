# MiniPromptLib — Personal Mini-Prompt Management for SWE AI Agents

**Goal**: Give your AI coding tools (Grok Build, Claude Code / Artifacts, local Codex/Ollama agents, CAM-PULSE, etc.) a persistent, searchable, self-improving library of the mini-prompts you use every day.

You repeatedly type similar short instructions. This library lets you:
1. **Save** them once with rich metadata.
2. **Retrieve** them instantly (CLI, Python, or semantic/LLM-powered search).
3. **Improve / Generalize** them automatically using the underlying LLM.
4. **Contextually select** the best ones for the current task — so the agent itself decides which mini-prompts are relevant.

## Why This Exists

Most SWE AI sessions start with you pasting the same 3–8 mini-prompts ("act as senior Python reviewer", "focus on async correctness and race conditions", "write comprehensive tests", "consider clinical data privacy...").

Over time you refine them mentally. This system makes that refinement **explicit, versioned, and automatic**.

## Core Features

| Requirement | How MiniPromptLib Delivers |
|-------------|---------------------------|
| 1. Save current mini-prompt | `save_mini_prompt(...)` + CLI `minipromptlib save "..." --name foo --tags python review` |
| 2. Quickly retrieve / choose one | CLI `list`, `get`, `search` + Python `list_prompts()`, `keyword_search()` |
| 3. LLM improves / generalizes | `improve_prompt(prompt_id, instructions=..., chat_completion_fn=your_llm)` — creates a new versioned copy |
| 4. Auto-choose best for context | `select_best_for_context(task_description, chat_completion_fn=...)` + `get_context_injection(...)` — returns ranked + reasoned list ready to inject |
| **NEW: Mine prior conversations** | `mine_prompts_from_conversation(conversation_text_or_messages, chat_completion_fn)` + CLI `minipromptlib mine --file export.md` — LLM extracts repeated/reusable mini-prompts from your chat history so you can bulk-populate the library |

## Quick Start (Python)

```python
from minipromptlib import MiniPromptLibrary, make_ollama_chat_fn

lib = MiniPromptLibrary()   # stored in ~/.miniprompts/prompts.json

# 1. Save
lib.save_mini_prompt(
    prompt_text="""You are a senior Python engineer with deep expertise in async code, 
type hints, and production-grade error handling. Review the following code for 
correctness, performance, race conditions, and maintainability. Be concise but thorough.""",
    name="python-async-review",
    tags=["python", "review", "async", "production"],
    category="code-review",
    description="Strong default reviewer prompt for Python services"
)

# 2. Retrieve
print(lib.get_prompt("python-async-review")["prompt_text"])

# 3. Improve (requires LLM wrapper)
ollama_chat = make_ollama_chat_fn(default_model="qwen2.5-coder:32b")  # or your model
improved = lib.improve_prompt(
    "python-async-review",
    instructions="Make it more general so it also works well for FastAPI + SQLAlchemy codebases. Add emphasis on Pydantic v2 and dependency injection patterns.",
    chat_completion_fn=ollama_chat,
    auto_save=True
)
print("New improved version saved as:", improved["id"])

# 4. Let the agent choose the best prompts for a task
task = "Debug why this Celery task is sometimes processing the same message twice under high load"

best_prompts = lib.select_best_for_context(
    task_description=task,
    context="We use Redis as broker, FastAPI background tasks also involved",
    top_k=3,
    chat_completion_fn=ollama_chat
)

for p in best_prompts:
    print(p["id"], p.get("relevance_score"), p.get("relevance_reason"))

# Even better: get a ready-to-paste context block
injection = lib.get_context_injection(task, chat_completion_fn=ollama_chat, top_k=2)
print(injection)
# Then add `injection` to your agent's system prompt or messages
```

## NEW: Mine Prior Conversations to Rapidly Populate the Library

This directly addresses your request. Instead of manually hunting through old chats for the mini-prompts you keep reusing, let the LLM do the archaeology for you.

```python
from minipromptlib import MiniPromptLibrary, make_ollama_chat_fn

lib = MiniPromptLibrary()
ollama_chat = make_ollama_chat_fn(default_model="qwen2.5-coder:32b")

# Paste conversation text, or load from a Claude/Grok export file
with open("old_claude_chat.md") as f:
    history = f.read()

candidates = lib.mine_prompts_from_conversation(
    history,
    chat_completion_fn=ollama_chat,
    max_candidates=10
)

for c in candidates:
    print(f"→ {c['suggested_name']}")
    print(f"   Why: {c['why_recommended']}")
    print(f"   Tags: {c['suggested_tags']}")
    print()

# Review, then save the good ones:
# lib.save_mini_prompt(c['suggested_prompt_text'], name=c['suggested_name'], tags=c['suggested_tags'], ...)
```

**CLI version** (very convenient):
```bash
python -m minipromptlib.cli mine --file ~/Downloads/claude_export_2026-07-10.md --model qwen2.5-coder:32b
# or pipe text
cat conversation.txt | python -m minipromptlib.cli mine
```

The miner is tuned to find **repeated or high-signal instructional blocks** (role definitions, review rubrics, domain rules like HIPAA/async/security, checklists, etc.) while ignoring one-off chatter. It proposes cleaned canonical versions + metadata.

This turns weeks/months of conversation history into a high-quality seed for your personal prompt library in minutes.

## CLI (Fastest for Daily Use)

```bash
# Save while you're in the flow
python -m minipromptlib.cli save \
  "Focus on clinical data handling, HIPAA considerations, and clear audit logging. Never log PHI." \
  --name hipaa-aware-review \
  --tags python healthcare privacy review \
  --category code-review

# Browse what you have
python -m minipromptlib.cli list --tags python review
python -m minipromptlib.cli search "async race condition"
python -m minipromptlib.cli get python-async-review
```

## Integration Patterns (for different SWE AI apps)

### 1. Local Ollama / LM Studio / Custom Codex-style Agent

In your agent loop (before the main LLM call):

```python
injection = lib.get_context_injection(
    user_request,
    chat_completion_fn=your_ollama_fn,
    top_k=3
)
full_system = base_system_prompt + "\n\n" + injection
# then call your model with full_system + user_request
```

After the task completes (success or failure), call:
```python
lib.log_usage(used_prompt_id, success=True/False, notes="Helped catch a subtle race condition")
```

### 2. Grok Build / xAI coding sessions

- Keep `~/.miniprompts/prompts.json` in your repo or home.
- In long sessions, periodically ask me (Grok): "Using your MiniPromptLib, save the following as ... " or "Improve the prompt we just used for X".
- Or run the Python snippets above in a notebook / terminal alongside the chat.

### 3. Claude Code / Claude Projects / Artifacts

Claude has excellent long context and Projects. You can:
- Upload the `prompts.json` as a knowledge file in a Project.
- Or paste the output of `get_context_injection(...)` at the start of a new chat.
- Use Claude's Artifacts to maintain an evolving "Prompt Curator" artifact that calls the improve logic.

### 4. CAM-PULSE (your self-improving Grok-powered coder)

This library is a natural fit. You can:
- Give CAM-PULSE the `MiniPromptLibrary` as a tool.
- Let it call `select_best_for_context` before starting a build.
- After successful builds, have it call `log_usage(..., success=True)`.
- Periodically run `lib.get_underperforming_prompts()` and auto-improve the weak ones.
- This creates a **meta self-improvement loop** on top of CAM-PULSE's existing build-success scoring.

## Advanced / Future Ideas (you can extend)

- Add vector embeddings (Chroma / FAISS + nomic-embed-text via Ollama) for true semantic search.
- Prompt versioning with git-like diff view.
- "Prompt of the week" auto-suggestion based on recent task patterns.
- Multi-user / shared team library (sync via git or simple server).
- Variable substitution: prompts containing `{language}`, `{framework}` get filled at selection time.
- Success-rate weighted selection (prompts that worked well for you before get boosted).

## Data Model (one entry)

```json
{
  "id": "python-async-review",
  "name": "python-async-review",
  "prompt_text": "...",
  "description": "...",
  "tags": ["python", "review", "async"],
  "category": "code-review",
  "created_at": "2026-07-18T...",
  "last_used": "...",
  "usage_count": 47,
  "success_count": 41,
  "failure_count": 3,
  "notes": ["Worked great on the Celery duplicate task bug"],
  "version": 3
}
```

## Installation / Portability

Just copy the `minipromptlib/` folder into your project or `~/.local/lib/python...` or put it on your `PYTHONPATH`.

It has **zero mandatory dependencies**. The LLM wrappers are optional helpers.

The JSON file `~/.miniprompts/prompts.json` is the only state — trivial to backup, version with git, or rsync between machines (Mac Mini ↔ other devices).

## Recommended Seed Prompts (add these first)

Common high-value ones for a healthcare + Python + AI engineer:

- `python-senior-review`
- `async-race-condition-hunter`
- `fastapi-production-patterns`
- `hipaa-pii-redaction-review`
- `test-driven-refactor`
- `sqlalchemy-query-optimizer`
- `error-handling-resilience`
- `docstring-and-type-hint-enforcer`
- `security-audit-prompt`

You can seed them via the Python API or by editing the JSON directly.

---

**This library turns your repeated mini-prompts from ephemeral chat text into a living, improving knowledge base that gets smarter the more you (and your agents) use it.**

Built for you, Wayne — to accelerate all your SWE AI work across every tool you use.

If you want me to:
- Add embedding-based semantic search
- Create a FastAPI wrapper so remote agents can call it
- Pre-seed 10–15 excellent starter prompts
- Integrate it directly into a CAM-PULSE tool definition
- Generate a one-file "drop-in" version

...just say the word and we'll iterate.

## Current Workflow Navigator Release

MiniPromptLib is now an offline workflow prompt navigator. Start with the authored 34-prompt panel in a temporary or personal store:

```bash
python3 seeds.py --storage /tmp/prompts.json
mini suggest --context "Not sure, lets run through scenarios before deciding."
```

The default experience shows at most three numbered suggestions. Enter a number with `--choice`, use `--offset 3` for the next small page, or supply revised context to try again. A selected prompt increments `selection_count`; merely showing or previewing one does not.

The core workflow runs offline with no API key, model, network call, or required dependency beyond Python. It does not scrape conversations, auto-save prompts, auto-compose selections, push code, or change global agent configuration. The 34 authored prompts in `seeds.md` are loaded deterministically and preserve their text.
