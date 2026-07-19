# Claude Code

**Maturity: Copyable project template.** Claude Code supports project skills; MiniPromptLib provides a local template rather than installing anything automatically.

1. Install MiniPromptLib in the project environment.
2. Copy `integrations/claude/miniprompt-navigator/SKILL.md` to `.claude/skills/miniprompt-navigator/SKILL.md` in that project.
3. Start or reload Claude Code, then use the skill whenever the current workflow moment needs a small choice set.

The shared call is:

```bash
mini suggest --json --context "<latest user message>" --agent-message "<latest agent message>" --build-status "<short status>"
```

The template passes bounded context and renders at most three choices. It must not auto-save, auto-compose, call a model, scrape a full conversation, push, deploy, publish, or alter global settings.
