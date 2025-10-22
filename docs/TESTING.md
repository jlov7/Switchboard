# Testing & Quality Assurance

## Automated Gates

| Layer | Command | Purpose |
| --- | --- | --- |
| Lint | `ruff`, `black` | Style + import hygiene |
| Types | `mypy` | Strict typing, optional deps guarded |
| Unit Tests | `pytest` | Policy engine, router, audit signer, persistent store, adapters (dry-run) |
| Integration | `pytest` (ASGI transport) | API lifecycle, approvals, audit verification |
| Property-based | `pytest` + `hypothesis` | `tests/property/test_policy_props.py` exercises policy invariants |
| tox | `tox` | Re-run in isolated env with in-memory DB |
| Coverage | `scripts/report_coverage.sh` | Generates XML/JSON + badge under `reports/` |
| Mutation | `scripts/report_mutation.sh` | Captures mutation summary + HTML report |
| Containerized | `scripts/run_tests_container.sh` | Build + run tests in Docker image |

`make qa` runs lint + mypy + pytest. CI mirrors these steps via `.github/workflows/ci.yml` plus tox.

## Manual Checklist (Release Candidates)

- [ ] `make dev` booted, `/healthz` returns ok
- [ ] `make demo-e2e` exercised allowed/approval/blocked
- [ ] Streamlit UI shows pending items with redacted fields
- [ ] `make audit-verify` succeeds
- [ ] `evals/runner.py` against `evals/tasks/graph2eval_example.yaml`
- [ ] (Optional) dry-run Bedrock + Vertex adapters return success

## Fuzzing Hooks

`tests/property/` houses Hypothesis suites. Start with `test_policy_props.py` and extend with router / adapter invariants as you discover edge cases.

## Observability Smoke Test

With stack running:

1. Send three `/route` calls (allowed, approve, block)
1. Check OTEL collector logs for spans `switchboard-api.route`
1. Inspect `data/audit-log.jsonl` for new entries + verification reference

Keep this checklist updated as the project evolves.
