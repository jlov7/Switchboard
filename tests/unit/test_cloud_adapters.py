from __future__ import annotations

from typing import Any

import pytest

from switchboard.adapters.aws import BedrockAgentCoreAdapter
from switchboard.adapters.base import AdapterResult
from switchboard.adapters.google import VertexAgentEngineAdapter
from switchboard.core.models import ActionArguments, ActionContext, ActionRequest, ActionSeverity


def build_request(**kwargs: Any) -> ActionRequest:
    context = ActionContext(
        agent_id="agent",
        principal_id="user",
        tenant_id="tenant",
        severity=ActionSeverity.P1,
        metadata={"role": "ops"},
    )
    return ActionRequest(
        context=context,
        tool_name=kwargs.get("tool_name", "bedrock:demo"),
        tool_action="invoke",
        arguments=ActionArguments(data=kwargs.get("arguments", {"input_text": "hello"})),
    )


@pytest.mark.asyncio
async def test_bedrock_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWITCHBOARD_AWS_MODE", raising=False)
    adapter = BedrockAgentCoreAdapter()
    result = await adapter.execute_action(build_request())
    assert isinstance(result, AdapterResult)
    assert result.success is True
    assert result.response["mode"] == "dry-run"


@pytest.mark.asyncio
async def test_vertex_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SWITCHBOARD_GCP_MODE", raising=False)
    adapter = VertexAgentEngineAdapter()
    request = build_request(tool_name="vertex:demo", arguments={"input_text": "hey"})
    result = await adapter.execute_action(request)
    assert result.success is True
    assert result.response["mode"] == "dry-run"


def test_bedrock_live_requires_boto3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWITCHBOARD_AWS_MODE", "live")
    monkeypatch.delenv("AWS_REGION", raising=False)
    with pytest.raises(RuntimeError):
        BedrockAgentCoreAdapter()
    monkeypatch.delenv("SWITCHBOARD_AWS_MODE", raising=False)


def test_vertex_live_requires_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWITCHBOARD_GCP_MODE", "live")
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    with pytest.raises(RuntimeError):
        VertexAgentEngineAdapter()
    monkeypatch.delenv("SWITCHBOARD_GCP_MODE", raising=False)
