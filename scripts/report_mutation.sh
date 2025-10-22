#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
mutmut run "$@"
mutmut results > reports/mutmut.txt
mutmut html --report-html reports/mutmut.html || true
