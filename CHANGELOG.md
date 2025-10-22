# Changelog

## Unreleased
- Added persistent approval store with SQLite/Postgres backend (`switchboard.storage`).
- Introduced Bedrock AgentCore and Vertex Agent Engine adapters (dry-run by default, live-ready).
- Added database init script (`scripts/init_db.py`) and `make db-init` target.
- Expanded testing stack with tox, pytest-httpx, and cloud adapter dry-run coverage.
- Refreshed documentation suite: README, onboarding guide, research positioning, growth playbook, testing guide.
- Added optional `.pre-commit-config.yaml` for consistent linting.
