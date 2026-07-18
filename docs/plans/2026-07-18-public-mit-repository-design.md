# Public MIT Repository and Cross-Host Distribution Design

## Purpose

Turn this checkout into the canonical public source for `https://github.com/deesatzed/mimi-prompts`, with a GitHub Pages landing page and a truthful, portable path for installing and using the local-first Workflow Prompt Navigator across AI coding hosts.

## Product boundary

The public product is still a local Python CLI and reusable engine. The website explains and distributes it; it is not a hosted prompt service. It does not add accounts, cloud synchronization, automatic chat scraping, telemetry, a required model, or automatic global agent configuration.

## Repository architecture

```text
mimi-prompts/
├── minipromptlib/                 # installable local engine
├── README.md                      # concise public quickstart
├── LICENSE                         # MIT
├── site/                           # static Pages source
├── docs/
│   ├── install.md                  # supported install/uninstall/upgrade paths
│   ├── ux-guide.md                 # terminal workflow and examples
│   └── hosts/                      # host-specific, truth-labeled guides
├── integrations/                   # copyable project-local templates
└── .github/workflows/
    ├── verify.yml                  # test and packaging evidence
    └── pages.yml                   # static site deployment
```

The package root remains the source of truth. `site/` is static HTML/CSS/JS with no build dependency so GitHub Pages can deploy it reproducibly. Documentation and landing copy must point to one command contract, never duplicate ranking logic:

```bash
mini suggest --json --context "<latest user message>" \
  --agent-message "<latest agent message>" \
  --build-status "<short status>"
```

## Installation and seed portability

The public install path is a virtual environment plus `python -m pip install .` from a clone. The package must expose a supported way to locate/load the reviewed 34-prompt seed panel after installation; public docs must not imply that `seeds.md` exists in an arbitrary working directory if it has not been packaged there.

The first-use path is deliberately short:

1. Create or activate a Python 3.11+ virtual environment.
2. Install the local clone.
3. Seed a chosen local JSON store from the reviewed panel.
4. Run `mini suggest --interactive` with a bounded context.

## Cross-host model

| Host | Public deliverable | Truth boundary |
| --- | --- | --- |
| Codex | Copyable project skill/template and guide. | No global installation or automatic conversation access. |
| Claude Code | Copyable `.claude/skills/<name>/SKILL.md` template and guide. | Project-local skill is documented; user chooses installation. |
| Cursor | Rules/agent guide that invokes the JSON contract. | No claim of a tested native plugin until one is tested. |
| Local/Ollama/custom agents | Shell and Python JSON examples. | No model needed for navigator behavior. |
| Grok | Manual/CLI bounded-context workflow guide. | No claim of a native extension point unless independently verified. |

Every guide distinguishes **verified**, **copyable template**, and **manual fallback**. All pass only bounded context and preserve the two-to-three-choice UI.

## Landing-page content

The landing page should answer, in this order:

1. What it is: a local workflow prompt navigator, not a giant prompt catalog.
2. Why it helps: recognize the immediate workflow moment, show up to three choices, use relevance plus explicit frequency.
3. How it feels: an interactive terminal transcript for uncertainty and a failed build.
4. How to install and seed it.
5. How integrations work: one shared JSON command plus host cards labeled by maturity.
6. Safety and privacy: offline core, no scraping, no auto-save, no external account.
7. Links: GitHub source, MIT license, guides, and verification evidence.

## GitHub readiness

Before public push, add MIT license text, issue/PR community templates only if they can be maintained, a verification workflow that runs the existing proof surface, and a Pages workflow that deploys only `site/`. The repository description/homepage, default branch, and Pages settings require GitHub-side changes and are intentionally not assumed or mutated by the local build.

## Acceptance evidence

- README quickstart commands work from a clean clone/virtual environment.
- Installed package can seed without relying on a source-relative working directory.
- Each host guide corresponds to an adapter/template or an explicitly labeled manual fallback.
- Static landing page has no broken internal links and renders locally.
- CI workflow syntax is valid and invokes the existing full proof surface.
- `LICENSE` is the standard MIT license.
- Existing 44-test suite, tabletop, package release check, compile check, and diff check remain green.

## Explicit non-goals

- Publishing a package to PyPI.
- Pushing to GitHub, enabling Pages, changing repository settings, or creating releases without explicit user authorization in a later step.
- Building a hosted web application or automatic native integration for every host.
