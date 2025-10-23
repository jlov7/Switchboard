#!/usr/bin/env python3
"""Wait for Switchboard demo services to become ready."""

from __future__ import annotations

import asyncio

from scripts.media.utils import wait_for_http, wait_for_opa


async def main() -> None:
    await asyncio.gather(
        wait_for_http("http://localhost:8000/healthz", timeout=300),
        wait_for_opa(timeout=300),
    )


if __name__ == "__main__":
    asyncio.run(main())
