# youtube-script-extractor

Extract scripts, captions, subtitles, or transcript text from YouTube URLs.

## Use With An Agent

Give this README URL to your agent (Codex, Claude Code, or another skill-aware agent) and ask it to install or use the skill:

https://github.com/sanghunka/skills/tree/main/skills/youtube-script-extractor

## Usage

Ask your agent things like:

```text
Get the transcript for this YouTube video.
Extract Korean captions from https://youtu.be/VIDEO_ID.
Save this video's script as Markdown with timestamps.
```

Direct script examples:

```bash
python3 ~/.codex/skills/youtube-script-extractor/scripts/extract_youtube_script.py "https://www.youtube.com/watch?v=VIDEO_ID"
python3 ~/.codex/skills/youtube-script-extractor/scripts/extract_youtube_script.py "https://youtu.be/VIDEO_ID" --lang ko,en --timestamps
python3 ~/.codex/skills/youtube-script-extractor/scripts/extract_youtube_script.py "URL" --cookies-from-browser chrome
```

By default, output is Markdown with frontmatter. Set `YOUTUBE_TRANSCRIPT_INBOX` or pass `--output <path>` to choose where files are saved.

## Details

Agent-facing workflow and failure handling live in [`SKILL.md`](SKILL.md).

## Scripts

- `scripts/extract_youtube_script.py`
