# Repo Hygiene Demo

Demonstrates routing a partner agent request over ACP to perform GitHub hygiene tasks.

## Flow

1. LangGraph agent identifies outdated pull request comments.
2. Switchboard policy engine flags the GitHub write as production-critical and sends it through the ACP adapter (`partner:repo-bot`).
3. Approval is required if the comment touches sensitive repositories; otherwise the action executes immediately.
4. Results are signed and recorded in the transparency log.

To experiment, update the demo agent or craft your own payload:

```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d @examples/payloads/repo_hygiene_request.json
```

Review the audit log and Streamlit UI to observe how ACP routing behaves.
