---
name: youtube-script-extractor
description: Extract scripts, captions, subtitles, or transcript text from YouTube video URLs. Use when the user asks to pull a YouTube script, get a transcript, summarize from video captions, save captions as Markdown/text, or process a YouTube URL such as youtube.com/watch or youtu.be.
---

# YouTube Script Extractor

## Workflow

1. Read `format.md` in full before saving or presenting transcript output. Treat it as the source of truth for note format.
2. Run `scripts/extract_youtube_script.py <youtube-url>` for the requested video.
3. Prefer manually authored subtitles over auto-generated captions unless the user requests otherwise.
4. Select language with `--lang <code>` when requested. Use `ko` for Korean, `en` for English, or a comma-separated fallback list such as `ko,en`.
5. Use `--timestamps` when the user needs a study script, quote lookup, or citation-friendly output. Omit timestamps for clean prose unless `format.md` says otherwise.
6. If YouTube returns HTTP 429, login, bot-check, or private-video errors, retry with `--cookies-from-browser chrome` or another browser that has YouTube access.
7. If extraction fails, report the concrete reason: missing captions, private/unavailable video, geo restriction, dependency/network failure, rate limiting, or unsupported URL.

## Command Examples

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/youtube-script-extractor/scripts/extract_youtube_script.py" "https://www.youtube.com/watch?v=VIDEO_ID"
python "${CODEX_HOME:-$HOME/.codex}/skills/youtube-script-extractor/scripts/extract_youtube_script.py" "https://youtu.be/VIDEO_ID" --lang ko,en --timestamps
python "${CODEX_HOME:-$HOME/.codex}/skills/youtube-script-extractor/scripts/extract_youtube_script.py" "URL" --cookies-from-browser chrome
python "${CODEX_HOME:-$HOME/.codex}/skills/youtube-script-extractor/scripts/extract_youtube_script.py" "URL" --output transcript.md
```

## Output Handling

- Follow `format.md` for saved Markdown note structure.
- Save to `$YOUTUBE_TRANSCRIPT_INBOX` by default when set, otherwise save to the current directory. Use `--output <path>` to choose a file explicitly.
- The bundled script reads the first fenced `md` block in `format.md` as its saved-note template.
- If the user modifies `format.md`, honor that file over older examples or assumptions.

## Implementation Notes

The script uses `yt-dlp` through an installed executable or `uv tool run --from yt-dlp yt-dlp`, so avoid creating a virtual environment. It downloads subtitle metadata only, not the video.
