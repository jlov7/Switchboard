# Contributing Guide

Thanks for your interest in the Switchboard research project! While this isn’t a commercial product, contributions and experiments are welcome.

## Workflow
1. Fork/clone the repo and create a feature branch.
2. Run `make qa` locally before opening a PR (lint, mypy, pytest).
3. Include context: what problem you’re solving, links to research, screenshots if UI-related.
4. Keep PRs focused; large refactors should be discussed via issue first.

## Development Checklist
- [ ] Update or add tests (`pytest`)
- [ ] Update docs (README, relevant files under `docs/`)
- [ ] Add entries to `CHANGELOG` (TODO) if you introduce breaking behavior
- [ ] Run `make audit-verify` if your change touches audit pipeline
- [ ] Mention research framing in commit/PR description (keeps scope clear)

## Communication
- Use GitHub issues/discussions for ideas and roadmap debates.
- Respect the [Code of Conduct](CODE_OF_CONDUCT.md).
- DM/email if you have sensitive security findings before public disclosure.

Happy hacking—and please share what you learn along the way!
