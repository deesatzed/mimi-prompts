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
| `v N` | View suggestion N's full text without selecting it. | No. |
| `m` | Show the next non-repeating small page. | No. |
| `n` | Offer a nested page excluding selected prompts. | No. |
| `p` | Preview selected prompt text together. | No. |
| `c` | Print the selected prompt composition. | No. |
| `r` | Enter revised context and start a new page. | No. |
| `a` | Draft a new mini-prompt and choose whether to save it. | No, unless you later select it. |
| `b` | Remove the latest session selection. | Yes — undoes the selection count it added. |
| `h` | Show this action list inline. | No. |
| `q` | Quit. Asks once per selection this session whether it helped. | No (feedback is separate from selection count). |

`more` says when there are no additional matching prompts. At that point, retry with more context or capture a thought; the app does not silently repeat a page.

If the classifier lands on `general` and none of the ranked suggestions actually share a word with your context, the app asks a one-keypress clarifying question (`[d]eciding`, `[r]eviewing`, `[s]hipping`, `[x] show anyway`) instead of presenting a confident-looking but essentially arbitrary page. Non-interactively, `mini suggest` prints the equivalent `--state ...` commands, or `--show-anyway` to bypass it.

If revised context you type looks like a reusable rule ("always...", "never...", "make sure..."), the loop nudges you once per session to press `a` and review it as a capture draft. The nudge only ever suggests; it never saves anything on its own.

## Reusable-prompt lifecycle

```bash
mini rm <id>            # delete, with confirmation (--yes to skip it)
mini rename <id> "New Title"
mini edit <id> --text "..." --tags a b --category planning --folder review/async
mini folders            # folder tree with counts
mini list --folder review   # matches "review" and anything nested under it, e.g. review/async
```

## Harvesting reusable prompts from text you paste

```bash
mini harvest --text "Always check for race conditions before approving async PRs."
```

`mini harvest` only ever reads the exact `--file`, `--text`, or stdin content you give it — never conversation history. For each detected instruction-like candidate it shows your original wording next to a generalized rewrite (project names, file paths, versions become placeholders), a recommended folder with its confidence and reason, and a warning if something similar is already saved. Nothing is written until you choose `g`/`o`/`e` and confirm, or explicitly `u`pdate/`v`ariant a near-duplicate; `s` skips. `--json` returns the same candidate drafts and never saves anything, regardless of input.

## Closing the feedback loop

```bash
mini feedback <id> --helped        # or --not-helped
mini stats                         # usage totals plus underperforming prompts
```

`mini stats` surfaces prompts below a success-rate threshold with a `mini improve <id>` hint. The interactive loop also asks once per selected prompt on quit; `skip` (or anything else) records nothing.

## What gets passed to an agent

The scriptable interface accepts only context you provide:

```bash
mini suggest --json \
  --context "<current user message>" \
  --agent-message "<last agent message>" \
  --build-status "<short build status>"
```

The app does not read a host conversation automatically.
