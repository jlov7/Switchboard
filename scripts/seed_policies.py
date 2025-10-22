#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx
import yaml

OPA_URL = os.getenv("OPA_URL", "http://localhost:8181")


async def seed_rego(client: httpx.AsyncClient) -> None:
    rego_path = Path("switchboard/policy/base.rego")
    policy_id = "switchboard"
    response = await client.put(
        f"/v1/policies/{policy_id}",
        content=rego_path.read_text(encoding="utf-8"),
        headers={"Content-Type": "text/plain"},
    )
    response.raise_for_status()


async def seed_data(client: httpx.AsyncClient) -> None:
    config_path = Path("switchboard/policy/config.yaml")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    response = await client.put(
        "/v1/data/switchboard/config",
        json=data,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()


async def main() -> None:
    async with httpx.AsyncClient(base_url=OPA_URL, timeout=10.0) as client:
        await seed_rego(client)
        await seed_data(client)
    print("Seeded policies to OPA at", OPA_URL)


if __name__ == "__main__":
    asyncio.run(main())
