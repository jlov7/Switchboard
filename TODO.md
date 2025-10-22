# TODO Backlog

- [x] Implement Bedrock AgentCore and Vertex Agent Engine adapters (dry-run + live toggles).
- [x] Persist approvals metadata via `switchboard.storage` (SQLite/Postgres ready).
- [ ] Integrate Slack/Teams approvals and notifications.
- [ ] Swap HMAC signer for Sigstore keyless signatures.
- [ ] Wire `evals/runner.py` into CI with real Graph2Eval/SWE-Bench-Pro datasets.
- [ ] Add SSO (OIDC) to the FastAPI layer and Streamlit UI.
- [ ] Add circuit breakers/retries to adapters with configurable backoff.
- [ ] Provide Terraform/IaC for cloud deployments.
- [x] Promote hypothesis property tests for policy edge cases (tests/property/test_policy_props.py).
- [x] Build Grafana dashboard recipe for OTEL metrics (observability/grafana/switchboard_dashboard.json).

- [x] Add DB outage chaos script covering persistent store (scripts/chaos/db_outage.py).
- [x] Automate newsletter dispatch via GitHub Action (.github/workflows/newsletter.yml).
