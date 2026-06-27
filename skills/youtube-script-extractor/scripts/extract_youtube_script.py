#!/usr/bin/env python
"""Extract readable transcript text from a YouTube video's subtitles."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


DEFAULT_INBOX = Path(os.environ.get("YOUTUBE_TRANSCRIPT_INBOX", ".")).expanduser()


def build_ytdlp_command() -> list[str]:
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    uv = shutil.which("uv")
    if uv:
        return [uv, "tool", "run", "--from", "yt-dlp", "yt-dlp"]
    raise SystemExit("Missing dependency: install yt-dlp or uv.")


def run_ytdlp(
    url: str,
    langs: str,
    out_template: str,
    manual_only: bool,
    auto_only: bool,
    cookies_from_browser: str | None,
    js_runtime: str | None,
) -> None:
    cmd = build_ytdlp_command()
    cmd += [
        "--skip-download",
        "--ignore-no-formats",
        "--remote-components",
        "ejs:github",
        "--sub-langs",
        langs,
        "--sub-format",
        "json3/vtt/srv3/best",
        "-o",
        out_template,
    ]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]
    if js_runtime:
        cmd += ["--js-runtimes", js_runtime]
    if auto_only:
        cmd.append("--write-auto-subs")
    elif manual_only:
        cmd.append("--write-subs")
    else:
        cmd += ["--write-subs", "--write-auto-subs"]
    cmd.append(url)
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "yt-dlp failed."
        raise SystemExit(message)


def get_video_info(url: str, cookies_from_browser: str | None, js_runtime: str | None) -> dict:
    cmd = build_ytdlp_command()
    cmd += ["--skip-download", "--ignore-no-formats", "--remote-components", "ejs:github", "--dump-single-json"]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]
    if js_runtime:
        cmd += ["--js-runtimes", js_runtime]
    cmd.append(url)
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        return {"webpage_url": url}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"webpage_url": url}


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^\s*>+\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_timestamp(value: str) -> float:
    main = value.replace(",", ".")
    parts = main.split(":")
    seconds = float(parts[-1])
    if len(parts) >= 2:
        seconds += int(parts[-2]) * 60
    if len(parts) >= 3:
        seconds += int(parts[-3]) * 3600
    return seconds


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def parse_json3(path: Path) -> list[tuple[float, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[tuple[float, str]] = []
    for event in data.get("events", []):
        segs = event.get("segs") or []
        text = clean_text("".join(seg.get("utf8", "") for seg in segs))
        if text:
            rows.append((event.get("tStartMs", 0) / 1000, text))
    return rows


def parse_vtt(path: Path) -> list[tuple[float, str]]:
    rows: list[tuple[float, str]] = []
    current_start: float | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_start, current_lines
        if current_start is None:
            current_lines = []
            return
        text = clean_text(" ".join(current_lines))
        if text:
            rows.append((current_start, text))
        current_start = None
        current_lines = []

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if line == "WEBVTT" or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            flush()
            current_start = parse_timestamp(line.split("-->", 1)[0].strip())
            continue
        if current_start is not None and not line.isdigit():
            current_lines.append(line)
    flush()
    return rows


def collapse_repeats(rows: list[tuple[float, str]]) -> list[tuple[float, str]]:
    collapsed: list[tuple[float, str]] = []
    previous = ""
    for start, text in rows:
        if text == previous:
            continue
        collapsed.append((start, text))
        previous = text
    return collapsed


def render(rows: list[tuple[float, str]], timestamps: bool) -> str:
    if timestamps:
        return "\n".join(f"[{format_timestamp(start)}] {text}" for start, text in rows)
    return "\n".join(text for _, text in rows)


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def safe_filename(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|#\[\]]+', " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:180] or "Untitled"


def default_output_path(title: str) -> Path:
    today = dt.date.today().isoformat()
    return DEFAULT_INBOX / f"{today} {safe_filename(title)} YouTube Transcript.md"


def render_markdown_note(title: str, source: str, transcript: str) -> str:
    note_title = f"{title} YouTube Transcript"
    created = dt.date.today().isoformat()
    return "\n".join(
        [
            "---",
            f"title: {yaml_quote(note_title)}",
            f"source: {yaml_quote(source)}",
            "type: transcript",
            f"created: {created}",
            "tags:",
            "  - youtube",
            "  - transcript",
            "---",
            "",
            transcript,
            "",
        ]
    )


def find_subtitle_file(directory: Path) -> Path:
    candidates = sorted(
        directory.glob("video.*"),
        key=lambda p: (".json3" not in p.name, ".vtt" not in p.name, p.name),
    )
    files = [p for p in candidates if p.suffix in {".json3", ".vtt", ".srv3"}]
    if not files:
        raise SystemExit("No subtitles or captions were found for the requested language.")
    return files[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a YouTube transcript from subtitles.")
    parser.add_argument("url")
    parser.add_argument("--lang", default="ko,en", help="Subtitle language list for yt-dlp, e.g. ko,en")
    parser.add_argument("--timestamps", action="store_true")
    parser.add_argument("--auto-only", action="store_true", help="Only use auto-generated captions.")
    parser.add_argument("--manual-only", action="store_true", help="Only use manually authored subtitles.")
    parser.add_argument(
        "--cookies-from-browser",
        help="Pass a browser name to yt-dlp, such as chrome, safari, firefox, or edge.",
    )
    parser.add_argument("--js-runtime", help="Pass a yt-dlp JavaScript runtime, such as node:/path/to/node.")
    parser.add_argument("--output", help="Write transcript note to this file. Defaults to YOUTUBE_TRANSCRIPT_INBOX or cwd.")
    parser.add_argument("--stdout", action="store_true", help="Print transcript text instead of saving Markdown.")
    args = parser.parse_args()
    if args.auto_only and args.manual_only:
        raise SystemExit("Choose either --auto-only or --manual-only, not both.")

    with tempfile.TemporaryDirectory() as tmp:
        out_template = str(Path(tmp) / "video.%(ext)s")
        run_ytdlp(
            args.url,
            args.lang,
            out_template,
            args.manual_only,
            args.auto_only,
            args.cookies_from_browser,
            args.js_runtime,
        )
        subtitle_file = find_subtitle_file(Path(tmp))
        if subtitle_file.suffix == ".json3":
            rows = parse_json3(subtitle_file)
        else:
            rows = parse_vtt(subtitle_file)
        rows = collapse_repeats(rows)
        if not rows:
            raise SystemExit("Subtitle file was found, but no transcript text could be parsed.")
        text = render(rows, args.timestamps)

    if args.stdout:
        print(text)
    else:
        info = get_video_info(args.url, args.cookies_from_browser, args.js_runtime)
        title = clean_text(info.get("title") or info.get("id") or "Untitled")
        source = info.get("webpage_url") or args.url
        output_path = Path(args.output).expanduser() if args.output else default_output_path(title)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_markdown_note(title, source, text), encoding="utf-8")
        print(os.fspath(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
