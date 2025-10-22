from __future__ import annotations

from typing import Any

import pytest

from switchboard.adapters.base import AdapterResult, BaseAdapter
from switchboard.audit.service import AuditService
from switchboard.core.approvals import ActionBlocked, ApprovalRequired, ApprovalStore
from switchboard.core.models import (
    ActionArguments,
    ActionContext,
    ActionRequest,
    ActionSeverity,
)
from switchboard.core.router import ActionRouter, AdapterRegistry
from switchboard.policy.engine import PolicyEngine


class StubAdapter(BaseAdapter):
    async def execute_action(self, request: ActionRequest) -> AdapterResult:
        return AdapterResult(success=True, detail="stub", response={"echo": request.tool_action})


def build_request(**overrides: Any) -> ActionRequest:
    context = ActionContext(
        agent_id="agent",
        principal_id="user",
        tenant_id="tenant",
        severity=overrides.get("severity", ActionSeverity.P1),
        resource_scope=overrides.get("resource_scope"),
        pii=overrides.get("pii", False),
        sensitivity_tags=overrides.get("sensitivity_tags", []),
        metadata=overrides.get("metadata", {"role": "ops"}),
    )
    return ActionRequest(
        context=context,
        tool_name=overrides.get("tool_name", "jira"),
        tool_action=overrides.get("tool_action", "create_issue"),
        arguments=ActionArguments(data={"foo": "bar"}),
    )


@pytest.fixture(autouse=True)
def disable_opa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWITCHBOARD_USE_OPA", "false")
    monkeypatch.setenv("SWITCHBOARD_APPROVAL_BACKEND", "memory")


@pytest.mark.asyncio
async def test_router_executes_allowed_action() -> None:
    registry = AdapterRegistry()
    registry.register("mcp", StubAdapter("mcp"))
    router = ActionRouter(
        policy_engine=PolicyEngine(),
        audit_service=AuditService(),
        adapter_registry=registry,
        approvals=ApprovalStore(backend="memory"),
    )

    result, policy = await router.route(build_request())
    assert result.success is True
    assert policy.allowed is True


@pytest.mark.asyncio
async def test_router_requires_approval() -> None:
    registry = AdapterRegistry()
    registry.register("mcp", StubAdapter("mcp"))
    router = ActionRouter(
        policy_engine=PolicyEngine(),
        audit_service=AuditService(),
        adapter_registry=registry,
        approvals=ApprovalStore(backend="memory"),
    )
    with pytest.raises(ApprovalRequired):
        await router.route(build_request(pii=True))


@pytest.mark.asyncio
async def test_router_blocks_action() -> None:
    registry = AdapterRegistry()
    registry.register("mcp", StubAdapter("mcp"))
    router = ActionRouter(
        policy_engine=PolicyEngine(),
        audit_service=AuditService(),
        adapter_registry=registry,
        approvals=ApprovalStore(backend="memory"),
    )
    with pytest.raises(ActionBlocked):
        await router.route(build_request(resource_scope="prod", metadata={"role": "analyst"}))
