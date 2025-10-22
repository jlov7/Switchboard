from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ActionSeverity(str, Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


def _now_utc() -> datetime:
    return datetime.now(UTC)


class ActionContext(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    initiated_at: datetime = Field(default_factory=_now_utc)
    agent_id: str
    principal_id: str
    tenant_id: str
    severity: ActionSeverity = ActionSeverity.P1
    sensitivity_tags: list[str] = Field(default_factory=list)
    pii: bool = False
    resource_scope: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("agent_id", "principal_id", "tenant_id", mode="before")
    @classmethod
    def _strip_spaces(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("identifier fields must be strings")
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("identifier cannot be empty")
        return trimmed


class ActionArguments(BaseModel):
    data: dict[str, Any]
    redacted_fields: list[str] = Field(default_factory=list)

    def redacted(self) -> dict[str, Any]:
        """Return arguments with sensitive fields redacted."""
        sanitized = {}
        for key, value in self.data.items():
            sanitized[key] = "***" if key in self.redacted_fields else value
        return sanitized


class ActionRequest(BaseModel):
    context: ActionContext
    tool_name: str
    tool_action: str
    arguments: ActionArguments

    @field_validator("tool_name", "tool_action", mode="before")
    @classmethod
    def _validate_tool(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("tool identifiers must be strings")
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("tool identifiers cannot be empty")
        return trimmed


class PolicyDecision(BaseModel):
    allowed: bool
    requires_approval: bool = False
    reason: str
    policy_ids: list[str] = Field(default_factory=list)
    risk_level: str = "medium"
    expires_at: datetime | None = None


class RouteDecision(BaseModel):
    context: ActionContext
    policy: PolicyDecision
    target_adapter: str
    audit_event_id: UUID


class ApprovalDecision(BaseModel):
    approval_id: UUID = Field(default_factory=uuid4)
    status: ApprovalStatus
    decided_by: str | None = None
    decided_at: datetime | None = None
    notes: str | None = None


class AuditRecord(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=_now_utc)
    request: ActionRequest
    policy_decision: PolicyDecision
    approval: ApprovalDecision | None = None
    signature: str | None = None
    signature_algorithm: str | None = None
    verification_url: str | None = None


class HealthStatus(BaseModel):
    service: str
    status: str
    detail: str | None = None
    checked_at: datetime = Field(default_factory=_now_utc)
