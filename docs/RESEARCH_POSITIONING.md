# Research Positioning

Switchboard is intentionally framed as a **research project** to explore policy-first guardrails for multi-protocol agents. It is not a commercial product and carries no service guarantees.

## Research Questions
1. Can a neutral control plane mediate both MCP (tool use) and ACP (agent-to-agent) without locking into one vendor?
2. What mix of policy-as-code, human approvals, and provenance evidence satisfies emerging AI governance frameworks (EU GPAI Code, IETF provenance draft)?
3. How do multi-cloud agent runtimes (LangGraph, Bedrock AgentCore, Vertex Agent Engine) interact with central oversight?

## Anchoring Signals
- **MCP in ChatGPT** (Oct 2025) – direct access to enterprise tools is now a default expectation.
- **LangGraph 1.0** – production-ready agent graphs invite governance overlays.
- **AWS Bedrock AgentCore GA** + **Vertex Agent Engine updates** – multi-cloud agent ops is here.
- **EU GPAI Code of Practice** + **IETF provenance draft** – compliance regimes expect auditability + oversight.
- **Agent evals renaissance** (Graph2Eval, SWE-Bench-Pro) – highlights need for tool-use aware testing harnesses.

See the raw research pulls under `research/` for source material.

## Guiding Principles
- **Explainability beats opacity** – every approval, block, and signature must be inspectable.
- **Fail safe** – offline-friendly defaults (SQLite, dry-run adapters, local audit logs).
- **Composable** – clear interfaces for adapters & policies so future researchers can swap components.
- **Accessible** – inclusive approvals UI & docs so security, audit, and builder personas can collaborate.

## What Success Looks Like
- Reproducible demos that show safe/unsafe tool invocations with zero manual tweaks.
- External researchers can re-run the evaluation harness and verify provenance.
- Contributors map new policies/adapters quickly thanks to docs & tests.

If you have feedback, open a discussion or DM – the objective is to learn in public.
