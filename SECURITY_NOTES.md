# Security Notes (Summary)

- Enforce policy gates via Rego + local evaluator; default deny for production scope without `role=ops`.
- Sign every audit event with deterministic COSE-style HMAC signature; rotate keys via environment secrets.
- Redact fields flagged in `ActionArguments.redacted_fields` before logging.
- Approvals UI designed with dual-control; integrate SSO before production use.
- Persistent approvals store now defaults to SQLite; point `SWITCHBOARD_DATABASE_URL` at managed Postgres for shared deployments.
- Enable Rekor logging in production for tamper-evident provenance.
- Harden Docker images (non-root, pinned versions) prior to enterprise deployment.

See `docs/SECURITY.md` for full details.
