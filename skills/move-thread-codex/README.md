# move-thread-codex

Move a local Codex Desktop thread to a different project in the sidebar by updating the thread's stored `cwd` in Codex state and its rollout JSONL metadata.

## Install

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo sanghunka/skills \
  --path skills/move-thread-codex
```

Restart Codex after installing so the skill appears in new sessions.

## Usage

Ask Codex things like:

```text
Move this thread to atodrop.
Move thread 019f02cd-f2e0-7353-b1d9-0a2c7d71bad5 to /path/to/project.
Move the AtoDrop thread to keepmoving.
```

The skill resolves the target thread and project path, backs up Codex state, updates the narrow thread row and rollout file, then verifies the move. If the active thread is moved, refresh or restart Codex if the sidebar does not update immediately.

## Details

Agent-facing workflow and safety rules live in [`SKILL.md`](SKILL.md).

## Scripts

- `scripts/move-thread-codex.sh`
