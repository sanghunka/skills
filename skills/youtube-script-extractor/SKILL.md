---
name: youtube-script-extractor
description: Extract scripts, captions, subtitles, or transcript text from YouTube video URLs. Use when the user asks to pull a YouTube script, get a transcript, summarize from video captions, save captions as Markdown/text, or process a YouTube URL such as youtube.com/watch or youtu.be.
---

# YouTube Script Extractor

## Workflow

1. Run `scripts/extract_youtube_script.py <youtube-url>` for the requested video.
2. Prefer manually authored subtitles over auto-generated captions unless the user requests otherwise.
3. Select language with `--lang <code>` when requested. Use `ko` for Korean, `en` for English, or a comma-separated fallback list such as `ko,en`.
4. Use `--timestamps` when the user needs a study script, quote lookup, or citation-friendly output. Omit timestamps for clean prose.
5. If YouTube returns HTTP 429, login, bot-check, or private-video errors, retry with `--cookies-from-browser chrome` or another browser that has YouTube access.
6. If extraction fails, report the concrete reason: missing captions, private/unavailable video, geo restriction, dependency/network failure, rate limiting, or unsupported URL.

## Command Examples

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/youtube-script-extractor/scripts/extract_youtube_script.py" "https://www.youtube.com/watch?v=VIDEO_ID"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/youtube-script-extractor/scripts/extract_youtube_script.py" "https://youtu.be/VIDEO_ID" --lang ko,en --timestamps
python3 "${CODEX_HOME:-$HOME/.codex}/skills/youtube-script-extractor/scripts/extract_youtube_script.py" "URL" --cookies-from-browser chrome
python3 "${CODEX_HOME:-$HOME/.codex}/skills/youtube-script-extractor/scripts/extract_youtube_script.py" "URL" --output transcript.md
```

## Output Handling

- Save to `$YOUTUBE_TRANSCRIPT_INBOX` by default when set, otherwise save to the current directory. Use `--output <path>` to choose a file explicitly.
- Use Markdown with YAML frontmatter by default.
- Use no timestamps by default.
- End the note title and filename with `YouTube Transcript`.
- Use `youtube` and `transcript` tags. Do not add an `inbox` tag.
- Do not claim the transcript is complete if the video has no captions or only partial captions.

Default saved note format:

```md
---
title: "{video title} YouTube Transcript"
source: "{youtube url}"
type: transcript
created: YYYY-MM-DD
tags:
  - youtube
  - transcript
---

{transcript text}
```

## Implementation Notes

The script uses `yt-dlp` through an installed executable or `uv tool run --from yt-dlp yt-dlp`, so avoid creating a virtual environment. It downloads subtitle metadata only, not the video.
