# Growth & Media Playbook

Ready-to-share assets to help others discover the Switchboard research project.

## Elevator Pitch

> "Switchboard is my passion project on governing MCP/ACP agent actions with policy-as-code and signed provenance. Think approvals + audit + adapters for Bedrock, Vertex, and LangGraph in one control plane."

## Shareable Snippets

1. **Micro-post (58 words)** – already drafted in the repo root; add fresh links or GIFs.
1. **Builder’s Log** – extended narrative in `docs/OVERVIEW.md`.
1. **Conference Abstract** –
   - *Title*: "Switchboard: A Policy-First Control Plane for Tool-Using Agents"
   - *Angle*: Research learnings on approvals, provenance, and multi-cloud adapters.

## Demo Flow (10 minutes)

1. Frame the research hypothesis (Why now, signals, risks).
1. `make dev` and `make demo-e2e` live – narrate allowed vs approval vs blocked.
1. Open Streamlit approvals UI, approve the pending request.
1. Tail the signed audit log and show `make audit-verify` output.
1. (Optional) Flip on Bedrock/Vertex adapters in dry-run mode to show extensibility.

## Visual & Media Tips

- Use Mermaid diagrams (see `docs/ARCHITECTURE.md`) or export via https://mermaid.live
- Record terminal demos with `asciinema`:
  ```bash
  asciinema rec demos/switchboard.cast --command "make demo-e2e"
  ```
- Screenshot the Streamlit queue with high-contrast theme enabled.

## Metrics to Highlight

- Block rate vs false blocks (from evaluation harness).
- Approval latency (p95) using OTEL traces.
- Provenance verification success rate (`make audit-verify`).

## Calls to Action

- Invite collaborators to add adapters (ServiceNow, Slack approvals, Bedrock live recipes).
- Encourage policy contributions (SoD templates, PII tag packs).
- Ask auditors/compliance folks for feedback on evidence exports.

Share responsibly: remind audiences this is a research sandbox, not supported software.

## New Assets

- Lab: docs/labs/change_request_lab.md
- Talk: docs/TALK_TRACK.md
- Newsletter template: docs/NEWSLETTER_TEMPLATE.md
- GitHub Action `.github/workflows/newsletter.yml` renders templated dispatches (artifact output)
- Release notes: docs/RELEASE_NOTES_0.2.md
