# Change Request Demo

This script showcases how Switchboard routes a Jira change request through policy checks, approvals, and audit logging.

## Steps

1. **Allowed** – A standard Jira ticket creation executed immediately.
2. **Needs Approval** – An update containing financial PII is paused until a human approves.
3. **Blocked** – A production-scope change attempted by a non-ops role is denied.

Run with:

```bash
make demo-e2e
```

Watch the approvals queue at [http://localhost:8501](http://localhost:8501) to approve or deny actions, and inspect the signed audit trail in `data/audit-log.jsonl`.
