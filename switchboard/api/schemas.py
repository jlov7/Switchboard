from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from switchboard.core.models import ActionRequest, ApprovalStatus, AuditRecord, PolicyDecision


class RouteRequest(BaseModel):
    request: ActionRequest


class RouteResponse(BaseModel):
    result: str
    detail: str
    adapter: str
    policy: PolicyDecision
    response: dict[str, Any] = Field(default_factory=dict)


class ApprovalActionRequest(BaseModel):
    approval_id: UUID
    status: ApprovalStatus
    decided_by: str
    notes: str | None = None


class PolicyCheckRequest(BaseModel):
    request: ActionRequest


class PolicyCheckResponse(BaseModel):
    policy: PolicyDecision


class AuditVerifyRequest(BaseModel):
    record: AuditRecord
    verify_rekor: bool = True


class AuditVerifyResponse(BaseModel):
    verified: bool
    signature_valid: bool
    rekor_included: bool | None = None
    failure_reason: str | None = None
