# Switchboard Lab: Change Request Governance

This lab walks through policy-mediated approvals using the demo stack.

## Learning goals

- Understand how MCP actions flow through Switchboard policies.
- Practice approving/denying requests via the Streamlit UI.
- Inspect signed audit records and chaos scenarios.

## Prereqs

- `make dev`
- `make seed`
- Optional: run `scripts/setup_quickstart.sh` first.

## Exercises

1. **Happy path** – run `make demo-e2e`, approve the request in the UI.
1. **OPA outage** – run `scripts/chaos/opa_outage.py` and observe fallback decisions.
1. **Adapter chaos** – execute `scripts/chaos/adapter_flap.py` and inspect logs.
1. **Audit validation** – `make audit-verify` and parse `data/audit-log.jsonl`.

## Reflection questions

- What policies blocked the production scope action?
- How could you tune rate limits for your environment?
- Which metrics from Grafana highlight risky behavior?

Share findings or improvements via GitHub issues tagged `lab-feedback`.
