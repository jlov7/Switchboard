# Switchboard Poster

```
┌──────────────────────────────────────────────┐
│   SWITCHBOARD — GOVERNING TOOL-USES          │
├──────────────────────────────────────────────┤
│ Agents → Switchboard API → Policies → Tools  │
│                                              │
│  ROUTE   ┌───────────┐   APPROVE             │
│          │ Policy    │   • OPA + fallback    │
│          │ Engine    │   • Streamlit queue   │
│          └─────┬─────┘                       │
│                │                              │
│         ┌──────▼──────┐   PROVE              │
│         │ Audit Trail │   • COSE signatures  │
│         │ Rekor/JSONL │   • Verify script    │
│         └──────▲──────┘                      │
│                │                              │
│          ┌─────┴─────┐   ADAPTERS            │
│          │ MCP / ACP │   • Bedrock (dry)     │
│          │ Vertex    │   • Chaos-ready       │
└──────────────────────────────────────────────┘
```

Use this visual in presentations or docs to explain the flow at a glance.
