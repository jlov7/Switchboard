from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from switchboard.api.schemas import (
    ApprovalActionRequest,
    AuditVerifyRequest,
    PolicyCheckRequest,
    PolicyCheckResponse,
    RouteRequest,
    RouteResponse,
)
from switchboard.audit.service import AuditService
from switchboard.core.approvals import ActionBlocked, ApprovalRequired, ApprovalStore
from switchboard.core.logging import configure_logging
from switchboard.core.models import (
    ApprovalStatus,
    HealthStatus,
)
from switchboard.core.router import ActionRouter, AdapterRegistry
from switchboard.policy.engine import PolicyEngine
from switchboard.telemetry.setup import configure_telemetry

configure_logging()
configure_telemetry()

app = FastAPI(title="Switchboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_router() -> ActionRouter:
    policy_engine = PolicyEngine()
    audit_service = AuditService()
    adapter_registry = AdapterRegistry()
    approvals = ApprovalStore()
    return ActionRouter(
        policy_engine=policy_engine,
        audit_service=audit_service,
        adapter_registry=adapter_registry,
        approvals=approvals,
    )


router_dependency = get_router()
lock = asyncio.Lock()


@app.on_event("startup")
async def startup() -> None:
    await router_dependency.approvals.warmup()


@app.on_event("shutdown")
async def shutdown() -> None:
    await router_dependency.approvals.shutdown()
    await router_dependency.adapter_registry.aclose()


@app.post("/route", response_model=RouteResponse)
async def route_action(payload: RouteRequest) -> Any:
    try:
        result, policy = await router_dependency.route(payload.request)
        return RouteResponse(
            result="executed",
            detail=result.detail,
            adapter=router_dependency._determine_adapter(payload.request),
            policy=policy,
            response=result.response,
        )
    except ApprovalRequired as exc:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "result": "pending_approval",
                "approval_id": str(exc.approval_id),
                "detail": exc.decision.policy.reason,
                "approval_required": True,
                "policy": exc.decision.policy.model_dump(),
                "adapter": exc.decision.target_adapter,
            },
        )
    except ActionBlocked as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "result": "blocked",
                "policy": exc.decision.policy.model_dump(),
                "adapter": exc.decision.target_adapter,
            },
        ) from exc


@app.post("/approve")
async def approve_action(
    payload: ApprovalActionRequest,
) -> Any:
    if payload.status == ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Cannot transition to pending")
    record = await router_dependency.approvals.get(payload.approval_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval request not found")
    audit_record, decision = await router_dependency.approvals.resolve(
        approval_id=payload.approval_id,
        status=payload.status,
        decided_by=payload.decided_by,
        notes=payload.notes,
    )
    if payload.status == ApprovalStatus.DENIED:
        return {"result": "denied", "approval_id": str(payload.approval_id)}

    adapter = router_dependency.adapter_registry.get(decision.target_adapter)
    async with lock:
        result = await adapter.execute_action(audit_record.request)
    return {
        "result": "executed",
        "detail": result.detail,
        "adapter": decision.target_adapter,
        "approval_id": str(payload.approval_id),
    }


@app.post("/policy/check", response_model=PolicyCheckResponse)
async def policy_check(payload: PolicyCheckRequest) -> PolicyCheckResponse:
    decision = await router_dependency.policy_engine.evaluate(payload.request)
    return PolicyCheckResponse(policy=decision)


@app.get("/approvals/pending")
async def approvals_pending() -> Any:
    pending = await router_dependency.approvals.pending_details()
    return [
        {
            "approval_id": str(approval_id),
            "request": record.request.model_dump(),
            "policy": record.policy_decision.model_dump(),
            "adapter": route.target_adapter,
        }
        for approval_id, (record, route) in pending.items()
    ]


@app.post("/audit/verify")
async def audit_verify(payload: AuditVerifyRequest) -> Any:
    valid = await router_dependency.audit_service.verify(payload.record)
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return {"result": "verified"}


@app.get("/healthz", response_model=HealthStatus)
async def healthz() -> HealthStatus:
    return HealthStatus(service="switchboard-api", status="ok")
