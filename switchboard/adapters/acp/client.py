from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from switchboard.adapters.base import AdapterResult, BaseAdapter
from switchboard.core.models import ActionRequest


class ACPResponse(BaseModel):
    accepted: bool
    detail: str
    data: dict[str, Any] = {}


class ACPAdapter(BaseAdapter):
    def __init__(self, name: str = "acp") -> None:
        super().__init__(name=name)
        self.endpoint = os.getenv("ACP_ENDPOINT", "http://localhost:8082")
        self._client = httpx.AsyncClient(base_url=self.endpoint, timeout=10.0)

    async def execute_action(self, request: ActionRequest) -> AdapterResult:
        payload = {
            "request_id": str(request.context.request_id),
            "from_agent": request.context.agent_id,
            "tool": request.tool_name,
            "action": request.tool_action,
            "arguments": request.arguments.data,
            "metadata": request.context.metadata,
        }
        response = await self._client.post("/forward", json=payload)
        response.raise_for_status()
        try:
            parsed = ACPResponse.model_validate(response.json())
        except ValidationError as exc:
            raise ValueError(f"Invalid response from ACP endpoint: {exc}") from exc
        return AdapterResult(success=parsed.accepted, detail=parsed.detail, response=parsed.data)

    async def aclose(self) -> None:
        await self._client.aclose()
