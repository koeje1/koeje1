#!/usr/bin/env python3
"""Update a compact board from two explicitly selected PUBLIC repositories.

Python 3.11+; standard library only. No token or external service is required
for reading public data. Nothing is written until BOTH sources are validated.

    python scripts/update_public_work.py
    python scripts/update_public_work.py --snapshot assets/activity/public-work.json
    python scripts/update_public_work.py --snapshot snapshot.json --output-dir /tmp/work-proof

Offline snapshots use the same schema as assets/activity/public-work.json:
schema_version=1; projects contain repository, visibility="public", and a
commit object with sha, date, title and optional url. The allowlist below is
the only source of repository names and display labels. Read access to another
repository never implies permission to publish its contents.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPRedirectHandler, Request
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "assets" / "activity"
PROJECTS = (
    ("koeje1/operations-automation-lab", "문서 자동화"),
    ("koeje1/github-profile-banner-animation", "픽셀 애니메이션"),
)
OUTPUT_FILES = ("public-work-light.svg", "public-work-dark.svg", "public-work.json")
KST = timezone(timedelta(hours=9))
MAX_RESPONSE_BYTES = 1_000_000
THEMES = {
    "light": {"text": "#26394a", "muted": "#596775", "line": "#d8e2df", "accent": "#4a8068"},
    "dark": {"text": "#e7e8df", "muted": "#a4b6c1", "line": "#30434d", "accent": "#9bcbb4"},
}


class RefreshError(Exception):
    """Expected source or validation failure; retain the last good output."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        # A renamed repository needs an explicit allowlist update. Do not follow
        # network-provided redirects or silently change the publishing scope.
        return None


def fetch_json(url: str) -> object:
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "koeje1-public-work-board",
    })
    # Deliberately unauthenticated: a public repository becoming private must
    # fail closed even if the surrounding environment has a privileged token.
    try:
        with build_opener(NoRedirect).open(request, timeout=15) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        raise RefreshError(f"Public GitHub API returned HTTP {error.code}.") from None
    except (URLError, TimeoutError, OSError):
        raise RefreshError("Public GitHub API is unavailable.") from None
    if len(data) > MAX_RESPONSE_BYTES:
        raise RefreshError("Public GitHub API response exceeded the size limit.")
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise RefreshError("Public GitHub API returned invalid JSON.") from None


def fetch_snapshot() -> dict:
    projects = []
    for repository, _label in PROJECTS:
        base = f"https://api.github.com/repos/{repository}"
        metadata = fetch_json(base)
        if (not isinstance(metadata, dict) or metadata.get("private") is not False
                or metadata.get("full_name") != repository):
            raise RefreshError("A configured repository is no longer confirmed public.")
        branch = metadata.get("default_branch")
        if not isinstance(branch, str) or not branch or len(branch) > 255:
            raise RefreshError("A configured repository has no valid default branch.")
        commits = fetch_json(base + "/commits?" + urlencode({"sha": branch, "per_page": 1}))
        if not isinstance(commits, list) or not commits or not isinstance(commits[0], dict):
            raise RefreshError("A configured public repository has no readable commit.")
        item = commits[0]
        commit = item.get("commit")
        if not isinstance(commit, dict) or not isinstance(commit.get("committer"), dict):
            raise RefreshError("A public commit response has an invalid structure.")
        projects.append({"repository": repository, "visibility": "public", "commit": {
            "sha": item.get("sha"), "date": commit["committer"].get("date"),
            "title": commit.get("message"),
        }})
    return {"schema_version": 1, "projects": projects}


def clean_title(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RefreshError("A public commit has no readable title.")
    line = value.splitlines()[0]
    line = "".join(char for char in unicodedata.normalize("NFC", line)
                   if not unicodedata.category(char).startswith("C"))
    line = " ".join(line.split())
    if not line:
        raise RefreshError("A public commit has no printable title.")
    return line if len(line) <= 512 else line[:511] + "…"


def normalize_snapshot(snapshot: object) -> dict:
    if not isinstance(snapshot, dict) or snapshot.get("schema_version") != 1:
        raise RefreshError("Snapshot schema_version must be 1.")
    entries = snapshot.get("projects")
    if not isinstance(entries, list) or len(entries) != len(PROJECTS):
        raise RefreshError("Snapshot must contain exactly the selected public repositories.")
    by_repository = {}
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("visibility") != "public":
            raise RefreshError("Snapshot contains a source that is not explicitly public.")
        repository = entry.get("repository")
        if not isinstance(repository, str) or repository not in dict(PROJECTS) or repository in by_repository:
            raise RefreshError("Snapshot contains an unexpected or duplicate repository.")
        by_repository[repository] = entry
    projects = []
    for repository, label in PROJECTS:
        commit = by_repository[repository].get("commit")
        if not isinstance(commit, dict):
            raise RefreshError("Snapshot has no valid commit object.")
        sha, date = commit.get("sha"), commit.get("date")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise RefreshError("Snapshot has no valid commit SHA.")
        try:
            timestamp = datetime.fromisoformat(date.replace("Z", "+00:00"))
            if timestamp.tzinfo is None or not 1970 <= timestamp.year <= 2099:
                raise ValueError
        except (AttributeError, TypeError, ValueError):
            raise RefreshError("Snapshot has no valid timezone-aware commit date.") from None
        date = timestamp.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        url = f"https://github.com/{repository}/commit/{sha}"
        if commit.get("url", url) != url:
            raise RefreshError("Snapshot commit link does not match the selected repository and SHA.")
        projects.append({"repository": repository, "label": label, "visibility": "public", "commit": {
            "sha": sha, "date": date, "title": clean_title(commit.get("title")), "url": url,
        }})
    return {"schema_version": 1,
            "scope": "Latest commits on the default branches of two selected public repositories.",
            "projects": projects}


def clip_cells(text: str, limit: int = 58) -> str:
    used, result = 0, []
    for char in text:
        width = 0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in "WF" else 1
        if used + width > limit - 1:
            return "".join(result) + "…"
        result.append(char)
        used += width
    return text


def render_svg(snapshot: dict, theme: str) -> str:
    colors = THEMES[theme]
    description = " / ".join(f'{p["label"]}: {p["commit"]["title"]}, {p["commit"]["date"]}'
                             for p in snapshot["projects"])
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="420" height="168" viewBox="0 0 420 168" role="img" aria-labelledby="title desc">',
        '<title id="title">최근 공개 작업</title>',
        f'<desc id="desc">{escape(description)}</desc>',
        '<defs><clipPath id="row1"><rect x="18" y="74" width="384" height="20"/></clipPath>',
        '<clipPath id="row2"><rect x="18" y="130" width="384" height="20"/></clipPath></defs>',
        '<g font-family="Noto Sans CJK KR, Noto Sans KR, Segoe UI, sans-serif">',
        f'<path d="M5 17h3v4h4v3H8v4H5v-4H1v-3h4Z" fill="{colors["accent"]}"/>',
        f'<text x="18" y="28" font-size="16" font-weight="700" fill="{colors["text"]}">최근 공개 작업</text>',
        f'<text x="376" y="27" text-anchor="end" font-size="11" fill="{colors["muted"]}">마지막 커밋</text>',
        # A small static Lumi from the existing companion geometry. The board
        # reflects commits; it does not imply real-time presence or activity.
        '<g transform="translate(386 10) scale(.7)" shape-rendering="crispEdges">',
        '<path d="M8 0H13V4H18V8H21V19H18V24H5V22H1V10H4V5H8Z" fill="#b6dcd0"/>',
        '<path d="M6 12h2v2H6Z M14 12h2v2h-2Z" fill="#182830"/>',
        '<path d="M4 17h3v2H4Z M16 17h3v2h-3Z" fill="#dca9ab"/></g>',
        f'<path d="M18 101H402" stroke="{colors["line"]}"/>',
    ]
    for index, project in enumerate(snapshot["projects"]):
        commit = project["commit"]
        date = datetime.fromisoformat(commit["date"].replace("Z", "+00:00")).astimezone(KST).strftime("%Y.%m.%d")
        y = 64 + index * 56
        parts.extend([
            f'<text x="18" y="{y}" font-size="14" font-weight="600" fill="{colors["text"]}">{escape(project["label"])}</text>',
            f'<text x="402" y="{y}" text-anchor="end" font-size="11" fill="{colors["muted"]}">{date} · {commit["sha"][:7]}</text>',
            f'<text x="18" y="{y + 23}" font-size="12" fill="{colors["muted"]}" clip-path="url(#row{index + 1})">{escape(clip_cells(commit["title"]))}</text>',
        ])
    parts.append('</g></svg>\n')
    svg = "\n".join(parts)
    ET.fromstring(svg)
    return svg


def write_changed(output_dir: Path, outputs: dict[str, str]) -> list[str]:
    changed = {name: content.encode("utf-8") for name, content in outputs.items()
               if not (output_dir / name).exists() or (output_dir / name).read_bytes() != content.encode("utf-8")}
    if not changed:
        return []
    output_dir.mkdir(parents=True, exist_ok=True)
    # Prepare every file before replacing any output. API and input failures
    # have already returned, so they cannot erase the last successful board.
    with tempfile.TemporaryDirectory(prefix=".public-work-", dir=output_dir) as temporary:
        temporary_dir = Path(temporary)
        for name, data in changed.items():
            (temporary_dir / name).write_bytes(data)
        for name in changed:
            os.replace(temporary_dir / name, output_dir / name)
    return list(changed)


def refresh(snapshot_path: Path | None, output_dir: Path) -> list[str]:
    if snapshot_path is None:
        raw_snapshot = fetch_snapshot()
    else:
        try:
            raw_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise RefreshError("Cannot read the offline public snapshot.") from None
    snapshot = normalize_snapshot(raw_snapshot)
    outputs = {
        OUTPUT_FILES[0]: render_svg(snapshot, "light"),
        OUTPUT_FILES[1]: render_svg(snapshot, "dark"),
        OUTPUT_FILES[2]: json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
    }
    return write_changed(output_dir, outputs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, help="Use a validated local public snapshot; no network requests")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        changed = refresh(args.snapshot, args.output_dir)
    except RefreshError as error:
        print(f"Public work refresh failed; previous output kept: {error}", file=sys.stderr)
        return 1
    except OSError:
        print("Public work refresh could not write the generated files.", file=sys.stderr)
        return 1
    print("Updated: " + ", ".join(changed) if changed else "Public work is unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
