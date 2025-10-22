# Getting Started Guide

This guide is aimed at teammates picking up the Switchboard research project for the first time. It assumes macOS/Linux with Docker.

## 1. Clone & Install
```bash
git clone <repo-url>
cd Switchboard
make install         # installs dev dependencies into .venv
make db-init         # creates SQLite schema under data/switchboard.db
make seed            # loads baseline OPA policies
```

## 2. Launch the Demo Stack
```bash
make dev             # docker compose: API, demo agent, MCP server, approvals UI, OPA, OTEL
```

Key services:
- API – http://localhost:8000/docs
- Approvals UI – http://localhost:8501 (screen-reader friendly)
- OPA – http://localhost:8181 (policy inspector)

## 3. Run the Storyline Scripts
```bash
make demo-e2e        # allowed → manual approval → blocked
make audit-verify    # validates the most recent COSE-style audit signature
```

## 4. Explore the Codebase
- `switchboard/api/main.py` – FastAPI endpoints
- `switchboard/core/router.py` – policy + adapter routing logic
- `switchboard/storage/` – persistent approval store implementation
- `apps/demo_agent/` – LangGraph scenario hitting every policy branch
- `scripts/` – seeding, DB init, audit verification

## 5. Optional: Enable Cloud Adapters
Install extras and toggle env vars:
```bash
make install-extras
export SWITCHBOARD_ENABLE_BEDROCK=true
export SWITCHBOARD_ENABLE_VERTEX=true
```
Both adapters default to `dry-run`. Switch to live mode when you have credentials:
```bash
export SWITCHBOARD_AWS_MODE=live
export SWITCHBOARD_GCP_MODE=live
```
Read `README.md#Cloud Adapter Cheatsheet` for all variables.

## 6. Quality Gates
```bash
make qa             # lint + mypy + pytest
tox                 # isolated py311 run (uses in-memory sqlite)
```

## 7. Documentation Tour
- `docs/OVERVIEW.md` – narrative + storyboard
- `docs/ARCHITECTURE.md` – component breakdown
- `docs/SECURITY.md` – controls, compliance mapping
- `docs/OPERATIONS.md` – day-2 ops tips
- `docs/RESEARCH_POSITIONING.md` – framing + references
- `docs/GROWTH_PLAYBOOK.md` – shareable media/posts

That’s it! Open `TODO.md` for the living backlog and `docs/IMPLEMENTATION_PLAN.md` for the current milestone overview.
