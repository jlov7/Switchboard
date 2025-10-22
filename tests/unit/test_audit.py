from __future__ import annotations

from pathlib import Path

import pytest

from switchboard.audit.service import AuditService
from switchboard.core.models import (
    ActionArguments,
    ActionContext,
    ActionRequest,
    ActionSeverity,
    AuditRecord,
    PolicyDecision,
)


def build_audit_record() -> AuditRecord:
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
    policy = PolicyDecision(allowed=True, requires_approval=False, reason="ok")
    return AuditRecord(request=request, policy_decision=policy)


@pytest.mark.asyncio
async def test_audit_signature_roundtrip(tmp_path: Path) -> None:
    service = AuditService(output_path=tmp_path / "audit.jsonl")
    record = build_audit_record()
    stored = await service.record(record)
    assert stored.signature is not None
    assert stored.signature_algorithm is not None
    assert await service.verify(stored) is True
