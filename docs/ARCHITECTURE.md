# Architecture Deep Dive

## High-Level Diagram
```
User / Agent --> Switchboard API --> Adapter (MCP/ACP) --> Tool / Partner Agent
                          |              |
                          |              +--> Rekor (transparency log)
                          |--> Policy Engine (OPA + local)
                          |--> Audit Service (COSE-style signatures)
                          |--> Approvals Queue (Streamlit UI)
```

## Components

### API Layer
- **FastAPI** app exposes routing, policy checks, approvals, and signature verification.
- **OpenTelemetry** instrumentation automatically emits traces/metrics to an OTLP collector.
- **Structlog** JSON logs include redacted arguments to maintain observability without leaking secrets.

### Policy Engine
- Wraps Open Policy Agent (OPA) but fails open into a deterministic **LocalPolicyEngine** so tests/demos never stall if OPA is offline.
- Rego bundle (`switchboard/policy/base.rego`) codifies:
  - `role=ops` requirement for production scopes.
  - `p0` severity rate limiting (1 per 5 minutes).
  - Automatic approval for `pii` or `sensitivity_tags` that hit financial/legal keywords.
- Local engine mirrors the same checks and keeps a sliding window per tenant/tool/severity to enforce rate limits.

### Adapters
- **MCPAdapter**: Bridges to the example MCP server (Jira + GitHub tools). Real-world connectors swap the HTTP endpoint with your MCP broker.
- **ACPAdapter**: Demonstrates push into partner agents following the Agent Communication Protocol (ACP) pattern.
- `AdapterRegistry` centralizes adapter lookup and lifecycle; new connectors (Bedrock, Vertex, ServiceNow) simply register themselves.

### Audit & Provenance
- Deterministic signature via `AuditSigner` (COSE-ready HMAC for demo). Swap with hardware-backed keys for production.
- Persistent log (`data/audit-log.jsonl`) plus optional Rekor transparency append. Offline-friendly to avoid network blockers.
- `scripts/verify_audit.sh` replays the signature for local assurance.

### Approvals Workflow
- `ApprovalStore` tracks pending approvals with route metadata.
- `ApprovalStore` now defaults to the persistent backend (`switchboard/storage/approvals.py`) using SQLite/Postgres for shared state.
- **Streamlit UI** polls `/approvals/pending`, letting dual-control approvers review sanitized payloads and approve/deny with keyboard shortcuts.
- Accessibility taken seriously: descriptive headings, container borders, actionable text for screen readers.

### Telemetry & Observability
- OTLP exporter produces traces/metrics (latency, block counts) ready for Grafana, DataDog, or CloudWatch.
- `structlog` plus request IDs give auditors a consistent paper trail.

## Data Flow Example
1. LangGraph agent posts to `/route`.
2. Policy engine evaluates; severity and tags trigger approval.
3. Audit record is signed and logged; pending approval stored.
4. Human approves via Streamlit UI (`/approve`).
5. Adapter executes tool call; result returned to agent.
6. Rekor log entry recorded and accessible for auditors.

## Extending the Plane
- **Adapters**: Implement `BaseAdapter.execute_action` to talk to Bedrock AgentCore, Vertex Agent Engine, or ServiceNow. Bedrock/Vertex adapters shipped here default to dry-run and can be toggled live with env vars.
- **Policies**: Add new Rego files and update `scripts/seed_policies.py` to publish bundles.
- **Audit**: Swap `AuditSigner` with Sigstore, AWS KMS, or Azure Key Vault to meet enterprise compliance.
- **Storage**: Swap SQLite for managed Postgres by updating `SWITCHBOARD_DATABASE_URL`; Redis caching is a future enhancement.
