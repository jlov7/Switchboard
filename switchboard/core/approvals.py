from __future__ import annotations

import asyncio
import os
from uuid import UUID, uuid4

from switchboard.core.models import ApprovalDecision, ApprovalStatus, AuditRecord, RouteDecision
from switchboard.storage.approvals import PersistentApprovalStore


class ApprovalStore:
    def __init__(self, backend: str | None = None) -> None:
        env_backend = os.getenv("SWITCHBOARD_APPROVAL_BACKEND")
        self._backend = (backend or env_backend or "memory").lower()
        self._pending: dict[UUID, tuple[AuditRecord, RouteDecision]] = {}
        self._lock = asyncio.Lock()
        self._persistent: PersistentApprovalStore | None = None
        if self._backend == "persistent":
            self._persistent = PersistentApprovalStore()

    async def create_pending(self, audit_record: AuditRecord, route: RouteDecision) -> UUID:
        approval = audit_record.approval
        if approval is None:
            approval = ApprovalDecision(approval_id=uuid4(), status=ApprovalStatus.PENDING)
            audit_record.approval = approval

        if self._persistent:
            return await self._persistent.create_pending(audit_record, route)

        async with self._lock:
            self._pending[approval.approval_id] = (audit_record, route)
            return approval.approval_id

    async def resolve(
        self, approval_id: UUID, status: ApprovalStatus, decided_by: str, notes: str | None = None
    ) -> tuple[AuditRecord, RouteDecision]:
        if self._persistent:
            return await self._persistent.resolve(
                approval_id=approval_id, status=status, decided_by=decided_by, notes=notes
            )

        async with self._lock:
            audit_record, route = self._pending.pop(approval_id)
            audit_record.approval = ApprovalDecision(
                approval_id=approval_id,
                status=status,
                decided_by=decided_by,
                notes=notes,
            )
            return audit_record, route

    async def get(self, approval_id: UUID) -> AuditRecord | None:
        if self._persistent:
            return await self._persistent.get(approval_id)

        async with self._lock:
            item = self._pending.get(approval_id)
            return item[0] if item else None

    async def pending_items(self) -> dict[UUID, AuditRecord]:
        if self._persistent:
            pending = await self._persistent.pending_details()
            return {key: value[0] for key, value in pending.items()}

        async with self._lock:
            return {key: value[0] for key, value in self._pending.items()}

    async def pending_details(self) -> dict[UUID, tuple[AuditRecord, RouteDecision]]:
        if self._persistent:
            return await self._persistent.pending_details()

        async with self._lock:
            return dict(self._pending)

    async def warmup(self) -> None:
        if self._persistent:
            await self._persistent.ensure_ready()

    async def shutdown(self) -> None:
        if self._persistent:
            await self._persistent.disconnect()


class ApprovalRequired(Exception):
    def __init__(self, decision: RouteDecision, approval_id: UUID) -> None:
        super().__init__("Approval required")
        self.decision = decision
        self.approval_id = approval_id


class ActionBlocked(Exception):
    def __init__(self, decision: RouteDecision) -> None:
        super().__init__("Action denied by policy")
        self.decision = decision
