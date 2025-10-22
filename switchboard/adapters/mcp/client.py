from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from switchboard.adapters.base import AdapterResult, BaseAdapter
from switchboard.core.models import ActionRequest


class MCPResponse(BaseModel):
    ok: bool
    detail: str
    data: dict[str, Any] = {}


class MCPAdapter(BaseAdapter):
    def __init__(self, name: str = "mcp") -> None:
        super().__init__(name=name)
        self.base_url = os.getenv("MCP_SERVER_URL", "http://localhost:8081")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def execute_action(self, request: ActionRequest) -> AdapterResult:
        payload = {
            "request_id": str(request.context.request_id),
            "tool": request.tool_name,
            "action": request.tool_action,
            "arguments": request.arguments.data,
            "context": request.context.model_dump(),
        }
        response = await self._client.post("/actions", json=payload)
        response.raise_for_status()
        try:
            parsed = MCPResponse.model_validate(response.json())
        except ValidationError as exc:
            raise ValueError(f"Invalid response from MCP server: {exc}") from exc
        return AdapterResult(success=parsed.ok, detail=parsed.detail, response=parsed.data)

    async def aclose(self) -> None:
        await self._client.aclose()
