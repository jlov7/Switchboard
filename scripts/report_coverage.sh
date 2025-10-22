#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
coverage erase
pytest --cov=switchboard --cov-report=xml --cov-report=term-missing "$@"
coverage-badge -o reports/coverage-badge.svg
coverage json -o reports/coverage.json
