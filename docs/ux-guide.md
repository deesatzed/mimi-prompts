# Terminal UX Guide

MiniPromptLib is intentionally a small-choice navigator. It does not replace a prompt library browser with a long list.

## First use

Run `mini seed` once. If a store is empty, `mini suggest` tells you this command without changing anything automatically.

## Suggestion loop

```bash
mini suggest --interactive --context "Not sure how to proceed after this review"
```

| Input | Meaning | Changes selection frequency? |
| --- | --- | --- |
| `1`, `2`, `3` | Select a displayed prompt. | Yes, once. |
| `m` | Show the next non-repeating small page. | No. |
| `n` | Offer a nested page excluding selected prompts. | No. |
| `p` | Preview selected prompt text together. | No. |
| `c` | Print the selected prompt composition. | No. |
| `r` | Enter revised context and start a new page. | No. |
| `a` | Draft a new mini-prompt and choose whether to save it. | No, unless you later select it. |
| `b` | Remove the latest session selection. | No. |
| `q` | Quit. | No. |

`more` says when there are no additional matching prompts. At that point, retry with more context or capture a thought; the app does not silently repeat a page.

## What gets passed to an agent

The scriptable interface accepts only context you provide:

```bash
mini suggest --json \
  --context "<current user message>" \
  --agent-message "<last agent message>" \
  --build-status "<short build status>"
```

The app does not read a host conversation automatically.
