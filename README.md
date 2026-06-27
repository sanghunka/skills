# Skills

Personal agent skills that can be installed selectively into Codex.

This repository is meant to be used as a skill catalog. You usually do not need to clone it manually. Ask Codex to install a skill from this repo, or run the install command for the specific skill path.

## Skills

### move-thread-codex

Move a local Codex thread to a different project/sidebar bucket by updating its stored cwd in SQLite and rollout JSONL with backups and verification.

Install:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo sanghunka/skills \
  --path skills/move-thread-codex
```

After installing, restart Codex so the skill appears in new sessions.

### publish-skill

Publish installed local Codex skills into a GitHub skills catalog repo.

Install:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo sanghunka/skills \
  --path skills/publish-skill
```

After installing, restart Codex so the skill appears in new sessions.

### youtube-script-extractor

Extract scripts, captions, subtitles, or transcript text from YouTube video URLs.

Install:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo sanghunka/skills \
  --path skills/youtube-script-extractor
```

After installing, restart Codex so the skill appears in new sessions.

## Repository Layout

```text
skills/
  move-thread-codex/
    SKILL.md
    scripts/
      move-thread-codex.sh
  publish-skill/
    SKILL.md
    agents/
      openai.yaml
    scripts/
      publish-skill.py
  youtube-script-extractor/
    SKILL.md
    agents/
      openai.yaml
    scripts/
      extract_youtube_script.py
```

Each skill is independently installable by path.
