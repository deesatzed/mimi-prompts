# MiniPromptLib

**A local workflow prompt navigator for AI-assisted work.**

MiniPromptLib notices the immediate moment in a build or conversation—uncertainty, a question, a failure, a checkpoint, or completion—and offers up to three reusable mini-prompts. It combines workflow relevance with your explicit selection frequency, without turning your prompt library into a giant menu.

It works offline with Python 3.11+ and no required model, account, or network service.

## Quick start

```bash
git clone https://github.com/deesatzed/mimi-prompts.git
cd mimi-prompts

python3 -m venv .venv
. .venv/bin/activate
python -m pip install .

mini --storage "$PWD/.miniprompts/prompts.json" seed
mini --storage "$PWD/.miniprompts/prompts.json" suggest --interactive \
  --context "Not sure, lets run through scenarios before deciding."
```

The reviewed 41-prompt seed panel is packaged with the installed command. Your prompts are stored locally in the JSON file you choose.

You can also use the default personal-store form: `mini seed`, then `mini suggest --interactive --context "..."`.

## What it feels like

```text
State: undecided | Page 1
1. seed-32-not-sure — matches undecided; used 0x
2. seed-07-alien-goggles-brainstorm — matches undecided; used 0x
3. seed-17-compare-three-solution-levels — matches undecided; used 0x

[1-3] use  [m] more  [n] nest  [p] preview  [c] compose
[r] retry  [a] add thought  [b] back  [q] quit
```

Choose a number to retrieve a prompt. That explicit choice is the only action that increases its `selection_count`.

## Core workflow

| Need | Command or action |
| --- | --- |
| Decide what to do next | `mini suggest --interactive --context "..."` |
| Give an agent structured context | `mini suggest --json --context "..." --agent-message "..." --build-status "..."` |
| Show another small page | `m` / `more` |
| Re-evaluate after a correction | `r` / `retry` |
| Add a second prompt | `n` / `nest` |
| View a suggestion without selecting it | `v N` |
| Inspect selected prompts | `p` / `preview` |
| Print the chosen composition | `c` / `compose` |
| Save a new thought safely | `a` / `add thought`, then confirm |
| Undo the last selection | `b` / `back` (also undoes its selection count) |

The core does not scrape a conversation, call a model, auto-save a prompt, execute prompt text, or change a host application's configuration.

## Library management, harvesting, and feedback

| Need | Command |
| --- | --- |
| Delete / rename / edit a saved prompt | `mini rm <id>`, `mini rename <id> "New Title"`, `mini edit <id> --text "..."` |
| See the folder taxonomy | `mini folders` |
| List prompts in a folder | `mini list --folder review` |
| Pull reusable prompts out of pasted text | `mini harvest --text "Always check for race conditions..."` (never reads history; nothing saves without your consent) |
| Record whether a prompt actually helped | `mini feedback <id> --helped` / `--not-helped` |
| See usage stats and underperforming prompts | `mini stats` |

`mini harvest` only reads the `--file`/`--text`/stdin content you give it, shows you a generalized rewrite next to your original wording, recommends a folder with its confidence, warns about near-duplicates, and saves nothing until you confirm. See the [terminal UX guide](docs/ux-guide.md) for the full walkthrough.

## Install, UX, and host guides

- [Installation and data ownership](docs/install.md)
- [Terminal UX guide](docs/ux-guide.md)
- [Cross-host integration overview](docs/integrations.md)
- [Host guides](docs/hosts/)
- [MIT License](LICENSE)

## One shared integration contract

Every host integration calls the same local command and renders its returned numbering unchanged:

```bash
mini suggest --json \
  --context "<latest user message>" \
  --agent-message "<latest agent message>" \
  --build-status "<short build/test status>"
```

Reference templates are project-local and opt-in. They are not automatic integrations. See [the host guides](docs/hosts/) for what is verified, copyable, or manual-only.

## Privacy and safety

- Local JSON storage, readable and versioned.
- Atomic writes and fail-closed handling for corrupt stores.
- Bounded context only: the caller chooses what current user/agent/build text to pass.
- No hosted account, telemetry, sync, mandatory LLM, or external model call for the workflow loop.
- A suggestion is text for a user or agent to consider—not permission to push, deploy, delete, publish, or change configuration.

## Optional legacy APIs

The Python library keeps compatibility APIs for CRUD, keyword search, optional LLM-assisted improvement, and conversation mining. They are optional and are not required for the workflow navigator or its verification evidence. Start with the CLI workflow above.

## Development verification

```bash
python3 -m unittest discover -s tests -v
python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json
python3 scripts/release_check.py
```

## License

This project is intended for public sharing under the [MIT License](LICENSE). Publication, GitHub Pages activation, and release creation remain deliberate repository-owner actions.
