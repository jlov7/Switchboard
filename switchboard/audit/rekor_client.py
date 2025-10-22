from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

import httpx


class RekorError(Exception):
    pass


class RekorClient:
    def __init__(self, url: str | None = None, offline_log: Path | None = None) -> None:
        self.url = url or os.getenv("REKOR_URL", "")
        self.offline_log = offline_log or Path("data/audit-log.jsonl")
        self.offline_log.parent.mkdir(parents=True, exist_ok=True)
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._http_client:
            if not self.url:
                raise RekorError("Rekor URL is not configured")
            self._http_client = httpx.AsyncClient(base_url=self.url, timeout=5.0)
        return self._http_client

    async def log_entry(self, payload: dict[str, Any]) -> str:
        if not self.url:
            with self.offline_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")
            return f"offline://{self.offline_log}"
        client = await self._get_client()
        response = await client.post("/api/v1/log/entries", json=payload)
        if response.status_code >= 400:
            raise RekorError(f"Rekor error {response.status_code}: {response.text}")
        data = cast(dict[str, Any], response.json())
        return str(data.get("uuid", "unknown"))

    async def verify_entry(self, entry_id: str) -> bool:
        if entry_id.startswith("offline://"):
            return Path(entry_id.replace("offline://", "")).exists()
        if not self.url:
            raise RekorError("Cannot verify entry without Rekor URL")
        client = await self._get_client()
        response = await client.get(f"/api/v1/log/entries/{entry_id}")
        return response.status_code == 200

    async def aclose(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
