#!/usr/bin/env python3
"""Simulate OPA outage and ensure Switchboard falls back to local policy engine."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

API_URL = os.getenv("SWITCHBOARD_API_URL", "http://localhost:8000")


@asynccontextmanager
async def opa_outage() -> AsyncIterator[None]:
    # flip env to unreachable host for duration
    original_url = os.getenv("OPA_URL")
    os.environ["OPA_URL"] = "http://127.0.0.1:9999"
    try:
        yield
    finally:
        if original_url is not None:
            os.environ["OPA_URL"] = original_url
        else:
            os.environ.pop("OPA_URL", None)


async def run() -> None:
    payload = {
        "request": {
            "context": {
                "agent_id": "chaos-agent",
                "principal_id": "user",
                "tenant_id": "demo",
                "severity": "p1",
                "metadata": {"role": "ops"},
            },
            "tool_name": "jira",
            "tool_action": "create_issue",
            "arguments": {"data": {"summary": "Chaos test"}, "redacted_fields": []},
        }
    }
    async with httpx.AsyncClient(base_url=API_URL, timeout=5.0) as client, opa_outage():
        response = await client.post("/route", json=payload)
        response.raise_for_status()
        print("OPA outage fallback decision:", response.json())


if __name__ == "__main__":
    asyncio.run(run())
