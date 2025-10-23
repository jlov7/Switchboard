from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from switchboard.api.schemas import (
    ApprovalActionRequest,
    AuditVerifyRequest,
    AuditVerifyResponse,
    PolicyCheckRequest,
    PolicyCheckResponse,
    RouteRequest,
    RouteResponse,
)
from switchboard.audit.service import AuditService
from switchboard.core.approvals import ActionBlocked, ApprovalRequired, ApprovalStore
from switchboard.core.logging import configure_logging
from switchboard.core.models import ApprovalStatus, HealthStatus
from switchboard.core.router import ActionRouter, AdapterRegistry
from switchboard.policy.engine import PolicyEngine
from switchboard.telemetry.setup import TelemetryController, configure_telemetry


def build_router() -> ActionRouter:
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


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    telemetry: TelemetryController | None = configure_telemetry()

    router = cast(ActionRouter | None, getattr(application.state, "router", None))
    if router is None:
        router = build_router()
        application.state.router = router

    await router.approvals.warmup()
    try:
        yield
    finally:
        await router.approvals.shutdown()
        await router.adapter_registry.aclose()
        if telemetry:
            telemetry.shutdown()


app = FastAPI(title="Switchboard API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def set_app_router(router: ActionRouter | None) -> None:
    if router is None:
        if hasattr(app.state, "router"):
            delattr(app.state, "router")
        return
    app.state.router = router


def get_app_router() -> ActionRouter:
    router = getattr(app.state, "router", None)
    if router is None:
        router = build_router()
        app.state.router = router
    return cast(ActionRouter, router)


@app.post("/route", response_model=RouteResponse)
async def route_action(payload: RouteRequest) -> Any:
    router = get_app_router()
    try:
        result, policy = await router.route(payload.request)
        return RouteResponse(
            result="executed",
            detail=result.detail,
            adapter=router._determine_adapter(payload.request),
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
async def approve_action(payload: ApprovalActionRequest) -> Any:
    router = get_app_router()
    if payload.status == ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Cannot transition to pending")
    record = await router.approvals.get(payload.approval_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval request not found")
    audit_record, decision = await router.approvals.resolve(
        approval_id=payload.approval_id,
        status=payload.status,
        decided_by=payload.decided_by,
        notes=payload.notes,
    )
    if payload.status == ApprovalStatus.DENIED:
        return {"result": "denied", "approval_id": str(payload.approval_id)}

    result = await router.execute_adapter(decision.target_adapter, audit_record.request)
    return {
        "result": "executed",
        "detail": result.detail,
        "adapter": decision.target_adapter,
        "approval_id": str(payload.approval_id),
    }


@app.post("/policy/check", response_model=PolicyCheckResponse)
async def policy_check(payload: PolicyCheckRequest) -> PolicyCheckResponse:
    router = get_app_router()
    decision = await router.policy_engine.evaluate(payload.request)
    return PolicyCheckResponse(policy=decision)


@app.get("/approvals/pending")
async def approvals_pending() -> Any:
    router = get_app_router()
    pending = await router.approvals.pending_details()
    return [
        {
            "approval_id": str(approval_id),
            "request": record.request.model_dump(),
            "policy": record.policy_decision.model_dump(),
            "adapter": route.target_adapter,
            "audit": {
                "event_id": str(record.event_id),
                "record": record.model_dump(),
                "signature": record.signature,
                "signature_algorithm": record.signature_algorithm,
                "verification_url": record.verification_url,
            },
        }
        for approval_id, (record, route) in pending.items()
    ]


@app.post("/audit/verify", response_model=AuditVerifyResponse)
async def audit_verify(payload: AuditVerifyRequest) -> AuditVerifyResponse:
    router = get_app_router()
    result = await router.audit_service.verify(
        payload.record,
        verify_rekor=payload.verify_rekor,
    )
    return AuditVerifyResponse(
        verified=result.verified,
        signature_valid=result.signature_valid,
        rekor_included=result.rekor_included,
        failure_reason=result.failure_reason,
    )


@app.get("/healthz", response_model=HealthStatus)
async def healthz() -> HealthStatus:
    return HealthStatus(service="switchboard-api", status="ok")
