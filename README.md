# Switchboard — MCP↔ACP Governance Control Plane (Research Edition)

> Personal passion project exploring how to govern autonomous agent actions across MCP tools and ACP agent meshes with policy-as-code, human approvals, and signed provenance.

## Why This Exists (Research Framing)

- **Enterprise agents are real** – MCP connectors launched in ChatGPT Business/Enterprise (Oct 2025), AWS Bedrock AgentCore is GA, and Vertex Agent Engine is getting priced like a platform
- **Governance is lagging** – EU GPAI Code of Practice and IETF provenance drafts call for provable oversight across tool-using agents
- **Hypothesis** – A protocol-neutral “switchboard” can sit between MCP/ACP, add policy/approvals, and emit transparency logs that satisfy risk teams without throttling builders

This repo is a research sandbox, not a product. Switchboard is a personal passion project; feel free to fork, remix, and study. Expect detailed docs, reproducible demos, and lots of TODOs for future explorers.

## New in this Iteration

- ✅ **Persistent approvals** via `switchboard.storage` (SQLite by default, Postgres ready)
- ✅ **Chaos scripts** (`scripts/chaos/`) simulating OPA outages & adapter flaps
- ✅ **Coverage & mutation** targets (`make coverage`, `make mutation`) with 90% gate
- ✅ **Cloud adapters** (AWS Bedrock AgentCore & Vertex AI Agent Engine) with dry-run defaults + live toggles
- ✅ **Expanded QA**: tox profile, Hypothesis fuzzing hooks, pytest-httpx for adapter simulation
- ✅ **Docs refresh**: research posture, onboarding guide, growth/media kit, operations runbook updates

## Quickstart (Local Sandbox)

```bash
# 1. Install dev deps
make install
# or bootstrap everything via the quickstart script
./scripts/setup_quickstart.sh

# (optional) install cloud extras
make install-extras  # adds boto3 + google-cloud-aiplatform

# 2. Initialize the local SQLite backing store
make db-init

# 3. Seed OPA with the sample policies
make seed

# 4. Fire up the stack (API, MCP server, demo agent, approvals UI, OPA, OTEL)
make dev

# 5. Run the change-request storyline (allowed → needs approval → blocked)
make demo-e2e

# 6. Verify the signed audit trail
make audit-verify
make coverage            # coverage gate
make mutation            # run mutation smoke test
# optional: auto-provision Grafana + Prometheus
./scripts/run_grafana_stack.sh
```

Endpoints & consoles:

- API docs: http://localhost:8000/docs
- Approvals UI (accessible Streamlit): http://localhost:8501
- Audit log: `data/audit-log.jsonl`

## Testing & Quality Gates

- `make qa` – lint (`ruff`, `black`), type check (`mypy`), tests
- `make coverage` – coverage gate (90%)
- `make mutation` – mutation smoke test via mutmut
- `tox` – py311 environment with in-memory sqlite
- `pytest` – unit + integration coverage, now including property tests and chaos fixtures
- `evals/runner.py` – Graph2Eval/SWE-Bench-inspired runner for task suites
- `scripts/report_coverage.sh` – generates badge + JSON report in `reports/`
- `scripts/report_mutation.sh` – produces mutation text/HTML summaries

## Evaluations

- `docs/EVALS.md` explains how to extend the evaluation harness.
- Sample dataset: `evals/datasets/graph2eval_sample.jsonl`
- Append JSONL datasets via `--dataset` flag when running `evals/runner.py`.

## Architecture Snapshot

```
LangGraph Agent --> /route -----------------------------┐
                                                       |
                                                       v
                                               Policy Engine
                                               (OPA + local)
                                                       |
                                    ┌──────────────────┴──────────────────┐
                                    v                                     v
                            Approvals Store (persistent)      Audit Service (COSE + Rekor)
                                    |                                     |
                                    v                                     v
                        Streamlit UI / CLI Approvals          Transparency log entries
                                    |
                                    v
 Adapter Registry ──▶ MCP Adapter (Jira/GitHub)
                  └▶ ACP Adapter (partner agents)
                  └▶ Bedrock Adapter (dry-run/live)
                  └▶ Vertex Adapter  (dry-run/live)
```

Telemetry: OTLP traces + metrics, structlog JSON logs with redacted arguments.

## Persistence & Configuration

- `SWITCHBOARD_APPROVAL_BACKEND` – defaults to `persistent`; set to `memory` for ephemeral tests
- `SWITCHBOARD_DATABASE_URL` – defaults to `sqlite+aiosqlite:///data/switchboard.db`; set to Postgres DSN for multi-instance deployments
- `scripts/init_db.py` – bootstraps the schema; run via `make db-init`

## Cloud Adapter Cheatsheet

| Adapter | Enable | Mode | Env knobs | Notes |
| --- | --- | --- | --- | --- |
| AWS Bedrock AgentCore | `SWITCHBOARD_ENABLE_BEDROCK=true` | `SWITCHBOARD_AWS_MODE` (`dry-run` / `live`) | `AWS_REGION`, `AWS_BEDROCK_AGENT_ID`, `AWS_BEDROCK_AGENT_ALIAS_ID` | Requires `pip install .[aws]` for live mode; dry-run echoes payloads |
| Vertex Agent Engine | `SWITCHBOARD_ENABLE_VERTEX=true` | `SWITCHBOARD_GCP_MODE` (`dry-run` / `live`) | `GOOGLE_CLOUD_PROJECT`, `VERTEX_AGENT_ID`, `VERTEX_LOCATION` | Requires `pip install .[gcp]`; uses Google ADC for auth when live |

Both adapters default to **dry-run** to keep demos and tests deterministic. Flip to `live` when you want to hit real services.

## Testing & Evaluation

- `make qa` – lint (`ruff`, `black`), type check (`mypy`), tests
- `tox` – py311 environment with in-memory sqlite + hypothesis hooks
- `pytest` – now includes persistent store tests, adapter dry-runs, audit verification, and API integration tests
- `evals/runner.py` – extended runner emits latency + routing summaries; plug in your own Graph2Eval/SWE-Bench-Pro tasks
- Property-based testing foundation via `hypothesis` (see `tests/property/` once added)

## Documentation & Media Trail

New/updated files worth reading:

- `docs/GETTING_STARTED.md` – teammate onboarding
- `docs/RESEARCH_POSITIONING.md` – why this is a research project, not a product
- `docs/GROWTH_PLAYBOOK.md` – ready-to-share posts, demo scripts, metrics to highlight
- `docs/TESTING.md` – QA matrix + manual checklists
- `docs/IMPLEMENTATION_PLAN.md` / `docs/IMPLEMENTATION_PLAN_V2.md` – roadmaps driving iterations
- `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/OPERATIONS.md` – refreshed for persistence & adapters
- `docs/CHAOS.md` – chaos playbook (OPA outage, adapter flaps)
- `docs/OBSERVABILITY_GRAFANA.md` – dashboard + metrics walkthrough
- `docs/CONTRIBUTOR_QUICKSTART.md` – onboarding script + checklist
- `docs/labs/change_request_lab.md` – hands-on learning path
- `docs/TALK_TRACK.md`, `docs/NEWSLETTER_TEMPLATE.md`, `docs/RELEASE_NOTES_0.2.md` – storytelling assets
- `docs/EVALS.md` – how to extend the evaluation harness with real datasets
- `docs/media/switchboard_poster.md` – visual poster for presentations

## Adapting / Extending

- **Policies** – edit `switchboard/policy/*.rego`, re-run `scripts/seed_policies.py`
- **Adapters** – register new connectors in `switchboard/core/router.py` or extend `AdapterRegistry`
- **Storage** – plug in your own backend via `SWITCHBOARD_DATABASE_URL` (SQLite → Postgres)
- **Approvals UX** – customize Streamlit app (`apps/approvals_ui/main.py`) or swap in your SSO-protected frontend

## Contributions & Growth Hacking

This is still a personal research effort, but collaboration is welcome:

1. Read `CODE_OF_CONDUCT.md`
1. Check `TODO.md` and `docs/GROWTH_PLAYBOOK.md` for bite-sized tasks
1. Use `make qa` before PRs; CI (`.github/workflows/ci.yml`) runs lint + tests + tox stub
1. Share learnings! There’s a builder’s log + micro-post draft in `docs/GROWTH_PLAYBOOK.md`

## License

Apache-2.0 for the core. Optional enterprise features (SSO, hosted Rekor, advanced policy packs) remain future research ideas.

______________________________________________________________________

*If you explore or extend this repo, let me know what you discover—this is about pushing the state of agent governance, not shipping a SKU.*
