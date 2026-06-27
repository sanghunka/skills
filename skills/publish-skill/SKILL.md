---
name: publish-skill
description: Publish installed local agent skills into a GitHub skills catalog repo. Use when the user asks to add, copy, export, publish, share, or sync an existing skill into a skills repository, update the repo README install instructions, or make a local skill distributable from GitHub.
---

# Publish Skill

Use this skill to move an already-installed local agent skill into a GitHub-hosted skills catalog, usually `sanghunka/skills`.

## Workflow

1. Identify the installed skill name and repo root.
   - Source defaults to `${CODEX_HOME:-$HOME/.codex}/skills/<skill-name>`.
   - Repo defaults to `$SKILLS_REPO_ROOT`, then the current directory if it looks like a skills repo, then `$HOME/Documents/git-repo/skills`.
2. Read the source skill files that require judgment before publishing.
   - For normal publishing, read `SKILL.md` in full.
   - Read scripts or references only when portability changes are needed.
3. Run the helper:

```bash
python3 ${CODEX_HOME:-$HOME/.codex}/skills/publish-skill/scripts/publish-skill.py <skill-name>
```

4. Review portability warnings. Replace personal absolute paths, machine-specific defaults, credentials, generated files, and private project assumptions before committing.
5. Validate and publish. If the user asked for a full GitHub update, rerun with:

```bash
python3 ${CODEX_HOME:-$HOME/.codex}/skills/publish-skill/scripts/publish-skill.py <skill-name> --commit --push
```

## Helper Behavior

`scripts/publish-skill.py` performs the deterministic parts:

- Copies the skill into `skills/<skill-name>` in the repo.
- Excludes generated or local-only junk such as `.DS_Store`, `__pycache__`, `*.pyc`, `.git`, and backup files.
- Refuses to replace an existing target skill directory if that path has uncommitted git changes, unless `--force` is passed.
- Regenerates the root README as a compact skill index.
- Creates a per-skill `README.md` that users can hand to an agent when the target skill does not already have one.
- Runs `quick_validate.py` when available.
- Runs `python3 -m py_compile` for Python scripts and `bash -n` for shell scripts.
- Warns on likely personal absolute paths in copied files.
- Optionally commits and pushes with `--commit --push`.

## Inputs

Prefer natural-language usage:

- "Add `youtube-script-extractor` to the skills repo."
- "Publish this installed skill to GitHub."
- "Sync `move-thread-codex` into `sanghunka/skills`."

If the skill name is omitted, infer it only when the current working directory is inside a skill folder containing `SKILL.md`; otherwise ask for the skill name.

Common options:

```bash
--repo-root /path/to/skills-repo
--source-root /path/to/codex/skills
--repo owner/name
--dest-name different-skill-name
--force
--commit
--push
--strict-portability
--skip-skill-readme
```

## Publishing Rules

- Keep the root README concise: list skills and link to each skill folder for details.
- Keep per-skill usage details in `skills/<skill-name>/README.md`.
- Prefer "give this README URL to your agent" instructions over tool-specific install commands in public READMEs.
- Keep skill folders self-contained: `SKILL.md`, optional `agents/`, optional `scripts/`, optional `references/`, optional `assets/`.
- Do not publish generated caches, local backups, secrets, or machine-specific absolute paths.
- Do not rewrite unrelated README prose by hand after the helper has regenerated the catalog.
