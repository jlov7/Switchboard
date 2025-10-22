#!/usr/bin/env python3
"""Chaos: rapidly toggle adapter availability to observe retry behaviour."""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx

API_URL = "http://localhost:8000"


async def attempt(action: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=API_URL, timeout=5.0) as client:
        response = await client.post("/route", json=action)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return {"unexpected": data}
        return data


async def main() -> None:
    actions = []
    for i in range(5):
        actions.append(
            {
                "request": {
                    "context": {
                        "agent_id": "chaos-agent",
                        "principal_id": "user",
                        "tenant_id": "demo",
                        "severity": "p1",
                        "metadata": {"role": "ops"},
                    },
                    "tool_name": "partner:flaky",
                    "tool_action": "noop",
                    "arguments": {"data": {"iteration": i}},
                }
            }
        )
    for payload in actions:
        await asyncio.sleep(random.uniform(0.1, 0.5))
        try:
            result = await attempt(payload)
            print("adapter response", result)
        except Exception as exc:  # noqa: BLE001
            print("adapter failure", exc)


if __name__ == "__main__":
    asyncio.run(main())
