#!/usr/bin/env python3
"""Generate Switchboard policy heatmap infographic."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

from scripts.media.utils import ensure_dir

SEVERITY_LEVELS = ["P2", "P1", "P0"]
SENSITIVITY_LEVELS = ["Standard", "Sensitive", "Restricted"]


POLICY_MAP = np.array(
    [
        ["allow", "allow", "approval"],
        ["allow", "approval", "blocked"],
        ["approval", "blocked", "blocked"],
    ]
)


COLORS = {
    "allow": "#2ECC71",
    "approval": "#F1C40F",
    "blocked": "#E74C3C",
}


def render_heatmap(output_dir: Path) -> None:
    ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

    color_matrix = np.vectorize(COLORS.get)(POLICY_MAP)
    rgba_matrix = np.zeros((color_matrix.shape[0], color_matrix.shape[1], 4))
    for i in range(color_matrix.shape[0]):
        for j in range(color_matrix.shape[1]):
            rgba_matrix[i, j] = to_rgba(color_matrix[i, j])

    ax.imshow(rgba_matrix)

    ax.set_xticks(range(len(SENSITIVITY_LEVELS)))
    ax.set_yticks(range(len(SEVERITY_LEVELS)))
    ax.set_xticklabels(SENSITIVITY_LEVELS, fontsize=12)
    ax.set_yticklabels(SEVERITY_LEVELS, fontsize=12)
    ax.set_xlabel("Data Sensitivity", fontsize=14)
    ax.set_ylabel("Action Severity", fontsize=14)
    ax.set_title("Switchboard Policy Heatmap", fontsize=16, pad=20)

    for i in range(len(SEVERITY_LEVELS)):
        for j in range(len(SENSITIVITY_LEVELS)):
            decision = POLICY_MAP[i, j]
            ax.text(
                j,
                i,
                decision.upper(),
                ha="center",
                va="center",
                color="black",
                fontsize=12,
                fontweight="bold",
                bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": "none", "alpha": 0.7},
            )

    ax.grid(False)
    fig.tight_layout()

    png_path = output_dir / "policy_heatmap.png"
    svg_path = output_dir / "policy_heatmap.svg"
    fig.savefig(png_path)
    fig.savefig(svg_path)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Switchboard policy heatmap")
    parser.add_argument(
        "--output",
        type=str,
        default="docs/media/generated/policy_heatmap",
        help="Output directory for generated assets",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_heatmap(Path(args.output))


if __name__ == "__main__":
    main()
