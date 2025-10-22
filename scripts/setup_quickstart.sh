#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "python3.11 is required" >&2
  exit 1
fi

python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
make db-init
make seed
make qa
