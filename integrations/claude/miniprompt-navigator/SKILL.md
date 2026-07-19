---
name: miniprompt-navigator
description: Offer up to three workflow-aware local mini-prompts during an AI task.
---

# MiniPrompt Navigator

**Maturity: Copyable project template.** Copy this file into a project only when the user chooses to make the local `mini` command available there.

Pass only bounded context: the latest user message, latest assistant message, and a short build/test status. Do not read or transmit a full conversation, credentials, or unrelated files.

```bash
mini suggest --json --context "<latest user message>" --agent-message "<latest agent message>" --build-status "<short status>"
```

Render at most three returned choices and preserve their numbering. On a numeric user choice, call the same command with `--choice <number>` and return that prompt text. Offer `more`, `try again`, or reviewed capture when no choice fits.

This adapter must not auto-save, auto-compose, call a model, push, deploy, publish, or alter global settings. It is a thin local UI, not a second ranking implementation.
