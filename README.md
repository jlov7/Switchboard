# 🔄 Switchboard — Enterprise AI Agent Orchestration Platform

<div align="center">

[![CI/CD Pipeline](https://github.com/jlov7/Switchboard/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/jlov7/Switchboard/actions/workflows/ci-cd.yml)
[![CodeQL Security](https://github.com/jlov7/Switchboard/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/jlov7/Switchboard/actions/workflows/codeql-analysis.yml)
[![Coverage Status](https://codecov.io/gh/jlov7/Switchboard/branch/main/graph/badge.svg)](https://codecov.io/gh/jlov7/Switchboard)
[![Python Versions](https://img.shields.io/pypi/pyversions/switchboard.svg)](https://pypi.org/project/switchboard/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://hub.docker.com)
[![Dependabot](https://img.shields.io/badge/Dependabot-Enabled-brightgreen.svg)](https://github.com/jlov7/Switchboard/security/dependabot)

**Multi-Provider AI Agent Orchestration with Enterprise-Grade Governance**

</div>

[![Switchboard approval flow walkthrough](docs/media/generated/hero.gif)](docs/media/generated/hero.mp4)

<div align="center">

**🎬 Watch the 90-second hero demo →** [docs/media/generated/hero.mp4](docs/media/generated/hero.mp4)

</div>

---

## 🎯 Mission

Switchboard is an independent R&D sandbox for orchestrating AI agents across multiple providers (OpenAI, AWS Bedrock, Google Vertex) while experimenting with policy-based approvals, cryptographic audit trails, and observability. It exists to explore governance patterns—not to provide a production SLA.

**🔬 Research Edition**: This is a personal passion project. The code is shared so others can learn, remix, and critique; any production claims require your own hardening, threat modelling, and operational controls.

## ✨ Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| **🔧 Multi-Provider Support** | OpenAI, AWS Bedrock AgentCore, Google Vertex AI | 🧪 Research Prototype |
| **🛡️ Policy-Based Governance** | OPA (Open Policy Agent) with custom rules | 🧪 Research Prototype |
| **✅ Human Approval Workflows** | Persistent approval system with UI | 🧪 Research Prototype |
| **📋 Cryptographic Audit Trails** | COSE signatures + Rekor transparency logs | 🧪 Research Prototype |
| **📊 Enterprise Observability** | OTLP traces, metrics, structured logging | 🧪 Research Prototype |
| **🔒 Security Scanning** | CodeQL, Bandit, Safety vulnerability scanning | 🧪 Research Prototype |
| **🚀 CI/CD Pipeline** | Automated testing, Docker builds, releases | 🧪 Research Prototype |
| **📦 Container Ready** | Multi-stage Docker builds for all components | 🧪 Research Prototype |
| **🔄 Auto Dependency Updates** | Dependabot for Python, GitHub Actions, Docker | 🧪 Research Prototype |
| **🧪 Comprehensive Testing** | Unit, integration, property-based, chaos testing | 🧪 Research Prototype |

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

## 🚀 Quickstart

### Option 1: Local Development (Recommended)

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
# grab an audit event id from data/audit-log.jsonl (or approvals UI)
make audit-verify AUDIT_ID=<uuid>
# alternatively call the script directly (supports --rekor-url)
./scripts/verify_audit.sh <AUDIT_EVENT_ID>
# add --json for machine-readable receipts (ideal for CI or GRC ingestion)
make coverage            # coverage gate
make mutation            # run mutation smoke test
# optional: auto-provision Grafana + Prometheus
./scripts/run_grafana_stack.sh
```

### Option 2: Docker Compose (Demo Stack)

```bash
# Pull the latest release images
docker-compose -f docker-compose.release.yml pull

# Start all services
docker-compose -f docker-compose.release.yml up -d

# Or build from source
docker-compose up --build -d
```

**Available Services:**
- **API Server**: http://localhost:8000 (FastAPI with auto-generated docs)
- **Approvals UI**: http://localhost:8501 (Streamlit interface)
- **MCP Server**: http://localhost:8001 (Model Context Protocol)
- **Demo Agent**: http://localhost:8002 (Example agent implementation)

### Option 3: Individual Docker Images

```bash
# Pull specific images
docker pull ghcr.io/jlov7/switchboard:latest-api
docker pull ghcr.io/jlov7/switchboard:latest-mcp
docker pull ghcr.io/jlov7/switchboard:latest-approvals-ui
docker pull ghcr.io/jlov7/switchboard:latest-demo-agent

# Run individual services
docker run -p 8000:8000 ghcr.io/jlov7/switchboard:latest-api
docker run -p 8501:8501 ghcr.io/jlov7/switchboard:latest-approvals-ui
```

Endpoints & consoles:

- API docs: http://localhost:8000/docs
- Approvals UI (accessible Streamlit): http://localhost:8501
- Audit log: `data/audit-log.jsonl`

## Media & Storytelling Assets

- **Regenerate everything** with `make media-artifacts` (hero video, GIF loops, screenshots, heatmap, poster)
- **Hero walkthrough** – [PNG preview](docs/media/generated/hero.mp4) · [inline GIF](docs/media/generated/hero.gif)
- **Approvals queue loop** – [docs/media/generated/approvals.gif](docs/media/generated/approvals.gif)
- **Policy heatmap** – [PNG](docs/media/generated/policy_heatmap/policy_heatmap.png) · [SVG](docs/media/generated/policy_heatmap/policy_heatmap.svg)
- **Screenshot pack** – curated stills in [`docs/media/screenshots/`](docs/media/screenshots)
- **Architecture poster** – [PNG](docs/media/generated/poster/switchboard_poster.png) · [PDF](docs/media/generated/poster/switchboard_poster.pdf)
- **How-to guide** – [`docs/media/demo_instructions.md`](docs/media/demo_instructions.md)
- **Narrative framing** – [`docs/GROWTH_PLAYBOOK.md`](docs/GROWTH_PLAYBOOK.md)

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

- `SWITCHBOARD_APPROVAL_BACKEND` – defaults to `memory`; set to `persistent` when you want the shared database-backed queue
- `SWITCHBOARD_DATABASE_URL` – defaults to `sqlite+aiosqlite:///data/switchboard.db`; set to Postgres DSN for multi-instance deployments
- `scripts/init_db.py` – bootstraps the schema; run via `make db-init`

## Telemetry Controls

- `SWITCHBOARD_ENABLE_TELEMETRY` – opt-in flag (defaults to disabled); set to `true` to emit OTLP traces/metrics
- `OTEL_EXPORTER_OTLP_ENDPOINT` – override to point at your collector (defaults to `http://localhost:4317`)
- `OTEL_SDK_DISABLED=1` – hard-disable all OpenTelemetry SDK wiring if you need a zero-overhead run

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

## 🚀 Professional Development Practices

This repository implements industry-leading development practices:

### 🛡️ Security First
- **CodeQL Analysis**: Automated security vulnerability scanning on every PR
- **Dependency Scanning**: Safety and Bandit vulnerability detection
- **Branch Protection**: Required status checks, PR reviews, and up-to-date branches
- **Signed Commits**: Cryptographic verification of all changes
- **Dependabot**: Automated dependency updates with security patches

### 🔄 CI/CD Excellence
- **Multi-Python Testing**: Tested across Python 3.9-3.12
- **Docker Integration**: Multi-stage builds for all components
- **Comprehensive Coverage**: Unit, integration, property-based, and chaos testing
- **Performance Testing**: Automated benchmarks and load testing
- **Automated Releases**: Changelog generation and tagged releases

### 📊 Observability & Quality
- **90%+ Test Coverage**: Enforced coverage gates
- **Mutation Testing**: Advanced test quality validation
- **Performance Monitoring**: Built-in telemetry and metrics
- **Structured Logging**: JSON logs with sensitive data redaction

### 🏗️ Enterprise Ready
- **Multi-Environment**: Development, staging, and production configurations
- **Docker Compose**: Complete local development stack
- **Comprehensive Documentation**: Architecture, operations, and security guides
- **Issue & PR Templates**: Structured contribution workflows

## 🤝 Contributions & Growth Hacking

This is a passion project that has evolved into a professional-grade platform. Collaboration is very welcome:

1. **Read** [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
2. **Check** [`TODO.md`](TODO.md) and [`docs/GROWTH_PLAYBOOK.md`](docs/GROWTH_PLAYBOOK.md) for contribution opportunities
3. **Follow** the [PR Template](.github/PULL_REQUEST_TEMPLATE.md) for consistent contributions
4. **Use** `make qa` before submitting PRs - CI will run comprehensive checks
5. **Share** your learnings! The growth playbook has storytelling assets and metrics to highlight

### Issue Templates Available
- 🐛 **[Bug Reports](.github/ISSUE_TEMPLATE/bug_report.yml)**: Structured bug reporting with reproduction steps
- ✨ **[Feature Requests](.github/ISSUE_TEMPLATE/feature_request.yml)**: Detailed feature proposals with use cases

## License

Apache-2.0 for the core. Optional enterprise features (SSO, hosted Rekor, advanced policy packs) remain future research ideas.

______________________________________________________________________

*If you explore or extend this repo, let me know what you discover—this is about pushing the state of agent governance, not shipping a SKU.*
