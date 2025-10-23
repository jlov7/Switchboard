from __future__ import annotations

from uuid import uuid4

from switchboard.audit.receipt import build_receipt, receipt_to_json
from switchboard.audit.service import AuditVerificationResult
from switchboard.core.models import (
    ActionArguments,
    ActionContext,
    ActionRequest,
    ActionSeverity,
    AuditRecord,
    PolicyDecision,
)


def _record() -> AuditRecord:
    request = ActionRequest(
        context=ActionContext(
            agent_id="agent",
            principal_id="user",
            tenant_id="tenant",
            severity=ActionSeverity.P1,
        ),
        tool_name="jira",
        tool_action="create_issue",
        arguments=ActionArguments(data={"foo": "bar"}),
    )
    policy = PolicyDecision(allowed=True, requires_approval=False, reason="ok")
    return AuditRecord(request=request, policy_decision=policy)


def test_build_receipt_includes_defaults() -> None:
    record = _record()
    result = AuditVerificationResult(signature_valid=True, rekor_included=None, failure_reason=None)
    receipt = build_receipt(record, result)
    assert receipt["audit_event"] == str(record.event_id)
    assert receipt["verified"] is True
    assert receipt["signature_valid"] is True
    assert receipt["rekor_included"] is None
    assert receipt["failure_reason"] is None
    assert receipt["verification_reference"] is None


def test_build_receipt_can_drop_reference() -> None:
    record = _record()
    result = AuditVerificationResult(signature_valid=False, rekor_included=False, failure_reason="bad")
    receipt = build_receipt(record, result, include_rekor_reference=False)
    assert "verification_reference" not in receipt
    assert receipt["verified"] is False
    assert receipt["failure_reason"] == "bad"


def test_receipt_to_json_sorted_keys() -> None:
    receipt = {
        "b": 2,
        "a": 1,
    }
    json_output = receipt_to_json(receipt)
    assert json_output == '{"a":1,"b":2}'
