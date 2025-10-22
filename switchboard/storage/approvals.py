from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from switchboard.core.models import ApprovalDecision, ApprovalStatus, AuditRecord, RouteDecision
from switchboard.storage.database import Database, DatabaseConfig


class PersistentApprovalStore:
    """Database-backed approval store so multiple API instances share state."""

    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database(DatabaseConfig.from_env())
        self._ready = False

    async def _ensure_ready(self) -> None:
        if not self._ready:
            await self.database.connect()
            await self.database.ensure_schema()
            self._ready = True

    async def ensure_ready(self) -> None:
        await self._ensure_ready()

    async def disconnect(self) -> None:
        if self._ready:
            await self.database.disconnect()
            self._ready = False

    async def create_pending(self, record: AuditRecord, route: RouteDecision) -> UUID:
        await self._ensure_ready()
        approval = record.approval
        if approval is None:
            approval = ApprovalDecision(approval_id=uuid4(), status=ApprovalStatus.PENDING)
            record.approval = approval
        now = datetime.now(UTC).isoformat()
        await self.database.execute(
            (
                """
            INSERT INTO approvals (
                approval_id, request_json, policy_json, adapter, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
                if self.database.config.dialect == "sqlite"
                else """
            INSERT INTO approvals (
                approval_id, request_json, policy_json, adapter, status,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            ),
            str(approval.approval_id),
            self.database.dumps(record.request.model_dump()),
            self.database.dumps(record.policy_decision.model_dump()),
            route.target_adapter,
            approval.status.value,
            now,
            now,
        )
        await self.database.execute(
            (
                """
            INSERT OR REPLACE INTO audit_cache (event_id, approval_id, record_json, created_at)
            VALUES (?, ?, ?, ?)
            """
                if self.database.config.dialect == "sqlite"
                else """
            INSERT INTO audit_cache (event_id, approval_id, record_json, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (event_id) DO UPDATE SET
                approval_id = EXCLUDED.approval_id,
                record_json = EXCLUDED.record_json,
                created_at = EXCLUDED.created_at
            """
            ),
            str(record.event_id),
            str(approval.approval_id),
            self.database.dumps(record.model_dump()),
            now,
        )
        return approval.approval_id

    async def resolve(
        self,
        approval_id: UUID,
        status: ApprovalStatus,
        decided_by: str,
        notes: str | None = None,
    ) -> tuple[AuditRecord, RouteDecision]:
        await self._ensure_ready()
        now = datetime.now(UTC).isoformat()
        await self.database.execute(
            (
                """
            UPDATE approvals SET status = ?, decided_by = ?, decided_at = ?, notes = ?, updated_at = ?
            WHERE approval_id = ?
            """
                if self.database.config.dialect == "sqlite"
                else """
            UPDATE approvals SET status = $1, decided_by = $2, decided_at = $3, notes = $4, updated_at = $5
            WHERE approval_id = $6
            """
            ),
            status.value,
            decided_by,
            now,
            notes,
            now,
            str(approval_id),
        )
        approval_row = await self.database.fetchone(
            (
                "SELECT request_json, policy_json, adapter FROM approvals WHERE approval_id = ?"
                if self.database.config.dialect == "sqlite"
                else "SELECT request_json, policy_json, adapter FROM approvals WHERE approval_id = $1"
            ),
            str(approval_id),
        )
        if not approval_row:
            raise KeyError(f"Approval {approval_id} not found")

        audit_row = await self.database.fetchone(
            (
                "SELECT record_json FROM audit_cache WHERE approval_id = ?"
                if self.database.config.dialect == "sqlite"
                else "SELECT record_json FROM audit_cache WHERE approval_id = $1"
            ),
            str(approval_id),
        )
        if not audit_row:
            raise KeyError(f"Audit record for approval {approval_id} not found")

        record = AuditRecord.model_validate(self.database.loads(audit_row["record_json"]))
        route = RouteDecision(
            context=record.request.context,
            policy=record.policy_decision,
            target_adapter=approval_row["adapter"],
            audit_event_id=record.event_id,
        )
        if record.approval is None:
            record.approval = ApprovalDecision(approval_id=approval_id, status=status)
        record.approval.status = status
        record.approval.decided_by = decided_by
        record.approval.decided_at = datetime.now(UTC)
        record.approval.notes = notes
        return record, route

    async def get(self, approval_id: UUID) -> AuditRecord | None:
        await self._ensure_ready()
        row = await self.database.fetchone(
            (
                "SELECT record_json FROM audit_cache WHERE approval_id = ?"
                if self.database.config.dialect == "sqlite"
                else "SELECT record_json FROM audit_cache WHERE approval_id = $1"
            ),
            str(approval_id),
        )
        if not row:
            return None
        return AuditRecord.model_validate(self.database.loads(row["record_json"]))

    async def pending_details(self) -> dict[UUID, tuple[AuditRecord, RouteDecision]]:
        await self._ensure_ready()
        rows = await self.database.fetchall(
            (
                "SELECT approval_id, adapter FROM approvals WHERE status = ?"
                if self.database.config.dialect == "sqlite"
                else "SELECT approval_id, adapter FROM approvals WHERE status = $1"
            ),
            ApprovalStatus.PENDING.value,
        )
        pending: dict[UUID, tuple[AuditRecord, RouteDecision]] = {}
        for row in rows:
            approval_id = UUID(row["approval_id"])
            record = await self.get(approval_id)
            if not record:
                continue
            route = RouteDecision(
                context=record.request.context,
                policy=record.policy_decision,
                target_adapter=row["adapter"],
                audit_event_id=record.event_id,
            )
            pending[approval_id] = (record, route)
        return pending
