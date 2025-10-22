from __future__ import annotations

import os
from typing import Any

import httpx

from switchboard.adapters.base import AdapterResult, BaseAdapter
from switchboard.core.models import ActionRequest

google_auth_requests: Any | None = None

try:  # pragma: no cover - optional dependency
    import google.auth
    from google.auth.transport import requests as _google_auth_requests
except Exception:  # pragma: no cover - handled downstream
    google_auth: Any | None = None
else:  # pragma: no cover - importlib guard
    google_auth = google.auth
    google_auth_requests = _google_auth_requests


class VertexAgentEngineAdapter(BaseAdapter):
    """Adapter for Google Vertex AI Agent Engine.

    Similar to the Bedrock adapter, it defaults to **dry-run** mode. Set
    `SWITCHBOARD_GCP_MODE=live` to forward requests to Vertex AI using the
    service account credentials resolved by `google.auth.default()`.
    """

    def __init__(self, name: str = "vertex", *, location: str | None = None) -> None:
        super().__init__(name=name)
        self.mode = os.getenv("SWITCHBOARD_GCP_MODE", "dry-run").lower()
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.getenv("VERTEX_LOCATION", "us-central1")
        self.agent = os.getenv("VERTEX_AGENT_ID")
        self._credentials: Any | None = None
        if self.mode == "live":
            if google_auth is None:
                raise RuntimeError(
                    "google-cloud-aiplatform is required for live Vertex integration. Install extras via 'pip install .[gcp]'"
                )
            if not self.project or not self.agent:
                raise RuntimeError(
                    "Vertex adapter requires GOOGLE_CLOUD_PROJECT and VERTEX_AGENT_ID environment variables in live mode"
                )
            self._credentials, _ = google_auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )

    async def execute_action(self, request: ActionRequest) -> AdapterResult:
        if self.mode != "live" or self._credentials is None:
            return AdapterResult(
                success=True,
                detail="vertex dry-run",
                response={
                    "echo": request.arguments.data,
                    "project": self.project or "vertex-demo",
                    "agent": request.arguments.data.get("agent") or self.agent,
                    "mode": self.mode,
                },
            )

        endpoint = (
            f"https://{self.location}-aiplatform.googleapis.com/v1beta1/"
            f"projects/{self.project}/locations/{self.location}/agents/{self.agent}:predict"
        )
        payload = self._payload_from_request(request)
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                return AdapterResult(
                    success=True, detail="vertex invoke success", response=response.json()
                )
            except Exception as exc:  # pragma: no cover - network path
                return AdapterResult(
                    success=False, detail=f"vertex invoke failed: {exc}", response={}
                )

    def _get_token(self) -> str:  # pragma: no cover - network path
        if self._credentials is None or google_auth_requests is None:
            raise RuntimeError("Google credentials not initialized")
        if not self._credentials.valid:
            self._credentials.refresh(google_auth_requests.Request())
        return str(self._credentials.token)

    def _payload_from_request(self, request: ActionRequest) -> dict[str, Any]:
        args = request.arguments.data
        if "inputs" in args:
            return args
        return {
            "inputs": [
                {
                    "role": "user",
                    "content": args.get("input_text", ""),
                }
            ],
            "session": str(request.context.request_id),
            "parameters": args.get("parameters", {}),
        }
