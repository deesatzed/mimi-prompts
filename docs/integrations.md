# Agent Integrations

MiniPromptLib's core integration contract is local and versioned:

```bash
mini suggest --json --context "The agent asked which UX direction to choose"
```

Adapters may pass only bounded current context: the latest user message, latest agent message, and a short build/test status. They should render at most three returned choices, preserve the returned numbering, and call the same command when a user selects one.

Reference adapter templates live in `integrations/codex/` and `integrations/claude/`. Copy them into an agent-specific configuration only when the user explicitly chooses to install a global integration. The app itself does not scrape conversations, call a model, or alter external configuration.
