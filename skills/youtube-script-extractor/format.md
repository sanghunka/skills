# Transcript Output Format

Use this file as the source of truth for saved transcript notes.

## Rules

- Save transcript notes as Markdown.
- Preserve the transcript language and wording. Do not summarize or translate unless the user explicitly asks.
- Use no timestamps by default.
- When timestamps are requested, write each transcript row as `[MM:SS] text` or `[HH:MM:SS] text`.
- Do not add an `inbox` tag.
- Do not claim the transcript is complete when captions are missing or partial.

## Template

The bundled script uses the first fenced `md` block below as the saved-note template.

Available placeholders:

- `{note_title_yaml}`: YAML-quoted note title, normally `{video title} YouTube Transcript`
- `{source_yaml}`: YAML-quoted source URL
- `{created}`: ISO date
- `{transcript}`: extracted transcript text

```md
---
title: {note_title_yaml}
source: {source_yaml}
type: transcript
created: {created}
tags:
  - youtube
  - transcript
---

{transcript}
```
