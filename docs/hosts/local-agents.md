# Local, Ollama, and Custom Agents

**Maturity: Verified core.** The local CLI and JSON contract are tested without a model or network connection.

Use the shell interface:

```bash
mini suggest --json --context "<latest user message>" --agent-message "<latest agent message>" --build-status "<short status>"
```

Read the `state` and up to three `suggestions`, render their returned numbering, then call `mini suggest ... --choice <number>` only after an explicit selection.

Pass bounded context only. The core must not auto-save, auto-compose, call an external model, scrape a full conversation, push, deploy, publish, or alter global settings.
