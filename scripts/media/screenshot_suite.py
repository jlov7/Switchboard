#!/usr/bin/env python3
"""Capture consistent Switchboard documentation screenshots."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import TypedDict

from scripts.media.utils import ensure_dir, wait_for_http

try:
    from playwright.async_api import Playwright, async_playwright
except ModuleNotFoundError as exc:  # pragma: no cover - to surface quickly for CLI users
    raise SystemExit(
        "playwright is required. Install with `pip install switchboard[media] && playwright install`."
    ) from exc


DEFAULT_VIEWPORT = {"width": 1440, "height": 900}


class Clip(TypedDict, total=False):
    x: float
    y: float
    width: float
    height: float


class Scene(TypedDict):
    name: str
    url: str
    selector: str
    clip: Clip | None


SCENES: tuple[Scene, ...] = (
    Scene(
        name="fastapi-docs",
        url="http://localhost:8000/docs",
        selector="text=Switchboard API",
        clip=None,
    ),
    Scene(
        name="approvals-backlog",
        url="http://localhost:8501",
        selector="text=Switchboard Approvals Queue",
        clip=None,
    ),
    Scene(
        name="approvals-detail",
        url="http://localhost:8501",
        selector="text=Approval",
        clip=None,
    ),
    Scene(
        name="audit-log",
        url="http://localhost:8000/docs#/audit/verify_audit_verify_post",
        selector="text=Audit Verify",
        clip=None,
    ),
)


async def capture_scene(
    playwright: Playwright, output_dir: Path, scene: Scene, headless: bool
) -> None:
    browser = await playwright.chromium.launch(headless=headless)
    page = await browser.new_page(viewport=DEFAULT_VIEWPORT)
    await page.goto(scene["url"], wait_until="networkidle")
    await page.wait_for_selector(scene["selector"])
    clip = scene.get("clip")
    clip_box: Clip | None = None
    if clip is not None:
        clip_box = {
            "x": float(clip.get("x", 0.0)),
            "y": float(clip.get("y", 0.0)),
            "width": float(clip.get("width", 0.0)),
            "height": float(clip.get("height", 0.0)),
        }
    await page.screenshot(
        path=str(output_dir / f"{scene['name']}.png"),
        full_page=clip_box is None,
        clip=clip_box,
    )
    await browser.close()


async def run_capture(output_dir: Path, headless: bool) -> None:
    await wait_for_http("http://localhost:8000/healthz", timeout=60)
    await wait_for_http("http://localhost:8501", timeout=60)

    async with async_playwright() as playwright:
        for scene in SCENES:
            await capture_scene(playwright, output_dir, scene, headless=headless)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture Switchboard media screenshots")
    parser.add_argument("--output", type=str, default="docs/media/screenshots")
    parser.add_argument("--no-headless", action="store_false", dest="headless", default=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(args.output)
    asyncio.run(run_capture(output_dir, headless=args.headless))


if __name__ == "__main__":
    main()
