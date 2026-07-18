# MiniPromptLib `/mini` Reference Command

When invoked, collect bounded context only: the current user message, the immediately previous assistant message, and a short build/test status if one is present. Do not mine the conversation, expose secrets, or send data to an external service.

Call the shared local navigator:

```bash
mini suggest --json --context "<current user message>" --agent-message "<last assistant message>" --build-status "<short status>"
```

Render at most three numbered suggestions from the returned JSON. Explain the compact relevance reason and use count. A numeric reply retrieves that exact suggestion; `more` advances to the next small page; `try again` replaces context; and `capture` previews a user-authored prompt before saving.

This adapter must not auto-save, auto-compose, call an LLM, publish, push, or alter configuration. It is a thin UI over the local `mini` command, not a second ranking implementation.
