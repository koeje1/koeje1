#!/usr/bin/env python3
"""Render five wandering companions on a fully transparent README strip.

The characters share the code-native geometry and palette in render_banners.py.
Only this strip is written; the header, footer and standalone pets stay intact.
Requires Python >=3.11, Pillow and Inkscape on PATH.

    python scripts/render_divider.py
    python scripts/render_divider.py --proof-dir /tmp/companion-proof
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw

import render_banners as characters


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "divider"
WIDTH, HEIGHT = 420, 88
LOOP_MS, STEP_MS = 8000, 80
FRAME_COUNT = LOOP_MS // STEP_MS
SCALE = 1.4
P = characters.P


def wave(t: float, period: float, phase: float = 0) -> float:
    return math.sin(2 * math.pi * (t + phase) / period)


def closed_eyes(body: str, xs: tuple[int, ...], y: int, closed: bool) -> str:
    if closed:
        for x in xs:
            body = body.replace(characters.rect(x, y, 2, 2, P["ink"]),
                                characters.rect(x, y + 1, 2, 1, P["ink"]))
    return body


def place(body: str, center_x: float, feet_y: float, body_width: int,
          body_height: int, *, lift: float = 0, squash: float = 1) -> str:
    # Stretch about the feet, keeping pixel positions whole and edges crisp.
    x = round(center_x - body_width * SCALE / 2)
    y = round(feet_y - body_height * SCALE * squash - lift)
    return (f'<g transform="translate({x} {y}) scale({SCALE} {SCALE * squash:.3f})" '
            f'shape-rendering="crispEdges">{body}</g>')


def frame_svg(time_ms: int) -> str:
    """One periodic scene; frame 0 and frame T have identical SVG source."""
    t = (time_ms % LOOP_MS) / 1000
    pieces = []
    # The companions follow the same gentle wander with small delayed turns.
    centers = [57 + 74 * i + round(17 * wave(t, 8, (4 - i) * -0.15))
               for i in range(5)]

    # Sprout: wing beats and a little flight, with the original rounded dragon.
    wing_clock = 1.6 + ((t % 0.8) / 0.8) * 0.96
    dragon = characters.dragon(wing_clock)
    dragon = closed_eyes(dragon, (25,), 13, (t + 0.4) % 4 >= 3.84)
    pieces.append(place(dragon, centers[0], 75, 29, 29,
                        lift=5 + round(4 * wave(t, 1.6))))

    # Miso: alternating paws, a swishing curled tail and a slight walking bounce.
    cat = characters.cat(t)
    step = int(((t + 0.16) % 0.8) / 0.2)
    left_lift, right_lift = ((2, 0) if step < 2 else (0, 2))
    cat = cat.replace(characters.rect(5, 25, 4, 3, P["cat_dark"]),
                      characters.rect(4 if step == 0 else 5, 25 - left_lift,
                                      5, 3, P["cat_dark"]))
    cat = cat.replace(characters.rect(14, 25, 4, 3, P["cat_dark"]),
                      characters.rect(15 if step == 2 else 14, 25 - right_lift,
                                      5, 3, P["cat_dark"]))
    pieces.append(place(cat, centers[1], 76, 29, 28,
                        lift=1 + round(abs(2 * wave(t, 0.8, 0.16)))))

    # Peach: a clear jump followed by a brief soft landing and bent ears.
    jump = ((t + 0.4) % 1.6) / 1.6
    airborne = jump < 0.6
    bunny_lift = round(15 * math.sin(math.pi * jump / 0.6)) if airborne else 0
    landing = 0.6 <= jump < 0.7
    bunny = characters.bunny(6.18 if landing else 0)
    bunny = closed_eyes(bunny, (7, 14), 20, (t + 0.9) % 4 >= 3.84)
    pieces.append(place(bunny, centers[2], 76, 26, 33,
                        lift=bunny_lift, squash=0.88 if landing else 1))

    # Momo: four wing poses, offset from the dragon, and an easy rise and fall.
    wing_step = int(((t + 0.2) % 0.8) / 0.2)
    pose = (0, 1, 2, 1)[wing_step]
    owl = characters.owl(6.721 + pose * 0.16)
    owl = closed_eyes(owl, (7, 15), 10, (t + 1.4) % 4 >= 3.84)
    pieces.append(place(owl, centers[3], 76, 24, 26,
                        lift=7 + round(5 * wave(t, 2, 0.6))))

    # Lumi leads with a figure-eight float. The two pixels belong to its trail.
    lumi_x = centers[4] + round(4 * wave(t, 4))
    lumi_y = 62 - round(10 * wave(t, 4, 0.4))
    wisp = characters.wisp(t)
    pieces.append(place(wisp, lumi_x, lumi_y, 21, 24))
    for index in range(2):
        px = round(lumi_x - 25 - index * 7)
        py = round(lumi_y - 16 + 3 * wave(t, 2, index * 0.4))
        pieces.append(characters.rect(px, py, 2, 2,
                                      P["mint"] if index == 0 else P["gold"]))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
            f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img">'
            '<title>Five little companions on a wander</title>'
            '<desc>Sprout flies, Miso walks, Peach hops, Momo flutters and Lumi floats. '
            'A transparent eight-second loop, with no background panel.</desc>'
            + ''.join(pieces) + '</svg>')


def rasterize(source: str, directory: Path) -> Image.Image:
    key = hashlib.sha256(source.encode()).hexdigest()
    svg_path, png_path = directory / f"{key}.svg", directory / f"{key}.png"
    svg_path.write_text(source, encoding="utf-8")
    subprocess.run([shutil.which("inkscape") or "inkscape", str(svg_path),
                    "--export-type=png", "--export-background-opacity=0",
                    "--export-png-antialias=0",
                    f"--export-filename={png_path}"], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with Image.open(png_path) as image:
        result = image.convert("RGBA")
    # Canonical invisible RGB avoids treating transparent white and transparent
    # black as different pixels during exact GIF-disposal verification.
    assert set(result.getchannel("A").get_flattened_data()) == {0, 255}
    result.putdata([(r, g, b, a) if a else (0, 0, 0, 0)
                    for r, g, b, a in result.get_flattened_data()])
    return result


def save_transparent_gif(frames: list[Image.Image], output: Path) -> None:
    # Reserve index 0 only for transparency. All opaque colors are exact, stable
    # across frames and never dithered; crisp SVG geometry needs no matte color.
    colors = sorted({(r, g, b) for frame in frames for r, g, b, a in frame.get_flattened_data()
                     if a >= 128})
    if len(colors) > 255:
        raise ValueError("The pixel palette must fit 255 opaque colors.")
    lookup = {color: index + 1 for index, color in enumerate(colors)}
    palette = [0, 0, 0] + [channel for color in colors for channel in color]
    palette += [0] * (768 - len(palette))
    indexed = []
    for frame in frames:
        image = Image.new("P", frame.size, 0)
        image.putpalette(palette)
        image.putdata([lookup[(r, g, b)] if a >= 128 else 0
                       for r, g, b, a in frame.get_flattened_data()])
        indexed.append(image)
    # Restore each preceding frame to transparent before drawing the next. This
    # prevents a moving sprite leaving opaque trails on either GitHub theme.
    indexed[0].save(output, save_all=True, append_images=indexed[1:],
                    duration=STEP_MS, loop=0, transparency=0, background=0,
                    disposal=2, optimize=False)


def count_changed(first: Image.Image, second: Image.Image) -> int:
    difference = ImageChops.difference(first, second)
    channels = difference.split()
    combined = channels[0]
    for channel in channels[1:]:
        combined = ImageChops.lighter(combined, channel)
    return sum(combined.histogram()[1:])


def verify(output: Path, source_frames: list[Image.Image]) -> tuple[dict, list[Image.Image]]:
    decoded, durations = [], []
    with Image.open(output) as gif:
        for index in range(gif.n_frames):
            gif.seek(index)
            decoded.append(gif.convert("RGBA"))
            durations.append(gif.info.get("duration", 0))
    assert len(decoded) == FRAME_COUNT
    assert sum(durations) == LOOP_MS
    # Exact decoded-frame equivalence verifies palette, transparency and disposal
    # together, including pixels exposed by a character moving away.
    for source, result in zip(source_frames, decoded):
        assert count_changed(source, result) == 0, "GIF altered a source frame"
        alpha = result.getchannel("A")
        assert set(alpha.get_flattened_data()) == {0, 255}
        x0, y0, x1, y1 = alpha.getbbox()
        assert x0 > 0 and y0 > 0 and x1 < WIDTH and y1 < HEIGHT
    changes = [count_changed(a, b) for a, b in zip(decoded, decoded[1:])]
    seam = count_changed(decoded[-1], decoded[0])
    assert seam <= max(changes)
    report = {"width": WIDTH, "height": HEIGHT, "loop_ms": LOOP_MS,
              "frames": len(decoded), "frame_ms": STEP_MS,
              "bytes": output.stat().st_size, "companions": 5,
              "transparent_every_frame": True, "exact_decoded_frames": True,
              "all_frames_inside_canvas": True,
              "source_loop_equal": frame_svg(0) == frame_svg(LOOP_MS),
              "seam_changed_pixels": seam, "max_adjacent_changed_pixels": max(changes),
              "motions": {"Sprout": "wing beats and flight", "Miso": "alternating paws and tail",
                          "Peach": "hop, bent ears and landing", "Momo": "wing beats and floating",
                          "Lumi": "figure-eight float"}}
    assert report["source_loop_equal"]
    return report, decoded


def write_proof(directory: Path, frames: list[Image.Image], report: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    samples = [0, 5, 26, 63]
    board = Image.new("RGB", (WIDTH * 2 + 36, (HEIGHT + 26) * len(samples) + 24), "#e6e9ee")
    draw = ImageDraw.Draw(board)
    for row, index in enumerate(samples):
        y = 12 + row * (HEIGHT + 26)
        for col, background in enumerate(("#ffffff", "#0d1117")):
            x = 12 + col * (WIDTH + 12)
            theme = "light" if col == 0 else "dark"
            draw.text((x, y), f"{index * STEP_MS / 1000:.2f} s / {theme}", fill="#303844")
            composite = Image.new("RGBA", (WIDTH, HEIGHT), background)
            composite.alpha_composite(frames[index])
            board.paste(composite.convert("RGB"), (x, y + 18))
    board.save(directory / "transparent-companions-proof.png")
    (directory / "render-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main(proof_dir: Path | None = None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sources = [frame_svg(index * STEP_MS) for index in range(FRAME_COUNT)]
    with tempfile.TemporaryDirectory(prefix="koeje-companions-") as temporary:
        with ThreadPoolExecutor(max_workers=3) as executor:
            frames = list(executor.map(lambda source: rasterize(source, Path(temporary)), sources))
    (OUT / "trail.svg").write_text(sources[0], encoding="utf-8")
    frames[0].save(OUT / "trail.png")
    save_transparent_gif(frames, OUT / "trail.gif")
    report, decoded = verify(OUT / "trail.gif", frames)
    if proof_dir is not None:
        write_proof(proof_dir, decoded, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-dir", type=Path, help="Optional directory for theme proofs and metrics")
    main(parser.parse_args().proof_dir)
