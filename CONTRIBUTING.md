# Contributing

Thanks for improving MiniPromptLib.

## Before opening an issue or pull request

- Do not include private prompt stores, full conversation exports, credentials, API keys, personal data, or sensitive build logs.
- Use a small synthetic example and a temporary JSON store when reproducing behavior.
- Keep the local-first boundary intact: no mandatory network, account, model, telemetry, or global host configuration without a separately approved design.
- Preserve the two-to-three-choice workflow UX and the rule that only explicit numeric selection changes `selection_count`.

## Pull requests

Add or update the nearest test, run the verification commands named in the pull-request template, and describe any user-visible wording or integration-contract change. Do not add a host adapter that claims automatic installation or access to full conversation history unless it is independently tested and documented.
