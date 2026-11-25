#!/usr/bin/env python3
"""Render the small README divider from the existing Lumi SVG identity.

Run from the package root: python scripts/render_divider.py
Requires Python >=3.11, Pillow, and the Inkscape executable on PATH.
No banner-renderer import or modification is used. The original pet SVG is read
once and remains unchanged. All outputs stay under assets/divider/.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "divider"
PET_PATH = ROOT / "assets" / "source" / "pets" / "lumi.svg"
WIDTH, HEIGHT = 960, 72
LOOP_MS, STEP_MS = 16_000, 80
FRAME_COUNT = LOOP_MS // STEP_MS
COLORS = {
    "sky": "#111c29",
    "trail": "#304b50",
    "trail_tip": "#4b665e",
    "paper": "#c2cfce",
    "paper_fold": "#829b91",
    "paper_ink": "#657d79",
    "star_a": "#dab97c",
    "star_b": "#9bcbb4",
    "star_c": "#7772a8",
}
ET.register_namespace("", "http://www.w3.org/2000/svg")


def rectangle(x: int, y: int, width: int, height: int, color: str) -> str:
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{color}"/>'


def pet_svg(raw: str, center_x: int, center_y: int) -> str:
    """Nest the original 48-unit drawing without changing its geometry/colors."""
    pet = ET.fromstring(raw)
    pet.set("width", "48")
    pet.set("height", "48")
    # Existing artwork bounds center near (20, 20) in its 48-unit viewBox.
    pet.set("x", str(center_x - 20))
    pet.set("y", str(center_y - 20))
    return ET.tostring(pet, encoding="unicode")


def frame_svg(time_ms: int, raw_pet: str) -> str:
    # Modulo makes 0 and T the same source state. No last-frame reset is used.
    phase = 2 * math.pi * ((time_ms % LOOP_MS) / LOOP_MS)
    lumi_x = round(460 + 40 * math.sin(phase - 0.35))
    lumi_y = round(34 - 4 * math.sin(2 * phase - 0.7) - 2 * math.sin(phase))
    paper_x = round(487 + 44 * math.sin(phase))
    paper_y = round(27 - 4 * math.sin(2 * phase + 0.5))

    body = [rectangle(0, 0, WIDTH, HEIGHT, COLORS["sky"])]
    # A quiet floor cue; not a second landscape or another title banner.
    for x in range(324, 637, 12):
        body.append(rectangle(x, 58, 3, 1, COLORS["trail"]))
    body.append(rectangle(319, 58, 1, 1, COLORS["trail_tip"]))
    body.append(rectangle(642, 58, 1, 1, COLORS["trail_tip"]))

    # Three small stars circle the document, each using an existing muted accent.
    for index, color in enumerate(("star_a", "star_b", "star_c")):
        orbit = 2 * phase + index * 2 * math.pi / 3
        star_x = paper_x + round(16 * math.cos(orbit))
        star_y = paper_y + round(11 * math.sin(orbit))
        body.append(rectangle(star_x, star_y, 2, 2, COLORS[color]))
        if index == 0:
            body.append(rectangle(star_x + 1, star_y - 1, 1, 4, COLORS[color]))

    # A tiny document cue, with lines rather than readable text.
    body.append(rectangle(paper_x - 4, paper_y - 5, 8, 11, COLORS["paper"]))
    body.append(rectangle(paper_x + 1, paper_y - 5, 3, 3, COLORS["paper_fold"]))
    body.append(rectangle(paper_x - 2, paper_y, 4, 1, COLORS["paper_ink"]))
    body.append(rectangle(paper_x - 2, paper_y + 3, 3, 1, COLORS["paper_ink"]))
    body.append(pet_svg(raw_pet, lumi_x, lumi_y))

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" shape-rendering="crispEdges">'
        '<title>Lumi follows a small document through a quiet star trail</title>'
        + "".join(body) + "</svg>"
    )


def changed_pixels(left: Image.Image, right: Image.Image) -> int:
    delta = ImageChops.difference(left.convert("RGB"), right.convert("RGB"))
    red, green, blue = delta.split()
    maximum_channel = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    return delta.width * delta.height - maximum_channel.histogram()[0]


def render_one(job: tuple[int, Path, str, str]) -> tuple[int, Image.Image]:
    index, scratch, svg, inkscape = job
    source = scratch / f"frame-{index:03d}.svg"
    target = scratch / f"frame-{index:03d}.png"
    source.write_text(svg, encoding="utf-8")
    subprocess.run(
        [inkscape, str(source), "--export-type=png", "--export-filename=" + str(target)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    with Image.open(target) as image:
        return index, image.convert("RGB")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inkscape = shutil.which("inkscape")
    if not inkscape:
        raise SystemExit("Inkscape is required on PATH. The supplied trail.gif/png can be used without rerendering.")
    if not PET_PATH.is_file():
        raise SystemExit(f"Missing existing pet identity: {PET_PATH}")
    raw_pet = PET_PATH.read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    sources = [frame_svg(index * STEP_MS, raw_pet) for index in range(FRAME_COUNT)]
    assert frame_svg(0, raw_pet) == frame_svg(LOOP_MS, raw_pet)
    (OUT / "trail.svg").write_text(sources[0], encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="koeje-divider-") as temp:
        scratch = Path(temp)
        jobs = [(index, scratch, svg, inkscape) for index, svg in enumerate(sources)]
        with ThreadPoolExecutor(max_workers=4) as executor:
            rendered = list(executor.map(render_one, jobs))
    frames = [image for _, image in sorted(rendered)]
    frames[0].save(OUT / "trail.png", optimize=True)

    # Every fill is solid and present in the source. Keep an exact shared palette.
    color_hex = sorted(set(re.findall(r"#[0-9a-fA-F]{6}", raw_pet)) | set(COLORS.values()))
    colors = [tuple(int(value[index:index + 2], 16) for index in (1, 3, 5)) for value in color_hex]
    if len(colors) > 256:
        raise RuntimeError("The source palette unexpectedly exceeds GIF's color-table capacity.")
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette([component for color in colors for component in color] + [0] * (768 - len(colors) * 3))
    indexed = [frame.quantize(palette=palette_image, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(
        OUT / "trail.gif", save_all=True, append_images=indexed[1:],
        duration=[STEP_MS] * FRAME_COUNT, loop=0, optimize=True, disposal=1,
    )

    # Verify the decoded timeline, including any encoder-coalesced durations.
    decoded: list[Image.Image] = []
    durations: list[int] = []
    with Image.open(OUT / "trail.gif") as animation:
        for index in range(animation.n_frames):
            animation.seek(index)
            decoded.append(animation.convert("RGB"))
            durations.append(int(animation.info.get("duration", 0)))
    assert sum(durations) == LOOP_MS
    assert all(duration > 0 and duration % 10 == 0 for duration in durations)
    elapsed = 0
    sample_index = 0
    for decoded_frame, duration in zip(decoded, durations):
        while sample_index * STEP_MS < elapsed + duration:
            if ImageChops.difference(decoded_frame, frames[sample_index]).getbbox():
                raise RuntimeError(f"GIF decode differs from source at sample {sample_index}.")
            sample_index += 1
        elapsed += duration
    assert sample_index == FRAME_COUNT

    # The seam is a normal 80ms step, not an artificially duplicated first frame.
    step_changes = [changed_pixels(frames[index], frames[index + 1]) for index in range(FRAME_COUNT - 1)]
    boundary_changes = changed_pixels(frames[-1], frames[0])
    assert boundary_changes <= max(step_changes), "Loop seam exceeds an ordinary in-loop step."

    proof = Image.new("RGB", (WIDTH, 4 * (HEIGHT + 24)), "#111c29")
    proof_draw = ImageDraw.Draw(proof)
    for row, sample_ms in enumerate((0, 4_000, 8_000, 12_000)):
        top = row * (HEIGHT + 24)
        proof_draw.text((16, top + 5), f"{sample_ms / 1000:.2f} s", fill="#becbcc")
        proof.paste(frames[sample_ms // STEP_MS], (0, top + 24))
    proof.save(OUT / "trail-proof.png", optimize=True)

    file_report = {}
    for filename in ("trail.gif", "trail.png", "trail.svg", "trail-proof.png"):
        path = OUT / filename
        item = {"bytes": path.stat().st_size, "sha256": sha256(path)}
        if filename.endswith((".gif", ".png")):
            with Image.open(path) as image:
                item.update(width=image.width, height=image.height, frames=getattr(image, "n_frames", 1))
        file_report[filename] = item
    report = {
        "asset": "One low-profile animated README divider; no text in published strip.",
        "pet_source": PET_PATH.relative_to(ROOT).as_posix(),
        "pet_source_sha256": hashlib.sha256(raw_pet.encode()).hexdigest(),
        "pet_geometry_and_palette_unchanged": True,
        "loop_ms": LOOP_MS,
        "sample_step_ms": STEP_MS,
        "sample_fps": 1000 / STEP_MS,
        "source_sample_count": FRAME_COUNT,
        "encoded_frame_count": len(decoded),
        "decoded_duration_ms": sum(durations),
        "shared_palette_colors": len(colors),
        "all_decoded_samples_match_source_rgb": True,
        "source_state_at_0_equals_state_at_T": True,
        "boundary_changed_pixels": boundary_changes,
        "largest_in_loop_step_changed_pixels": max(step_changes),
        "first_and_last_encoded_frames_must_be_identical": False,
        "gif_under_200_kib": (OUT / "trail.gif").stat().st_size < 200 * 1024,
        "github_render_and_full_preview_ui_verified": False,
        "visual_review": "Pending image inspection; see the root handoff validation for observations.",
        "files": file_report,
    }
    (OUT / "trail-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not report["gif_under_200_kib"]:
        raise RuntimeError("The decorative divider exceeds its 200KiB design budget.")
    print(json.dumps({"output": str(OUT), "gif_bytes": file_report["trail.gif"]["bytes"], "frames": len(decoded), "duration_ms": LOOP_MS, "seam_changed_pixels": boundary_changes}, ensure_ascii=False))


if __name__ == "__main__":
    main()
