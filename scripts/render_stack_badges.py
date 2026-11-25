#!/usr/bin/env python3
"""Build offline GitHub README badges from vendored Simple Icons marks.

Requires Python 3, Pillow and Inkscape. No network request is made.
Run from any working directory: python scripts/render_stack_badges.py
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "assets" / "stack"
HEIGHT = 32
RASTER_SCALE = 2
FONT_SIZE = 13
PANEL = "#111C29"
BORDER = "#34495E"
TEXT = "#F0F6FC"
NS = "http://www.w3.org/2000/svg"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def measure_font() -> ImageFont.FreeTypeFont:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), FONT_SIZE * RASTER_SCALE)
    # Pillow resolves this on common Linux distributions. A missing font is an
    # explicit failure, not a silent replacement with an unreadable bitmap font.
    return ImageFont.truetype("DejaVuSans.ttf", FONT_SIZE * RASTER_SCALE)


def icon_markup(path: Path) -> str:
    node = ET.fromstring(path.read_text(encoding="utf-8"))
    if node.get("viewBox") != "0 0 24 24":
        raise ValueError(f"Unexpected upstream viewBox: {path}")
    fragments = []
    for child in node:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "title":
            continue
        if tag != "path" or set(child.attrib) - {"d", "fill-rule", "clip-rule"}:
            raise ValueError(f"Unexpected upstream geometry: {path}: {tag}")
        # Preserve every upstream path coordinate. Only the parent fill changes.
        attrs = " ".join(f'{key}="{html.escape(value, quote=True)}"' for key, value in child.attrib.items())
        fragments.append(f"<path {attrs}/>")
    if not fragments:
        raise ValueError(f"Empty upstream icon: {path}")
    return "".join(fragments)


def make_svg(item: dict, width: int, text_width: float, geometry: str) -> str:
    title = html.escape(item["title"])
    label = html.escape(item["label"])
    return f'''<svg xmlns="{NS}" width="{width}" height="{HEIGHT}" viewBox="0 0 {width} {HEIGHT}" role="img" aria-label="{title}">
  <title>{title}</title>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{HEIGHT - 1}" rx="6" fill="{PANEL}" stroke="{BORDER}"/>
  <g transform="translate(10 6) scale(0.8333333333333333)" fill="#{item['display_hex']}">{geometry}</g>
  <text x="38" y="20.4" font-family="DejaVu Sans,Segoe UI,Arial,sans-serif" font-size="{FONT_SIZE}" font-weight="400" fill="{TEXT}" textLength="{text_width:.3f}" lengthAdjust="spacingAndGlyphs">{label}</text>
</svg>
'''


def contact_sheet(items: list[dict], font: ImageFont.FreeTypeFont) -> None:
    # This is a visual QA sheet of the delivered badges, not an additional brand
    # illustration. The actual badge PNGs retain transparent rounded corners.
    labels = ["Core", "Web & tools", "Workspace"]
    groups = ["core", "web_tools", "workspace"]
    card_width = 930
    card_height = 198
    sheet = Image.new("RGB", (card_width, card_height * 2), "#F6F8FA")
    draw = ImageDraw.Draw(sheet)
    heading = ImageFont.truetype(font.path, 13)
    for block, bg in enumerate(["#F6F8FA", "#0D1117"]):
        ybase = block * card_height
        draw.rectangle((0, ybase, card_width, ybase + card_height), fill=bg)
        for row, (group, name) in enumerate(zip(groups, labels)):
            y = ybase + 16 + row * 58
            draw.text((16, y + 9), name, font=heading, fill="#57606A" if block == 0 else "#9DA7B2")
            x = 128
            for item in [entry for entry in items if entry["group"] == group]:
                badge = Image.open(STACK / item["png"]).convert("RGBA")
                badge = badge.resize((item["width"], HEIGHT), Image.Resampling.LANCZOS)
                sheet.paste(badge, (x, y), badge)
                x += item["width"] + 8
    sheet.save(STACK / "stack-badges-preview.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inkscape", default=shutil.which("inkscape"), help="Inkscape executable path")
    args = parser.parse_args()
    if not args.inkscape:
        raise SystemExit("Inkscape is required for offline SVG-to-PNG rasterization.")
    config = json.loads((STACK / "badge-config.json").read_text(encoding="utf-8"))
    font = measure_font()
    results = []
    for item in config["items"]:
        vendor_path = STACK / item["vendor_path"]
        original = vendor_path.read_bytes()
        if blob_sha(original) != item["upstream_blob_sha"]:
            raise ValueError(f"Vendored source differs from recorded Git blob: {vendor_path}")
        text_width = font.getlength(item["label"]) / RASTER_SCALE
        width = max(84, math.ceil(38 + text_width + 12))
        svg = STACK / f"{item['id']}.svg"
        png = STACK / f"{item['id']}.png"
        svg.write_text(make_svg(item, width, text_width, icon_markup(vendor_path)), encoding="utf-8")
        proc = subprocess.run(
            [args.inkscape, str(svg), "--export-type=png", f"--export-filename={png}",
             f"--export-width={width * RASTER_SCALE}", f"--export-height={HEIGHT * RASTER_SCALE}",
             "--export-background-opacity=0"], capture_output=True, text=True, check=True)
        with Image.open(png) as output:
            if output.size != (width * RASTER_SCALE, HEIGHT * RASTER_SCALE) or output.mode != "RGBA":
                raise ValueError(f"Invalid PNG dimensions or alpha: {png}")
            if output.getpixel((0, 0))[3] != 0:
                raise ValueError(f"Rounded outer corner must remain transparent: {png}")
        results.append({**item, "width": width, "height": HEIGHT, "svg": svg.name,
                        "png": png.name, "png_width": width * RASTER_SCALE,
                        "png_height": HEIGHT * RASTER_SCALE, "source_sha256": sha256(original),
                        "svg_sha256": sha256(svg.read_bytes()), "png_sha256": sha256(png.read_bytes())})
    manifest = {"retrieved_at": config["retrieved_at"], "source_commit": config["source_commit"],
                "height": HEIGHT, "raster_scale": RASTER_SCALE, "items": results}
    (STACK / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    contact_sheet(results, font)
    print(json.dumps({"badge_count": len(results), "manifest": str(STACK / "manifest.json"),
                      "badges": [{"id": x["id"], "width": x["width"], "height": x["height"]} for x in results]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
