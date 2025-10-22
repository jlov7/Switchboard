# Switchboard Research Refresh Plan — Iteration 2

## Objectives
1. **Resilience & Chaos** – simulate connector failures, OPA outages, and policy edge cases to guarantee graceful degradation.
2. **Confidence Tooling** – add contract tests, coverage gates, and mutation testing to drive towards zero bugs.
3. **Contributor UX** – provide quickstart scripts, template issues, and Backstage-compatible metadata for easier onboarding.
4. **Growth & Storytelling** – new media assets, release notes, and learning labs to evangelize the project as a passion-driven research effort.

## Key Deliverables
- Chaos scripts (`scripts/chaos/`) targeting policy engine, adapters, and approvals store.
- Coverage + mutation testing pipeline (pytest --cov, mutmut, coverage badges).
- Contributor onboarding kit (quickstart script, issue templates, architecture notebook).
- Learning lab materials (Jupyter scenario + talk track deck + newsletter template).

## Work Breakdown
| Track | Tasks | Owner | Notes |
| --- | --- | --- | --- |
| Chaos & Reliability | Add fault-injection scripts, resilience tests, chaos docs | Research Maintainer | Inspired by `research/chaos_agents.txt` |
| Confidence Tooling | Integrate coverage, mutmut, CI badges | QA + Infra | Guard against regressions |
| Contributor UX | Auto setup scripts, issue templates, Backstage catalog | Community | Make onboarding simple |
| Growth & Story | Labs, release notes, visuals, media kit | Storyteller | Keep research framing front-and-center |

## Timeline (aggressive)
- **Day 0**: Add tooling infrastructure (coverage, mutmut, scripts) + skeleton docs.
- **Day 1**: Build chaos scenarios, run against adapters/policy, document findings.
- **Day 2**: Publish contributor/growth toolkit, final QA pass, update README & changelog.

## Risks & Mitigations
- **Mutation tests slow** → allow opt-in via make target; cache results.
- **Chaos scripts flaky** → run in isolated env with deterministic seeds.
- **Documentation drift** → update docs/README in same PR; add doc lint (TODO).

## Success Criteria
- `make qa` extended to include coverage >90% enforcement and mutmut smoke test.
- Chaos scripts run without failures and surface meaningful metrics.
- New contributors can run `./scripts/setup_quickstart.sh` and be productive in <10 minutes.
- Marketing assets highlight research mission with new shareables.
