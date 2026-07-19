# Codex

**Maturity: Copyable project template.** The local command and JSON interface are verified; this host file is a template, not an automatic installation.

1. Install MiniPromptLib in the project environment.
2. Copy `integrations/codex/miniprompt-navigator/SKILL.md` into the Codex project skill location you control.
3. Start a new Codex session and invoke the workflow when a decision, failure, checkpoint, completion, or capture moment appears.

The template calls:

```bash
mini suggest --json --context "<latest user message>" --agent-message "<latest agent message>" --build-status "<short status>"
```

Only bounded context is supplied. The template must not auto-save, auto-compose, read a whole conversation, call a model, push, deploy, publish, or change global settings.
