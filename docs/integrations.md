# Agent Integrations

MiniPromptLib's core integration contract is local and versioned:

```bash
mini suggest --json --context "The agent asked which UX direction to choose"
```

Adapters may pass only bounded current context: the latest user message, latest agent message, and a short build/test status. They should render at most three returned choices, preserve the returned numbering, and call the same command when a user selects one.

Every adapter must pass only bounded current context: the latest user message, latest agent message, and a short build/test status. It must render at most three returned choices, preserve numbering, and call the same command when a user selects one.

## Maturity labels

- **Verified core:** the local CLI and JSON output are covered by the release check.
- **Copyable project template:** a repository file you may copy into a host project. It is not installed automatically and is not a live native plugin claim.
- **Manual fallback:** a documented CLI workflow when no tested host extension path exists.

Choose a host guide:

- [Codex](hosts/codex.md)
- [Claude Code](hosts/claude-code.md)
- [Cursor](hosts/cursor.md)
- [Local/Ollama/custom agents](hosts/local-agents.md)
- [Grok](hosts/grok.md)

Reference templates live in `integrations/`. They never auto-save, auto-compose, call an external model, publish, push, deploy, scrape a full conversation, or alter global configuration.
