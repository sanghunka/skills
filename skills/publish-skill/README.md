# publish-skill

Publish an installed local agent skill into this GitHub skills catalog.

## Use With An Agent

Give this README URL to your agent (Codex, Claude Code, or another skill-aware agent) and ask it to install or use the skill:

https://github.com/sanghunka/skills/tree/main/skills/publish-skill

## Usage

Ask your agent things like:

```text
Add youtube-script-extractor to the skills repo.
Publish this installed skill to GitHub.
Sync move-thread-codex into sanghunka/skills.
```

The helper copies a local skill folder into `skills/<skill-name>`, skips generated files, validates `SKILL.md`, runs syntax checks for scripts, warns on likely personal absolute paths, updates the root README index, and creates a per-skill README when needed. By default, it reads from `${CODEX_HOME:-$HOME/.codex}/skills`, but `--source-root` can point elsewhere.

Common direct command:

```bash
python3 ~/.codex/skills/publish-skill/scripts/publish-skill.py <skill-name> --commit --push
```

Agent-facing workflow and implementation details live in [`SKILL.md`](SKILL.md).

## Scripts

- `scripts/publish-skill.py`
