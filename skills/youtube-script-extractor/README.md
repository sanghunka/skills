# youtube-script-extractor

Extract scripts, captions, subtitles, or transcript text from YouTube URLs.

## Install

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo sanghunka/skills \
  --path skills/youtube-script-extractor
```

Restart Codex after installing so the skill appears in new sessions.

## Usage

Ask Codex things like:

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
