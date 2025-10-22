from __future__ import annotations

import json
from typing import Any

import httpx

from switchboard.core.models import ActionRequest, PolicyDecision


class OPAError(Exception):
    pass


class OPAClient:
    def __init__(self, url: str) -> None:
        self.url = url
        self._client = httpx.AsyncClient(timeout=5.0)

    async def evaluate(self, request: ActionRequest) -> PolicyDecision:
        payload: dict[str, Any] = {
            "input": {
                "context": request.context.model_dump(),
                "request": {
                    "tool_name": request.tool_name,
                    "tool_action": request.tool_action,
                    "arguments": request.arguments.data,
                },
                "activity": {"window_count": 0},
                "policy": {"rate_limit": 0},
            }
        }
        response = await self._client.post(self.url, content=json.dumps(payload, default=str))
        if response.status_code >= 400:
            raise OPAError(f"OPA error {response.status_code}: {response.text}")
        data = response.json()
        result = data.get("result")
        if result is None:
            raise OPAError("OPA response missing result")
        allowed = bool(result.get("allow", False))
        requires_approval = bool(result.get("requires_approval", False))
        reason = result.get("reason", "allowed" if allowed else "denied")
        policy_ids = result.get("policy_ids", [])
        risk_level = result.get("risk_level", "medium")
        return PolicyDecision(
            allowed=allowed,
            requires_approval=requires_approval,
            reason=reason,
            policy_ids=policy_ids,
            risk_level=risk_level,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
