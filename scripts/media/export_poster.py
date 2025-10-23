#!/usr/bin/env python3
"""Render the Switchboard architecture poster without external CLIs."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from scripts.media.utils import ensure_dir


def _load_poster_spec(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_font(font_size: int) -> ImageFont.FreeTypeFont:
    for candidate in ("Arial.ttf", "Helvetica.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, font_size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _render_rectangle(draw: ImageDraw.ImageDraw, element: dict[str, Any]) -> None:
    x, y = element["x"], element["y"]
    w, h = element["width"], element["height"]
    fill = element.get("backgroundColor", "#FFFFFF")
    outline = element.get("strokeColor", "#000000")
    stroke_width = max(1, int(element.get("strokeWidth", 1)))
    draw.rectangle([x, y, x + w, y + h], fill=fill, outline=outline, width=stroke_width)


def _render_text(draw: ImageDraw.ImageDraw, element: dict[str, Any]) -> None:
    text = element.get("text") or element.get("originalText", "")
    font_size = int(element.get("fontSize", 24))
    font = _pick_font(font_size)
    color = element.get("strokeColor", "#000000")
    text_align = element.get("textAlign", "left")
    x, y = element["x"], element["y"]
    width = element.get("width", 0)

    if text_align == "center" and width:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = x + (width - text_width) / 2

    draw.text((x, y), text, fill=color, font=font)


def _render_elements(draw: ImageDraw.ImageDraw, elements: list[dict[str, Any]]) -> None:
    dispatch = {
        "rectangle": _render_rectangle,
        "text": _render_text,
    }
    for element in elements:
        if element.get("isDeleted"):
            continue
        renderer = dispatch.get(element.get("type"))
        if renderer:
            renderer(draw, element)


def export_poster(source: Path, output_dir: Path) -> None:
    spec = _load_poster_spec(source)
    elements = spec.get("elements", [])

    if not elements:
        raise RuntimeError("Poster specification has no drawable elements")

    ensure_dir(output_dir)

    max_x = max(el["x"] + el.get("width", 0) for el in elements)
    max_y = max(el["y"] + el.get("height", 0) for el in elements)

    margin = 40
    width = int(math.ceil(max_x + margin))
    height = int(math.ceil(max_y + margin))

    background = spec.get("appState", {}).get("viewBackgroundColor", "#FFFFFF")
    image = Image.new("RGB", (width, height), color=background)
    draw = ImageDraw.Draw(image)

    _render_elements(draw, elements)

    png_path = output_dir / "switchboard_poster.png"
    pdf_path = output_dir / "switchboard_poster.pdf"

    image.save(png_path, format="PNG", optimize=True)
    image.save(pdf_path, format="PDF")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Switchboard poster assets")
    parser.add_argument(
        "--source",
        type=str,
        default="docs/media/poster/switchboard_poster.excalidraw",
        help="Source Excalidraw JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/media/generated/poster",
        help="Output directory for exported assets",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_poster(Path(args.source), Path(args.output))


if __name__ == "__main__":
    main()

