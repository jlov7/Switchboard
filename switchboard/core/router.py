from __future__ import annotations

import asyncio
import os

import structlog

from switchboard.adapters.acp.client import ACPAdapter
from switchboard.adapters.aws import BedrockAgentCoreAdapter
from switchboard.adapters.base import AdapterResult, BaseAdapter
from switchboard.adapters.google import VertexAgentEngineAdapter
from switchboard.adapters.mcp.client import MCPAdapter
from switchboard.audit.service import AuditService
from switchboard.core.approvals import ActionBlocked, ApprovalRequired, ApprovalStore
from switchboard.core.logging import redact_args
from switchboard.core.models import (
    ActionRequest,
    AuditRecord,
    PolicyDecision,
    RouteDecision,
)
from switchboard.policy.engine import PolicyEngine

logger = structlog.get_logger(__name__)


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, BaseAdapter] = {}

    def register(self, key: str, adapter: BaseAdapter) -> None:
        self._adapters[key] = adapter

    def get(self, key: str) -> BaseAdapter:
        if key not in self._adapters:
            raise KeyError(f"No adapter registered for key={key}")
        return self._adapters[key]

    async def aclose(self) -> None:
        for adapter in self._adapters.values():
            aclose = getattr(adapter, "aclose", None)
            if aclose:
                await aclose()


class ActionRouter:
    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        audit_service: AuditService | None = None,
        adapter_registry: AdapterRegistry | None = None,
        approvals: ApprovalStore | None = None,
    ) -> None:
        self.policy_engine = policy_engine or PolicyEngine()
        self.audit_service = audit_service or AuditService()
        self.adapter_registry = adapter_registry or AdapterRegistry()
        self.approvals = approvals or ApprovalStore()
        self._register_default_adapters()
        self._adapter_locks: dict[str, asyncio.Lock] = {}

    def _register_default_adapters(self) -> None:
        if not self.adapter_registry._adapters:
            self.adapter_registry.register("mcp", MCPAdapter())
            self.adapter_registry.register("acp", ACPAdapter())
            if os.getenv("SWITCHBOARD_ENABLE_BEDROCK", "false").lower() == "true":
                self.adapter_registry.register("bedrock", BedrockAgentCoreAdapter())
            if os.getenv("SWITCHBOARD_ENABLE_VERTEX", "false").lower() == "true":
                self.adapter_registry.register("vertex", VertexAgentEngineAdapter())

    async def route(self, request: ActionRequest) -> tuple[AdapterResult, PolicyDecision]:
        policy = await self.policy_engine.evaluate(request)
        audit_record = AuditRecord(request=request, policy_decision=policy)
        await self.audit_service.record(audit_record)

        route_decision = RouteDecision(
            context=request.context,
            policy=policy,
            target_adapter=self._determine_adapter(request),
            audit_event_id=audit_record.event_id,
        )

        redacted = redact_args(request.arguments.data, request.arguments.redacted_fields)
        logger.info(
            "route_decision",
            request_id=str(request.context.request_id),
            adapter=route_decision.target_adapter,
            allowed=policy.allowed,
            requires_approval=policy.requires_approval,
            policy_ids=policy.policy_ids,
            args=redacted,
        )

        if not policy.allowed:
            raise ActionBlocked(route_decision)

        if policy.requires_approval:
            approval_id = await self.approvals.create_pending(audit_record, route_decision)
            raise ApprovalRequired(route_decision, approval_id)

        result = await self.execute_adapter(route_decision.target_adapter, request)
        return result, policy

    def _determine_adapter(self, request: ActionRequest) -> str:
        if request.tool_name.startswith("partner:"):
            return "acp"
        if request.tool_name.startswith("bedrock:"):
            return "bedrock"
        if request.tool_name.startswith("vertex:"):
            return "vertex"
        return "mcp"

    def _lock_for_adapter(self, adapter_name: str) -> asyncio.Lock:
        lock = self._adapter_locks.get(adapter_name)
        if lock is None:
            lock = asyncio.Lock()
            self._adapter_locks[adapter_name] = lock
        return lock

    async def execute_adapter(self, adapter_name: str, request: ActionRequest) -> AdapterResult:
        adapter = self.adapter_registry.get(adapter_name)
        async with self._lock_for_adapter(adapter_name):
            return await adapter.execute_action(request)
