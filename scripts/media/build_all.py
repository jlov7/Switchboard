#!/usr/bin/env python3
"""Orchestrate Switchboard media artifact generation."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".venv_media"
VENV_BIN = VENV_PATH / "bin"
PYTHON = VENV_BIN / "python"
MAKE = shutil.which("make") or "make"


if not PYTHON.exists():
    subprocess.run([MAKE, "install"], cwd=ROOT, check=True)


STEPS = [
    [MAKE, "dev-media"],
    [str(PYTHON), "-m", "scripts.media.wait_for_services"],
    [
        str(PYTHON),
        "-m",
        "scripts.media.walkthrough",
        "--video",
        "docs/media/generated/hero.mp4",
    ],
    [
        str(PYTHON),
        "-m",
        "scripts.media.walkthrough",
        "--scene",
        "approvals",
        "--video",
        "docs/media/generated/approvals.mp4",
        "--gif",
        "docs/media/generated/approvals.gif",
    ],
    [str(PYTHON), "-m", "scripts.media.screenshot_suite"],
    [str(PYTHON), "-m", "scripts.media.policy_heatmap"],
    [str(PYTHON), "-m", "scripts.media.export_poster"],
]


def run_step(command: list[str]) -> None:
    print(f"\n[media] Running step: {' '.join(map(str, command))}")
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    for step in STEPS:
        run_step([str(part) for part in step])


if __name__ == "__main__":
    main()
