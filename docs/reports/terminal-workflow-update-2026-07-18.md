# Terminal Workflow Update — Verification Transcript

**Date:** 2026-07-18
**Storage:** fresh temporary paths only; the real default prompt library was not accessed.

## Empty-store guidance

```text
$ python3 -m minipromptlib.cli --storage <tmp>/empty.json suggest --context "I am not sure what to do next"
State: undecided
No saved prompts yet. Seed the included panel with: mini seed --panel seeds.md
```

The `<tmp>/empty.json` path did not exist after this command.

## Explicit nesting / preview / compose / back

```text
$ python3 -m minipromptlib.cli --storage <tmp>/prompts.json seed --panel seeds.md
Seeded 34 prompt(s).

$ printf '1\nn\n1\np\nb\nc\nq\n' | python3 -m minipromptlib.cli --storage <tmp>/prompts.json suggest --state checkpoint --interactive
[1-3] use  [m] more  [n] nest  [p] preview  [c] compose  [r] retry  [a] add thought  [b] back  [q] quit:
Selected: seed-06-confirm-we-are-in-sync
...
Selected: seed-09-contrarian-product-review
...
Composition preview:
... both selected prompt texts ...
Backed out of: seed-09-contrarian-product-review
Composed mini-prompt:
... seed-06-confirm-we-are-in-sync prompt text ...
```

Only the two numeric selections incremented `selection_count`; preview, back, and composition made no additional selection mutation.

An independent JSON count check after this sequence reported exactly two nonzero counts, both equal to `1`.

## Exhausted `more`

```text
$ printf 'm\nq\n' | python3 -m minipromptlib.cli --storage <tmp>/prompts.json suggest --state failure --interactive
State: failure | Page 1
1. seed-05-interactive-terminal-guide — matches failure; used 0x
2. seed-25-edge-case-review — matches failure; used 0x
No more matching prompts. Retry with more context or add a thought.
```

The same JSON count check remained exactly two after exhausted `more`.

## Fresh proof surface

```text
python3 -m unittest discover -s tests -v
Ran 44 tests ... OK

python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json
10 tabletop scenarios passed; llm_calls=0

python3 scripts/release_check.py
RELEASE CHECK PASS: package and legacy imports; direct and module CLI; isolated seed and suggestion workflow; fresh target install; installed mini console; saved tabletop evidence

python3 -m py_compile core.py cli.py seeds.py minipromptlib/*.py scripts/*.py tests/*.py
exit 0

git diff --check
exit 0
```
