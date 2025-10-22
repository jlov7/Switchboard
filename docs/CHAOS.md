# Chaos Playbook

Switchboard includes lightweight chaos scripts to validate resilience assumptions.

## Scripts

- `scripts/chaos/opa_outage.py` – simulates OPA being unreachable. Expected: `/route` still succeeds via local policy engine.
- `scripts/chaos/adapter_flap.py` – hammers a partner adapter namespace to observe retries/logging.
- `scripts/chaos/db_outage.py` – points DB env to in-memory sqlite to mimic outage.

## How to run

```bash
make dev
python scripts/chaos/db_outage.py
python scripts/chaos/opa_outage.py
python scripts/chaos/adapter_flap.py
```

## Observability

- Watch API logs for fallback decisions.
- Grafana dashboard shows block counts + latency.
- Use `make audit-verify` after chaos to ensure audit trail integrity.

## Future Ideas

- Inject network latency/packet loss via tools like `toxiproxy`.
- Replay recorded actions with chaos toggles.
- Automate chaos runs in CI (see `.github/workflows/chaos.yml`).

Document chaos experiments in issues tagged `chaos-notes`.
