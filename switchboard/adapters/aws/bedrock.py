from __future__ import annotations

import asyncio
import os
from typing import Any

from switchboard.adapters.base import AdapterResult, BaseAdapter
from switchboard.core.models import ActionRequest

try:  # pragma: no cover - optional dependency
    import boto3
except Exception:  # pragma: no cover - handled downstream
    boto3 = None


class BedrockAgentCoreAdapter(BaseAdapter):
    """Adapter that proxies Switchboard actions to AWS Bedrock AgentCore.

    The adapter operates in two modes:
    - **dry-run** (default) – returns a mocked success payload for demos/tests.
    - **live** – performs `InvokeAgent` calls using `boto3` when
      `SWITCHBOARD_AWS_MODE=live`.
    """

    def __init__(self, name: str = "bedrock", *, region: str | None = None) -> None:
        super().__init__(name=name)
        self.mode = os.getenv("SWITCHBOARD_AWS_MODE", "dry-run").lower()
        self.region = region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        self._client = None
        if self.mode == "live" and boto3 is None:
            raise RuntimeError(
                "boto3 is required for live Bedrock integration. Install extras via 'pip install .[aws]'"
            )
        if self.mode == "live" and self.region and boto3 is not None:
            self._client = boto3.client("bedrock-agent-runtime", region_name=self.region)

    async def execute_action(self, request: ActionRequest) -> AdapterResult:
        if self.mode != "live" or self._client is None:
            dry_response = self._build_dry_run_response(request)
            return AdapterResult(success=True, detail="bedrock dry-run", response=dry_response)

        params = self._payload_from_request(request)
        try:
            response = await asyncio.to_thread(self._client.invoke_agent, **params)
            output = self._render_response(response)
            return AdapterResult(success=True, detail="bedrock invoke success", response=output)
        except Exception as exc:  # pragma: no cover - network path
            return AdapterResult(success=False, detail=f"bedrock invoke failed: {exc}", response={})

    def _payload_from_request(self, request: ActionRequest) -> dict[str, Any]:
        args = request.arguments.data
        agent_id = args.get("agent_id") or os.getenv("AWS_BEDROCK_AGENT_ID")
        alias_id = args.get("agent_alias_id") or os.getenv(
            "AWS_BEDROCK_AGENT_ALIAS_ID", "TSTALIASID"
        )
        if not agent_id:
            raise ValueError(
                "Bedrock adapter requires 'agent_id' in arguments or AWS_BEDROCK_AGENT_ID env"
            )
        session_id = str(request.context.request_id)
        options = {
            "agentId": agent_id,
            "agentAliasId": alias_id,
            "sessionId": session_id,
        }
        if "input_text" in args:
            options["inputText"] = args["input_text"]
        if "session_state" in args:
            options["sessionState"] = args["session_state"]
        if "enable_trace" in args:
            options["enableTrace"] = bool(args["enable_trace"])
        return options

    def _render_response(self, response: Any) -> dict[str, Any]:  # pragma: no cover - network path
        # boto3 streaming response exposes an iterator of events; we surface high-level details for logging
        completions = []
        for event in response.get("completion", []):
            if isinstance(event, dict) and "content" in event:
                completions.append(event["content"])
        return {"completion": completions or str(response)}

    def _build_dry_run_response(self, request: ActionRequest) -> dict[str, Any]:
        return {
            "echo": request.arguments.data,
            "agent_id": request.arguments.data.get("agent_id")
            or os.getenv("AWS_BEDROCK_AGENT_ID", "bedrock-demo-agent"),
            "mode": self.mode,
        }
