# Observability & Grafana Quickstart

This guide shows how to wire Grafana to the Switchboard OTEL pipeline and visualize the included dashboard (`observability/grafana/switchboard_dashboard.json`).

## 1. Prerequisites

- Running Switchboard stack via `make dev` (which boots the OTLP collector).
- Prometheus-compatible backend receiving OTEL metrics (e.g., [prometheus-community/otel-collector](https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus) or the lightweight docker-compose snippet below).
- Grafana 9+ with access to the Prometheus datasource.

### Minimal Prometheus collector (optional)

```yaml
# save as observability/prometheus-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

The matching `prometheus.yml` scrapes the OTEL collector metrics endpoint:

```yaml
scrape_configs:
  - job_name: switchboard-otel
    scrape_interval: 15s
    static_configs:
      - targets: ['otel-collector:8889']
```

Run with `./scripts/run_grafana_stack.sh` (uses docker compose to boot Prometheus + Grafana and auto-load the dashboard).

## 2. Import the Dashboard

1. Open Grafana → Dashboards → Import.
1. Upload `observability/grafana/switchboard_dashboard.json`.
1. Select your Prometheus datasource when prompted.

The dashboard includes:

- **API Requests (5m rate)** – `http_server_duration_count` converted to req/s.
- **Blocked Actions (5m)** – `switchboard_policy_blocks_total` (exported via OpenTelemetry counters).
- **API Latency Quantiles** – p95/p99 latency using histogram buckets.

> Tip: Enable OTEL metric export to Prometheus by adding an OTLP → Prometheus receiver/exporter in `infra/docker/otel-collector-config.yml` if you prefer pushing rather than scraping.

## 3. Extending Metrics Coverage

- Instrument new counters with `switchboard.telemetry.setup` or FastAPI middleware.
- Add approvals metrics (e.g., `switchboard_approvals_pending_total`).
- Use exemplars or traceID attributes to link metrics with audit events.

## 4. Alerting Ideas

- High block rate (`switchboard_policy_blocks_total`) spikes.
- Approval queue backlog > N for more than 10 minutes.
- API p99 latency crossing SLO thresholds.

Feel free to iterate on the JSON dashboard and contribute improvements back to `observability/grafana/`.
