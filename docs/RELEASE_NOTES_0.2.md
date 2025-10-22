# Switchboard Research Release Notes — v0.2

## TL;DR

- Chaos engineering scripts stress policy engine and adapters.
- Coverage gate (90%) + mutation tests keep regressions in check.
- Contributor quickstart + issue templates streamline onboarding.
- Grafana dashboard + lab material help tell the story.

## Highlights

- Added Hypothesis property tests for policy invariants.
- Created chaos scripts for OPA outages and adapter flapping.
- Integrated pytest coverage + mutmut, updated CI to publish coverage.
- Shipped quickstart setup script, Backstage catalog entry, issue templates.
- Authored lab guide, talk track, and newsletter template for growth hacking.

## Breaking changes

- None.

## Upgrade notes

Run:

```bash
pip install -e .[dev]
make db-init
make seed
make qa
```

Explore new tooling:

- `make coverage`
- `make mutation`
- `scripts/chaos/opa_outage.py`
- `scripts/chaos/adapter_flap.py`

Feedback welcome via GitHub issues tagged `release-0.2`.
