"""Shared utilities for Switchboard media automation scripts."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import httpx


class TimeoutError(RuntimeError):
    """Raised when a wait operation times out."""


async def wait_for_http(url: str, timeout: float = 60.0, interval: float = 1.0) -> None:
    """Wait for an HTTP endpoint to return a successful response."""

    deadline = asyncio.get_event_loop().time() + timeout
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            try:
                response = await client.get(url)
                if response.status_code < 500:
                    return
            except httpx.HTTPError:
                pass

            if asyncio.get_event_loop().time() >= deadline:
                raise TimeoutError(f"Timed out waiting for {url}")
            await asyncio.sleep(interval)


async def wait_for_opa(url: str = "http://localhost:8181/health", timeout: float = 120.0) -> None:
    deadline = asyncio.get_event_loop().time() + timeout
    probe_urls = [url, "http://localhost:8181/v1/data"]
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            for candidate in probe_urls:
                try:
                    response = await client.get(candidate)
                    if response.status_code < 400:
                        return
                except httpx.HTTPError:
                    continue
            if asyncio.get_event_loop().time() >= deadline:
                raise TimeoutError("Timed out waiting for OPA readiness")
            await asyncio.sleep(1.0)


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def require_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required binary '{name}' not found on PATH")
