#!/usr/bin/env python3
"""Automate Switchboard hero walkthrough capture with Playwright."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import httpx

from scripts.media.utils import ensure_dir, require_binary, wait_for_http

try:
    from playwright.async_api import (
        BrowserContext,
        Error as PlaywrightError,
        Page,
        async_playwright,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - surfaced immediately to caller
    raise SystemExit(
        "playwright is required. Install with `pip install switchboard[media] && playwright install`."
    ) from exc


Scene = Literal["hero", "approvals"]

DEFAULT_SCENE: Scene = "hero"
DEFAULT_UI_URL = os.getenv("SWITCHBOARD_APPROVALS_URL", "http://localhost:8501")
DEFAULT_API_URL = os.getenv("SWITCHBOARD_API_URL", "http://localhost:8000")


def _approval_request_payload() -> dict[str, Any]:
    return {
        "request": {
            "context": {
                "agent_id": "demo-agent",
                "principal_id": "user-123",
                "tenant_id": "demo",
                "severity": "p0",
                "pii": True,
                "metadata": {"role": "ops"},
            },
            "tool_name": "partner:repo-bot",
            "tool_action": "sync_comments",
            "arguments": {
                "data": {
                    "repository": "example/repo",
                    "pull_request": 42,
                    "comment": "Ensure compliance labels are applied.",
                },
                "redacted_fields": [],
            },
        }
    }


async def _post_route(api_url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_url, timeout=15.0) as client:
        response = await client.post("/route", json=_approval_request_payload())
    if response.status_code != 202:
        raise RuntimeError(
            "Expected 202 response when submitting approval demo payload; "
            f"got {response.status_code}: {response.text}"
        )
    data = response.json()
    if not isinstance(data, dict) or "approval_id" not in data:
        raise RuntimeError("Route response missing approval_id")
    return data


async def _wait_for_pending(api_url: str, approval_id: str, timeout: float = 30.0) -> None:
    deadline = asyncio.get_event_loop().time() + timeout
    async with httpx.AsyncClient(base_url=api_url, timeout=5.0) as client:
        while True:
            try:
                response = await client.get("/approvals/pending")
                response.raise_for_status()
                payload = response.json()
                if any(item.get("approval_id") == approval_id for item in payload):
                    return
            except httpx.HTTPError:
                pass
            if asyncio.get_event_loop().time() >= deadline:
                raise TimeoutError(f"Approval {approval_id} not visible via API in time")
            await asyncio.sleep(1.0)


async def _clear_pending(api_url: str) -> None:
    async with httpx.AsyncClient(base_url=api_url, timeout=5.0) as client:
        while True:
            response = await client.get("/approvals/pending")
            response.raise_for_status()
            payload = response.json()
            if not payload:
                return
            for item in payload:
                approval_id = item.get("approval_id")
                if approval_id:
                    await client.post(
                        "/approve",
                        json={
                            "approval_id": approval_id,
                            "status": "denied",
                            "decided_by": "media-bot",
                        },
                    )


async def _read_latest_audit_record(log_path: Path) -> dict[str, Any]:
    if not log_path.exists():
        raise RuntimeError(
            "Audit log file not found. Expected to locate at data/audit-log.jsonl; "
            "ensure the API service is running with audit logging enabled."
        )

    content = await asyncio.to_thread(log_path.read_text, encoding="utf-8")
    lines = [line for line in content.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("Audit log appears to be empty; cannot verify last run")

    entry = json.loads(lines[-1])
    record = entry.get("record")
    if not isinstance(record, dict):
        raise RuntimeError("Audit log entry missing record field")
    record["signature"] = entry.get("signature")
    record["signature_algorithm"] = entry.get("algorithm")
    record["verification_url"] = entry.get("verification_reference")
    return record


async def _verify_audit_record(api_url: str, record: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_url, timeout=15.0) as client:
        response = await client.post("/audit/verify", json={"record": record})
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected payload from /audit/verify")
    return data


async def _wait_for_selector(page: Page, selector: str, timeout: float = 30.0) -> None:
    await page.wait_for_selector(selector, timeout=timeout * 1000, state="visible")


async def _pull_to_front(page: Page, approval_id: str) -> None:
    refresh_button = page.locator("button:has-text('Refresh queue')").first
    entry_container = page.locator(f"text=Approval {approval_id}").first
    approve_button = page.locator(f"text=Approve {approval_id}")

    for _ in range(36):
        if await entry_container.count() > 0:
            await entry_container.scroll_into_view_if_needed()
            await entry_container.wait_for(state="visible", timeout=10_000)
            if await approve_button.count() > 0:
                await approve_button.first.scroll_into_view_if_needed()
                return
            return
        try:
            await refresh_button.click()
        except PlaywrightError:
            pass
        await page.wait_for_timeout(1_500)

    await _wait_for_selector(page, f"text=Approve {approval_id}", timeout=60)


async def _perform_approval(page: Page, approval_id: str) -> None:
    approve_button = page.locator(f"text=Approve {approval_id}").first
    await approve_button.click()
    await page.wait_for_timeout(2_000)
    await page.wait_for_load_state("networkidle")
    await _wait_for_selector(page, "text=No pending approvals.", timeout=30)


async def _inject_banner(page: Page, content: dict[str, Any]) -> None:
    snippet = json.dumps(content, indent=2)
    await page.evaluate(
        """
        (text) => {
            const existing = document.getElementById('audit-verify-banner');
            if (existing) existing.remove();
            const banner = document.createElement('div');
            banner.id = 'audit-verify-banner';
            banner.style.position = 'fixed';
            banner.style.bottom = '32px';
            banner.style.right = '32px';
            banner.style.zIndex = '9999';
            banner.style.padding = '16px';
            banner.style.maxWidth = '420px';
            banner.style.background = 'rgba(0, 34, 102, 0.92)';
            banner.style.color = 'white';
            banner.style.fontFamily = 'Menlo, monospace';
            banner.style.fontSize = '12px';
            banner.style.borderRadius = '8px';
            banner.style.boxShadow = '0 12px 24px rgba(0,0,0,0.35)';
            banner.style.whiteSpace = 'pre-wrap';
            banner.textContent = text;
            document.body.appendChild(banner);
        }
        """,
        snippet,
    )


@dataclass(slots=True)
class WalkthroughResult:
    approval_id: str
    audit_verification: dict[str, Any]
    video_dir: Path | None


async def _scene_hero(context: BrowserContext, api_url: str, ui_url: str) -> WalkthroughResult:
    page = await context.new_page()
    await page.goto(ui_url, wait_until="networkidle")

    await _clear_pending(api_url)
    route_payload = await _post_route(api_url)
    approval_id = route_payload["approval_id"]

    await _wait_for_pending(api_url, approval_id)
    await page.reload(wait_until="networkidle")

    await _pull_to_front(page, approval_id)
    await page.wait_for_timeout(1_000)
    await _perform_approval(page, approval_id)

    log_path = Path("data/audit-log.jsonl")
    record = await _read_latest_audit_record(log_path)
    verify_payload = await _verify_audit_record(api_url, record)
    await _inject_banner(page, verify_payload)
    await page.wait_for_timeout(2_000)

    return WalkthroughResult(
        approval_id=approval_id, audit_verification=verify_payload, video_dir=None
    )


async def _scene_approvals(context: BrowserContext, api_url: str, ui_url: str) -> WalkthroughResult:
    page = await context.new_page()
    await page.goto(ui_url, wait_until="networkidle")

    route_payload = await _post_route(api_url)
    approval_id = route_payload["approval_id"]

    await _pull_to_front(page, approval_id)
    await page.wait_for_timeout(1500)
    await _perform_approval(page, approval_id)
    await page.wait_for_timeout(1500)

    return WalkthroughResult(approval_id=approval_id, audit_verification={}, video_dir=None)


async def _capture_scene(args: argparse.Namespace) -> WalkthroughResult:
    record_dir: Path | None = None
    if args.video:
        record_dir = Path(tempfile.mkdtemp(prefix="switchboard_walkthrough_"))

    await wait_for_http(f"{args.api_url}/healthz", timeout=args.timeout)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=args.headless)
        context = await browser.new_context(
            viewport={"width": args.width, "height": args.height},
            record_video_dir=str(record_dir) if record_dir else None,
        )
        try:
            if args.scene == "approvals":
                result = await _scene_approvals(context, args.api_url, args.ui_url)
            else:
                result = await _scene_hero(context, args.api_url, args.ui_url)
        finally:
            await context.close()
            await browser.close()

    result.video_dir = record_dir
    return result


def _convert_to_mp4(source_dir: Path, destination: Path, fps: int) -> None:
    require_binary("ffmpeg")

    source_files = sorted(source_dir.glob("**/*.webm"))
    if not source_files:
        raise RuntimeError(f"No recorded Playwright video found in {source_dir}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_files[0]),
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        str(destination),
    ]
    subprocess_run(command)


def _convert_to_gif(source_mp4: Path, destination: Path) -> None:
    require_binary("ffmpeg")

    palette = destination.with_suffix(".palette.png")
    palette_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_mp4),
        "-vf",
        "fps=15,scale=1280:-1:flags=lanczos,palettegen",
        str(palette),
    ]
    gif_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_mp4),
        "-i",
        str(palette),
        "-filter_complex",
        "fps=15,scale=1280:-1:flags=lanczos[x];[x][1:v]paletteuse",
        str(destination),
    ]
    subprocess_run(palette_cmd)
    subprocess_run(gif_cmd)
    palette.unlink(missing_ok=True)


def subprocess_run(command: list[str]) -> None:
    import subprocess

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "Command failed: "
            f"{' '.join(command)}\n"
            f"stdout: {completed.stdout}\n"
            f"stderr: {completed.stderr}"
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture Switchboard demo scenes")
    parser.add_argument("--video", type=str, help="Output MP4 path", default=None)
    parser.add_argument("--gif", type=str, help="Optional GIF output path", default=None)
    parser.add_argument("--scene", type=str, choices=["hero", "approvals"], default=DEFAULT_SCENE)
    parser.add_argument("--api-url", type=str, default=DEFAULT_API_URL)
    parser.add_argument("--ui-url", type=str, default=DEFAULT_UI_URL)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=60, help="Seconds to wait for API readiness")
    parser.add_argument("--headless", dest="headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    result = asyncio.run(_capture_scene(args))

    if args.video and result.video_dir:
        mp4_path = Path(args.video)
        ensure_dir(mp4_path.parent)
        _convert_to_mp4(result.video_dir, mp4_path, fps=args.fps)
        if args.gif:
            gif_path = Path(args.gif)
            ensure_dir(gif_path.parent)
            _convert_to_gif(mp4_path, gif_path)


if __name__ == "__main__":
    main()
