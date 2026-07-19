# Cursor

**Maturity: Copyable project template.** This is a project rule/template, not a claim of a tested native MiniPromptLib plugin.

1. Install MiniPromptLib in the project environment.
2. Copy `integrations/cursor/miniprompt-navigator.mdc` into the project rule location you control.
3. Use it only in workflows where the agent can run the local CLI.

The rule calls:

```bash
mini suggest --json --context "<latest user message>" --agent-message "<latest agent message>" --build-status "<short status>"
```

It passes bounded context and renders at most three choices. It must not auto-save, auto-compose, call an external model, read a full conversation, push, deploy, publish, or alter global settings.
