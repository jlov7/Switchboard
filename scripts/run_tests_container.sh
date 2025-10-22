#!/usr/bin/env bash
set -euo pipefail

docker build -t switchboard-tests -f infra/docker/Dockerfile.test .
docker run --rm switchboard-tests
