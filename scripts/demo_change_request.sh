#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"

echo "1) Allowed action"
curl -s "${API_URL}/route" \
  -H "Content-Type: application/json" \
  -d @- <<'EOF' | jq
{
  "request": {
    "context": {
      "agent_id": "demo-agent",
      "principal_id": "user-123",
      "tenant_id": "demo",
      "severity": "p1",
      "metadata": {"role": "ops"},
      "sensitivity_tags": []
    },
    "tool_name": "jira",
    "tool_action": "create_issue",
    "arguments": {
      "data": {"project": "SW", "summary": "Allowed action"},
      "redacted_fields": []
    }
  }
}
EOF

echo "2) Needs approval"
PENDING=$(curl -s -w "\n%{http_code}" "${API_URL}/route" \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "request": {
    "context": {
      "agent_id": "demo-agent",
      "principal_id": "user-123",
      "tenant_id": "demo",
      "severity": "p1",
      "pii": true,
      "metadata": {"role": "ops"},
      "sensitivity_tags": ["financial"]
    },
    "tool_name": "jira",
    "tool_action": "update_issue",
    "arguments": {
      "data": {"issue_key": "SW-123", "fields": {"description": "Contains PII"}},
      "redacted_fields": ["description"]
    }
  }
}
EOF
)

BODY=$(echo "$PENDING" | head -n -1)
STATUS=$(echo "$PENDING" | tail -n1)
echo "$BODY" | jq
if [[ "$STATUS" == "202" ]]; then
  APPROVAL_ID=$(echo "$BODY" | jq -r '.approval_id')
  echo "Auto-approving $APPROVAL_ID"
  curl -s "${API_URL}/approve" \
    -H "Content-Type: application/json" \
    -d "{\"approval_id\":\"$APPROVAL_ID\",\"status\":\"approved\",\"decided_by\":\"demo\"}" | jq
fi

echo "3) Blocked"
HTTP_CODE=$(curl -s -o /tmp/blocked.txt -w "%{http_code}" "${API_URL}/route" \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "request": {
    "context": {
      "agent_id": "demo-agent",
      "principal_id": "user-123",
      "tenant_id": "demo",
      "severity": "p0",
      "resource_scope": "prod",
      "metadata": {"role": "analyst"}
    },
    "tool_name": "jira",
    "tool_action": "update_issue",
    "arguments": {
      "data": {"issue_key": "SW-123", "fields": {"status": "Closed"}},
      "redacted_fields": []
    }
  }
}
EOF
)
cat /tmp/blocked.txt | jq
echo "HTTP status: $HTTP_CODE"
