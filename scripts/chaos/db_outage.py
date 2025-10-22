#!/usr/bin/env python3
"""Chaos: simulate database outage for persistent approval store."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

API_URL = os.getenv("SWITCHBOARD_API_URL", "http://localhost:8000")


@asynccontextmanager
async def disconnect_db() -> AsyncIterator[None]:
    original_url = os.getenv("SWITCHBOARD_DATABASE_URL")
    os.environ["SWITCHBOARD_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"  # force fallback
    try:
        yield
    finally:
        if original_url is not None:
            os.environ["SWITCHBOARD_DATABASE_URL"] = original_url
        else:
            os.environ.pop("SWITCHBOARD_DATABASE_URL", None)


async def main() -> None:
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
            "arguments": {"data": {"summary": "DB chaos"}},
        }
    }
    async with httpx.AsyncClient(base_url=API_URL, timeout=5.0) as client, disconnect_db():
        response = await client.post("/route", json=payload)
        print("DB chaos response status:", response.status_code)
        print("Body:", response.json())


if __name__ == "__main__":
    asyncio.run(main())
