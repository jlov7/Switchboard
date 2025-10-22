# Switchboard Narrative Overview

## The Problem
Enterprise AI teams are excited about Model Context Protocol (MCP) connectors in ChatGPT and cross-cloud agent frameworks like AWS Bedrock AgentCore and Vertex AI Agent Engine. Yet governance leaders still worry: which actions are happening, who approved them, and can we prove adherence to the EU GPAI Code of Practice or internal audit mandates?

## The Switchboard Answer
Switchboard is a policy-first control plane that bridges MCP tool calls and ACP agent-to-agent messages. It treats every agent action as a governed transaction:

- **Route**: Decide which adapter should execute the action (MCP, ACP, future Bedrock/Vertex connectors).
- **Approve**: Apply policy-as-code (OPA/Rego + local safeguards) to auto-allow, require human approval, or block.
- **Prove**: Stamp every decision with COSE-style signatures and log to a Rekor-compatible transparency journal.

## Why Now
- **MCP connectors** became real inside ChatGPT (Oct 17, 2025). Enterprises can now give agents direct tool access.
- **LangGraph 1.0** and signed releases prove agent graphs are production-ready, reducing build risk.
- **Bedrock AgentCore GA** and **Vertex AI Agent Engine** updates show multi-cloud agent ops are a near-term requirement.
- **EU GPAI Code of Practice** and IETF provenance drafts give regulators a framework to evaluate safe tool use.

## What You Get in this Repo
1. **FastAPI control plane** with `/route`, `/policy/check`, `/approve`, `/audit/verify`, plus observability and access to pending approvals.
2. **OPA/Rego policies** implemented alongside a resilient local evaluator, covering SoD, high-severity rate limits, and PII approvals.
3. **Adapters** for MCP, ACP, and optional Bedrock/Vertex connectors (dry-run by default, live-ready with extras).
4. **Persistent approvals store** backed by SQLite/Postgres so multi-instance Switchboard stays in sync.
5. **Signed audit trail** with deterministic signatures and Rekor integration (offline-friendly by default).
6. **LangGraph demo agent** that exercises allowed, needs-approval, and blocked flows end-to-end.
9. **Chaos scripts** to simulate OPA outages and adapter flaps.
7. **Streamlit approvals UI** crafted with accessibility notes so keyboard and screen-reader users can review actions.
8. **Evaluation harness stub** hooking into Graph2Eval and SWE-Bench-Pro concepts for contamination-resistant testing.

## Storyboard (Share with Execs)
1. **Kickoff** – “Agents are ready to call your critical systems. Are you ready to govern them?”
2. **Live Demo** – Run `make dev` and `make demo-e2e`; approve a request in the UI and show the signed audit log.
3. **Assurance** – Highlight policy-as-code, dual-control approvals, and provenance for regulators.
4. **Scale** – Discuss adapters for Bedrock AgentCore/Vertex Agent Engine and integration into enterprise IAM.

Switchboard turns agent autonomy from a risk into a governed operating model.
