# publish-skill

Publish an installed local Codex skill into this GitHub skills catalog.

## Install

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo sanghunka/skills \
  --path skills/publish-skill
```

Restart Codex after installing so the skill appears in new sessions.

## Usage

Ask Codex things like:

```text
Add youtube-script-extractor to the skills repo.
Publish this installed skill to GitHub.
Sync move-thread-codex into sanghunka/skills.
```

The helper copies `${CODEX_HOME:-$HOME/.codex}/skills/<skill-name>` into `skills/<skill-name>`, skips generated files, validates `SKILL.md`, runs syntax checks for scripts, warns on likely personal absolute paths, updates the root README index, and creates a per-skill README when needed.

Common direct command:

```bash
python3 ~/.codex/skills/publish-skill/scripts/publish-skill.py <skill-name> --commit --push
```

Agent-facing workflow and implementation details live in [`SKILL.md`](SKILL.md).

## Scripts

- `scripts/publish-skill.py`
