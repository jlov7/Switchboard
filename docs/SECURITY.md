# Security & Compliance Playbook

## Policy Controls
- **Segregation of Duties**: Production actions require `role=ops`. Extend with department-level policies to prevent self-approval.
- **PII Handling**: `pii=true` or financial/legal sensitivity tags force manual approvals and redact payload fields in logs.
- **Rate Limiting**: Severity-aware token bucket ensures high-severity actions are rare and reviewable.

## Provenance & Audit
- Every decision produces a signed `AuditRecord` (COSE-style with deterministic HMAC for demo).
- `RekorClient` logs entries to Sigstore-compatible transparency log; offline fallback ensures air-gapped environments still capture events.
- `scripts/verify_audit.sh` verifies signatures locally. Integrate with your GRC tooling to automate evidence collection.

## Secrets & Config
- `.env.example` documents required environment variables. Use HashiCorp Vault or cloud secrets managers in production.
- `AuditSigner` secret key should come from an HSM or cloud KMS. Rotate on a schedule and update the verification path.

## Access Control
- Approvals UI is an independent Streamlit app; front it with your SSO (Okta, Azure AD) for workforce auth.
- Future roadmap (see README) includes RBAC at the API layer, per-tenant policy packs, and Slack approvals.

## Privacy
- `redacted_fields` on `ActionArguments` masks sensitive values in logs and UI.
- Ensure tool adapters apply least-privilege OAuth scopes.
- Activate OTEL attribute filters before exporting into shared observability backends.

## Compliance Mapping (Highlights)
- **EU GPAI Code of Practice**: Transparency (signed logs), risk management (policy-as-code), human oversight (approvals).
- **SOX / Internal Controls**: Dual-control approvals, detailed audit trails, segregation of duties.
- **HIPAA/PCI**: PII tagging, redaction, ready for PHI-specific policies.

## Threat Scenarios & Mitigations
| Threat | Mitigation |
| --- | --- |
| Prompt injection modifies arguments | Validate payload via Pydantic, enforce policy schema, redacted logs for review |
| Adapter downtime | Registry supports retries; add circuit breakers and DLQs per adapter |
| Approval spamming | Persistent store deduplicates by approval ID + request hash (extendable with hashed body) |
| Clock skew breaks signatures | AuditSigner encodes timestamp; use NTP or signed timestamps (roadmap) |

## Responsible Deployment Checklist
1. Configure `SWITCHBOARD_DATABASE_URL` to use managed Postgres for state persistence; add Redis caching only if approvals volume demands it.
2. Wire OTLP exporter into your observability stack with alerting on block/approval anomalies.
3. Harden Dockerfiles with non-root users, pinned dependencies, SBOM scans.
4. Integrate evaluation harness (`evals/runner.py`) into CI pre-prod gates.
5. Run tabletop exercises with audit/compliance to rehearse investigations.
