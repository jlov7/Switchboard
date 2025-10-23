from __future__ import annotations

from typing import Any

import pytest

from switchboard.core.models import ActionArguments, ActionContext, ActionRequest, ActionSeverity
from switchboard.policy.engine import PolicyEngine


@pytest.fixture(autouse=True)
def disable_opa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWITCHBOARD_USE_OPA", "false")
    monkeypatch.setenv("SWITCHBOARD_APPROVAL_BACKEND", "memory")
    monkeypatch.setenv("SWITCHBOARD_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


def build_request(**overrides: Any) -> ActionRequest:
    context = ActionContext(
        agent_id="agent",
        principal_id="user",
        tenant_id="tenant",
        severity=overrides.get("severity", ActionSeverity.P1),
        resource_scope=overrides.get("resource_scope"),
        pii=overrides.get("pii", False),
        sensitivity_tags=overrides.get("sensitivity_tags", []),
        metadata=overrides.get("metadata", {"role": "ops"}),
    )
    return ActionRequest(
        context=context,
        tool_name=overrides.get("tool_name", "jira"),
        tool_action=overrides.get("tool_action", "create_issue"),
        arguments=ActionArguments(data={"foo": "bar"}),
    )


@pytest.mark.asyncio
async def test_policy_engine_allows_normal_action() -> None:
    engine = PolicyEngine()
    decision = await engine.evaluate(build_request())
    assert decision.allowed is True
    assert decision.requires_approval is False


@pytest.mark.asyncio
async def test_policy_engine_requires_approval_for_pii() -> None:
    engine = PolicyEngine()
    decision = await engine.evaluate(build_request(pii=True, sensitivity_tags=["financial"]))
    assert decision.allowed is True
    assert decision.requires_approval is True


@pytest.mark.asyncio
async def test_policy_engine_blocks_prod_without_role() -> None:
    engine = PolicyEngine()
    decision = await engine.evaluate(
        build_request(resource_scope="prod", metadata={"role": "analyst"})
    )
    assert decision.allowed is False
    assert "policy:prod-role" in decision.policy_ids


@pytest.mark.asyncio
async def test_policy_engine_rate_limits_p0() -> None:
    engine = PolicyEngine()
    request = build_request(severity=ActionSeverity.P0)
    first = await engine.evaluate(request)
    assert first.allowed is True
    assert first.requires_approval is True
    assert "policy:pii-approval" in first.policy_ids
    assert first.risk_level in {"high", "critical"}
    second = await engine.evaluate(request)
    assert second.allowed is False
    assert "policy:rate-limit" in second.policy_ids
    assert second.reason == "rate limit exceeded"


@pytest.mark.asyncio
async def test_policy_engine_blocks_self_approval() -> None:
    engine = PolicyEngine()
    decision = await engine.evaluate(
        build_request(metadata={"role": "ops", "approver": "user"})
    )
    assert decision.allowed is False
    assert "policy:segregation-of-duties" in decision.policy_ids
    assert decision.reason == "Segregation of duties: requester cannot approve"


@pytest.mark.asyncio
async def test_policy_engine_allows_ops_in_roles_list() -> None:
    engine = PolicyEngine()
    decision = await engine.evaluate(
        build_request(metadata={"roles": ["dev", "ops"], "approver": "other"})
    )
    assert decision.allowed is True
    assert decision.requires_approval is False


@pytest.mark.asyncio
async def test_policy_engine_blocks_sensitive_p0_actions() -> None:
    engine = PolicyEngine()
    decision = await engine.evaluate(
        build_request(severity=ActionSeverity.P0, sensitivity_tags=["secret"])
    )
    assert decision.allowed is False
    assert "policy:p0-sensitive-block" in decision.policy_ids
    assert decision.reason == "p0 action with sensitive tags denied"
    assert decision.risk_level == "critical"
