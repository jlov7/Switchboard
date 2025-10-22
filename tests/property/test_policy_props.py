from __future__ import annotations

import asyncio
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from switchboard.core.models import ActionArguments, ActionContext, ActionRequest, ActionSeverity
from switchboard.policy.engine import PolicyEngine


@pytest.fixture(autouse=True)
def _disable_opa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWITCHBOARD_USE_OPA", "false")
    monkeypatch.setenv("SWITCHBOARD_APPROVAL_BACKEND", "memory")
    monkeypatch.setenv("SWITCHBOARD_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


def _build_request(**overrides: Any) -> ActionRequest:
    context = ActionContext(
        agent_id=overrides.get("agent_id", "agent"),
        principal_id=overrides.get("principal_id", "user"),
        tenant_id=overrides.get("tenant_id", "tenant"),
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
        arguments=ActionArguments(data=overrides.get("arguments", {"foo": "bar"})),
    )


@settings(max_examples=50)
@given(role=st.text(min_size=1).filter(lambda r: r.lower() != "ops"))
def test_prod_scope_requires_ops(role: str) -> None:
    engine = PolicyEngine()
    request = _build_request(
        resource_scope="prod",
        metadata={"role": role},
    )
    decision = asyncio.run(engine.evaluate(request))
    assert decision.allowed is False
    assert "policy:prod-role" in decision.policy_ids


@settings(max_examples=50)
@given(tags=st.lists(st.text(min_size=1), max_size=3))
def test_pii_or_sensitive_requires_approval(tags: list[str]) -> None:
    engine = PolicyEngine()
    request = _build_request(pii=True, sensitivity_tags=tags)
    decision = asyncio.run(engine.evaluate(request))
    assert decision.allowed is True
    assert decision.requires_approval is True


@settings(max_examples=50)
@given(
    severity=st.sampled_from([ActionSeverity.P1, ActionSeverity.P2]),
    tool_name=st.text(min_size=1, max_size=16).filter(lambda s: s.strip() != ""),
    payload=st.dictionaries(
        keys=st.text(min_size=1, max_size=8), values=st.text(max_size=16), max_size=4
    ),
)
def test_default_actions_allowed(
    severity: ActionSeverity, tool_name: str, payload: dict[str, str]
) -> None:
    engine = PolicyEngine()
    request = _build_request(
        severity=severity,
        tool_name=tool_name,
        arguments=payload or {"foo": "bar"},
        metadata={"role": "ops"},
        pii=False,
        sensitivity_tags=[],
        resource_scope=None,
    )
    decision = asyncio.run(engine.evaluate(request))
    assert decision.allowed is True
    assert decision.requires_approval is False
