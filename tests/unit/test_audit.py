from __future__ import annotations

from pathlib import Path

import pytest

from switchboard.audit.rekor_client import RekorError
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


class _StubRekorClient:
    def __init__(self, verify_result: bool = True, raise_error: bool = False) -> None:
        self.logged_payloads: list[dict] = []
        self.verified_entries: list[str] = []
        self.verify_result = verify_result
        self.raise_error = raise_error

    async def log_entry(self, payload: dict) -> str:
        self.logged_payloads.append(payload)
        return "entry-123"

    async def verify_entry(self, entry_id: str) -> bool:
        self.verified_entries.append(entry_id)
        assert entry_id == "entry-123"
        if self.raise_error:
            raise RekorError("simulated Rekor outage")
        return self.verify_result


@pytest.mark.asyncio
async def test_audit_signature_roundtrip(tmp_path: Path) -> None:
    service = AuditService(output_path=tmp_path / "audit.jsonl")
    record = build_audit_record()
    stored = await service.record(record)
    assert stored.signature is not None
    assert stored.signature_algorithm is not None
    verification = await service.verify(stored)
    assert verification.signature_valid is True
    assert verification.verified is True
    assert verification.failure_reason is None


@pytest.mark.asyncio
async def test_audit_verify_checks_rekor(tmp_path: Path) -> None:
    rekor = _StubRekorClient()
    service = AuditService(
        output_path=tmp_path / "audit.jsonl",
        rekor_client=rekor,
    )
    record = build_audit_record()
    stored = await service.record(record)
    verification = await service.verify(stored)
    assert verification.signature_valid is True
    assert verification.rekor_included is True
    assert verification.verified is True
    assert rekor.verified_entries == ["entry-123"]
    assert verification.failure_reason is None


@pytest.mark.asyncio
async def test_audit_verify_can_skip_rekor(tmp_path: Path) -> None:
    rekor = _StubRekorClient()
    service = AuditService(
        output_path=tmp_path / "audit.jsonl",
        rekor_client=rekor,
    )
    record = build_audit_record()
    stored = await service.record(record)
    verification = await service.verify(stored, verify_rekor=False)
    assert verification.signature_valid is True
    assert verification.rekor_included is None
    assert verification.verified is True
    assert rekor.verified_entries == []
    assert verification.failure_reason is None


@pytest.mark.asyncio
async def test_audit_verify_missing_signature_sets_reason(tmp_path: Path) -> None:
    service = AuditService(output_path=tmp_path / "audit.jsonl")
    record = build_audit_record()
    verification = await service.verify(record)
    assert verification.signature_valid is False
    assert verification.verified is False
    assert verification.failure_reason == "Audit record is missing signature metadata"


@pytest.mark.asyncio
async def test_audit_verify_rekor_negative_sets_reason(tmp_path: Path) -> None:
    rekor = _StubRekorClient(verify_result=False)
    service = AuditService(
        output_path=tmp_path / "audit.jsonl",
        rekor_client=rekor,
    )
    stored = await service.record(build_audit_record())
    verification = await service.verify(stored)
    assert verification.signature_valid is True
    assert verification.rekor_included is False
    assert verification.verified is False
    assert verification.failure_reason == "Rekor inclusion could not be confirmed"


@pytest.mark.asyncio
async def test_audit_verify_rekor_exception_sets_reason(tmp_path: Path) -> None:
    rekor = _StubRekorClient(raise_error=True)
    service = AuditService(
        output_path=tmp_path / "audit.jsonl",
        rekor_client=rekor,
    )
    stored = await service.record(build_audit_record())
    verification = await service.verify(stored)
    assert verification.signature_valid is True
    assert verification.rekor_included is False
    assert verification.verified is False
    assert verification.failure_reason is not None
    assert verification.failure_reason.startswith("Rekor verification failed:")
