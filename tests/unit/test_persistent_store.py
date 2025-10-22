from __future__ import annotations

from uuid import UUID

import pytest

from switchboard.core.models import (
    ActionArguments,
    ActionContext,
    ActionRequest,
    ActionSeverity,
    ApprovalStatus,
    AuditRecord,
    PolicyDecision,
    RouteDecision,
)
from switchboard.storage.approvals import PersistentApprovalStore


def _build_audit_record() -> AuditRecord:
    request = ActionRequest(
        context=ActionContext(
            agent_id="agent",
            principal_id="user",
            tenant_id="tenant",
            severity=ActionSeverity.P1,
            metadata={"role": "ops"},
        ),
        tool_name="jira",
        tool_action="create_issue",
        arguments=ActionArguments(data={"foo": "bar"}),
    )
    policy = PolicyDecision(allowed=True, requires_approval=True, reason="needs approval")
    return AuditRecord(request=request, policy_decision=policy)


@pytest.mark.asyncio
async def test_persistent_store_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWITCHBOARD_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    store = PersistentApprovalStore()
    record = _build_audit_record()
    route = RouteDecision(
        context=record.request.context,
        policy=record.policy_decision,
        target_adapter="mcp",
        audit_event_id=record.event_id,
    )
    approval_id = await store.create_pending(record, route)
    assert isinstance(approval_id, UUID)

    pending = await store.pending_details()
    assert approval_id in pending

    fetched = await store.get(approval_id)
    assert fetched is not None
    assert fetched.request.tool_name == "jira"

    updated_record, updated_route = await store.resolve(
        approval_id=approval_id,
        status=ApprovalStatus.APPROVED,
        decided_by="tester",
    )
    assert updated_record.approval is not None
    assert updated_record.approval.status == ApprovalStatus.APPROVED
    assert updated_route.target_adapter == "mcp"

    await store.database.disconnect()
