#!/usr/bin/env bash
set -euo pipefail

pushd observability/grafana > /dev/null
if ! command -v docker-compose >/dev/null 2>&1 && command -v docker compose >/dev/null 2>&1; then
  docker compose up -d
else
  docker-compose up -d
fi
popd > /dev/null

echo "Grafana available at http://localhost:3000 (user: admin / pass: admin)"
echo "Prometheus scraping Switchboard OTEL metrics at http://localhost:9090"
