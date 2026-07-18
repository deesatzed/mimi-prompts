---
name: miniprompt-navigator
description: Offer a small, workflow-aware set of reusable mini-prompts during an AI task.
---

# MiniPrompt Navigator

Use this adapter when the user asks for help deciding, reviewing a checkpoint, recovering from a failure, confirming completion, or saving a useful instruction.

Pass only bounded context: the latest user message, the latest assistant message, and an optional short build-status summary. Do not read or transmit full conversation history, credentials, or unrelated files.

Run the shared local contract:

```bash
mini suggest --json --context "<latest user message>" --agent-message "<latest agent message>" --build-status "<optional short status>"
```

Present at most three returned choices, numbered exactly as returned. Include each short reason and visible selection count. If the user chooses a number, run `mini suggest` again with `--choice <number>` using the same bounded context and return the selected prompt verbatim.

If no choice fits, offer the user `more`, `try again` with a revised context, or `capture` a new thought. The adapter must not auto-save, auto-compose, push, deploy, call an external model, or change global settings.
