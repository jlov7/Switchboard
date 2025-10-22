# Switchboard Research Upgrade Plan

This iteration focuses on taking Switchboard from a functional demo to a **research-grade governance control plane** that others can study, reproduce, and extend. The plan is grounded in the latest references captured under `research/` (Bedrock AgentCore GA, Vertex AI Agent Engine, Sigstore Rekor guidance, OPA best practices, Graph2Eval, SWE-Bench-Pro) and aims to keep the project framed as a personal passion project rather than a commercial product.

## Goals
1. **Reliability** – eliminate single-node state by persisting approvals/audit metadata in a lightweight, optional database layer.
2. **Interoperability** – add cloud adapters for AWS Bedrock AgentCore and Vertex AI Agent Engine (opt-in, credential-aware).
3. **Observability & Evaluation** – expand testing harnesses (fuzzing, replay, eval suites) to keep bug count at zero.
4. **Narrative & Growth** – document the research framing, provide media kits, and make onboarding effortless for new contributors.

## Roadmap Overview
| Track | Key Tasks |
| --- | --- |
| **Persistence & State** | Introduce `switchboard.storage` with async backends for SQLite (default) and Postgres. Build a `PersistentApprovalStore` used by the router. Add `scripts/init_db.py` and `make db-init`. |
| **Adapters** | Implement opt-in adapters: `BedrockAgentCoreAdapter` (SigV4-signed AWS calls) and `VertexAgentEngineAdapter` (Google Cloud REST). Guard behind environment variables and optional dependencies. Provide mocked test coverage. |
| **Testing & Eval** | Add property-based fuzz tests for policy decisions, pytest fixtures for persistent storage, and extend `evals/runner.py` to capture replay traces. Integrate `pre-commit` + `tox` for consistent QA. |
| **Docs & Media** | Refresh README to emphasize research project status, add onboarding guide (`docs/GETTING_STARTED.md`), security/testing deep-dives, and a growth/media playbook with ready-to-share content. Provide Mermaid diagrams and CLI asciinema script references. |

## Delivery Phases
1. **Foundation (Day 0)** – set up storage module, migrations, config updates, and tests.
2. **Cloud Interop (Day 0-1)** – add AWS/GCP adapters with optional dependencies and docs.
3. **Quality Gates (Day 1)** – extend pytest + tox + fuzz harness; update CI to run both sqlite and in-memory tests.
4. **Story & Growth (Day 1)** – overhaul documentation, media kits, onboarding instructions, and research positioning.

## Risks & Mitigations
- **Credential Misconfiguration** – provide defensive checks and dry-run commands for adapters; document env var requirements.
- **Test Flakiness** – rely on sqlite for CI, mock external services; isolate cloud calls behind interfaces.
- **Scope Creep** – keep enterprise add-ons as future TODOs; stay focused on research-grade reliability & documentation.

This plan guides the implementation work in the subsequent steps.
