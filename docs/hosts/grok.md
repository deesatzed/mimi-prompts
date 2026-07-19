# Grok

**Maturity: Manual fallback.** No native MiniPromptLib extension path is claimed here.

Run the local CLI beside a Grok session and pass only the context you choose:

```bash
mini suggest --json --context "<latest user message>" --agent-message "<latest agent message>" --build-status "<short status>"
```

Paste or select from the returned small set manually. The workflow remains useful without a native integration because the core is local and deterministic.

Use bounded context only. This manual fallback must not auto-save, auto-compose, call an external model, scrape a full conversation, push, deploy, publish, or alter global settings.
