# Operations Runbook

## Setup
1. Clone repo and create `.env` from `.env.example`.
2. Run `make install` for local dev or `make dev` to start Docker Compose stack (API, demo agent, MCP server, approvals UI, Postgres, OPA, OTEL).
3. Initialize database schema with `make db-init` (defaults to SQLite unless `SWITCHBOARD_DATABASE_URL` points at Postgres).
4. Seed OPA policies: `make seed` (requires OPA container running).

## Day-2 Operations
- **Monitoring**: Scrape OTLP collector with Grafana/Prometheus. Alert on high block rates or approval queues >5 items.
- **Audit Retrieval**: Tail `data/audit-log.jsonl` or access Rekor entry referenced in `verification_url`.
- **Policy Updates**: Modify Rego files, rerun `scripts/seed_policies.py`, and version policies via Git tags.
- **Adapter Lifecycle**: Register new adapters in `AdapterRegistry`; ensure health checks before enabling.
- **Approvals UI**: Operators see policy rationale, risk level, a copy-paste audit verification command, can run a live `/audit/verify` check, and download the JSON receipt for evidence.

## Incident Response
1. Use `scripts/verify_audit.sh <AUDIT_EVENT_ID>` (optionally `--rekor-url`, `--json`) to confirm integrity of suspect events; failures emit a `failure_reason` line or JSON field for instant triage.
2. Query approvals UI for outstanding requests; deny suspicious items.
3. Adjust policies and redeploy (hot reload supported when using Uvicorn in dev mode).
4. Document outcomes in your GRC tooling using export from `data/audit-log.jsonl`.

## Scaling Guidance
- Deploy API and adapters in separate pods/services; use message queues for backpressure.
- Replace in-memory ApprovalStore with persistent DB + cache. Sample schema provided in README.
- Enable Sigstore Rekor logging in production for tamper-evident audits.

## Backup & Recovery
- Persisted artifacts: Postgres DB (policies, approvals), audit log, policy bundles.
- Back up using standard cloud snapshots. Verify restore by running `scripts/verify_audit.sh <AUDIT_EVENT_ID>` on restored logs and confirm the absence of a `failure_reason`.

## Change Management
- Use feature flags or configuration toggles for new policies.
- Maintain a staging environment with the evaluation harness connected to Graph2Eval-style suites before shipping to prod.
