# Talk Track — "Governing Tool-Using Agents"

## Slide 1: Why this research exists
- MCP connectors went GA in ChatGPT; Bedrock AgentCore & Vertex Agent Engine are production-ready.
- Execs still ask: who approved that action? Can we audit tool autonomy?
- Switchboard is a personal passion project exploring a control plane answer.

## Slide 2: Architecture snapshot
- LangGraph agent → Switchboard API → policy/approval/audit/adapters.
- Policy engine = OPA (when available) + local fallback.
- Approvals stored persistently; audit events COSE-signed + Rekor compatible.

## Slide 3: Demo storyline
1. `make dev`
2. `make demo-e2e`
3. Approve pending request in Streamlit UI.
4. Run chaos scripts (OPA outage, adapter flap).
5. Inspect Grafana dashboard + audit verification.

## Slide 4: Testing & Confidence
- ruff/black/mypy + pytest + Hypothesis property tests.
- Mutation tests via `make mutation`.
- Chaos scripts to stress connectors/policies.
- Coverage gate at 90%.

## Slide 5: Growth & Community
- Open issue templates, quickstart script, Backstage metadata.
- Labs + newsletters for internal education.
- Invite collaborators: adapters, policy packs, eval harness PRs.

## Slide 6: Call to action
- Clone the repo, run the lab, share feedback.
- Help design next research iteration (Tripwire, Eval harness).
- Celebrate safe autonomy wins! 🚀
