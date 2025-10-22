from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

import pytest
from httpx import ASGITransport, AsyncClient

from switchboard.adapters.base import AdapterResult, BaseAdapter
from switchboard.api.main import app, build_router, set_app_router
from switchboard.core.models import ActionRequest, ActionSeverity


class StubAdapter(BaseAdapter):
    async def execute_action(self, _request: ActionRequest) -> AdapterResult:
        return AdapterResult(success=True, detail="stub", response={"ok": True})


@pytest.fixture(autouse=True)
def setup_router(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("SWITCHBOARD_USE_OPA", "false")
    monkeypatch.setenv("SWITCHBOARD_APPROVAL_BACKEND", "memory")
    monkeypatch.setenv("SWITCHBOARD_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    router = build_router()
    router.adapter_registry._adapters = {}
    router.adapter_registry.register("mcp", StubAdapter("mcp"))
    set_app_router(router)
    yield
    set_app_router(None)


@pytest.mark.asyncio
async def test_route_lifecycle() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload: dict[str, Any] = {
            "request": {
                "context": {
                    "agent_id": "agent",
                    "principal_id": "user",
                    "tenant_id": "tenant",
                    "severity": ActionSeverity.P1.value,
                    "metadata": {"role": "ops"},
                },
                "tool_name": "jira",
                "tool_action": "create_issue",
                "arguments": {"data": {"foo": "bar"}, "redacted_fields": []},
            }
        }
        response = await client.post("/route", json=payload)
        assert response.status_code == 200

        context = cast(dict[str, Any], payload["request"]["context"])
        context["pii"] = True
        context["sensitivity_tags"] = ["financial"]
        response = await client.post("/route", json=payload)
        assert response.status_code == 202
        approval_id = response.json()["approval_id"]

        approve = await client.post(
            "/approve",
            json={
                "approval_id": approval_id,
                "status": "approved",
                "decided_by": "tester",
            },
        )
        assert approve.status_code == 200

        metadata = cast(dict[str, Any], context["metadata"])
        context["resource_scope"] = "prod"
        metadata["role"] = "analyst"
        context["severity"] = ActionSeverity.P0.value
        response = await client.post("/route", json=payload)
        assert response.status_code == 403
