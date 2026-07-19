# Install MiniPromptLib

## Requirements

- Python 3.11 or newer
- A local clone of this repository

No API key, model, hosted account, or network connection is needed after installation.

## Recommended project-local install

```bash
git clone https://github.com/deesatzed/mimi-prompts.git
cd mimi-prompts
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
```

Use a project-local store when you want the prompt library to stay with that project:

```bash
mini --storage "$PWD/.miniprompts/prompts.json" seed
mini --storage "$PWD/.miniprompts/prompts.json" suggest --interactive \
  --context "The test suite failed with a traceback"
```

The first command adds the packaged 34-prompt reviewed panel. It is idempotent: running it again does not overwrite the authored prompts.

## Personal store

Omit `--storage` to use `~/.miniprompts/prompts.json`:

```bash
mini seed
mini suggest --context "The agent asked which design direction to choose"
```

Keep this file private. It may contain your reusable instructions and selection history.

## Upgrade from a clone

```bash
cd mimi-prompts
git pull
. .venv/bin/activate
python -m pip install .
```

Back up your personal JSON store before any manual edits. The application preserves legacy JSON reads and stops rather than overwriting unreadable or invalid data.

## Uninstall

From the same activated environment:

```bash
python -m pip uninstall minipromptlib
```

Uninstalling the package does not delete your local JSON store. Remove a store only after making your own backup decision.
