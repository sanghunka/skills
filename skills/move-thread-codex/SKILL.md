---
name: move-thread-codex
description: Move a local Codex thread to a different project/sidebar bucket by updating its stored cwd in SQLite and rollout JSONL with backups and verification. Use when the user asks to move an existing Codex thread to another project, change where a thread appears in the Projects sidebar, rename a Codex thread cwd/project path, move Codex history after a local repo rename, or mentions state_5.sqlite, rollout JSONL, or Codex thread path migration.
---

# Move Thread Codex

Use this skill only for local Codex Desktop thread metadata. It edits global Codex state, so stay narrow and reversible.

## Quick Start

Natural user inputs this skill should handle:

```text
Move this thread to atodrop.
Move this thread to /path/to/atodrop.
Move thread 019f... to atodrop.
Move the AtoDrop thread to keepmoving.
```

User-facing inputs are:

- Target thread: explicit thread id, "this thread", or a uniquely searchable title/preview.
- Target project: project label from `list_projects`/sidebar, or an absolute path.

For normal project moves, the helper script takes the resolved thread id and target absolute path. It infers the old path from `threads.cwd`:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/move-thread-codex/scripts/move-thread-codex.sh \
  019f02cd-f2e0-7353-b1d9-0a2c7d71bad5 \
  /path/to/new-project
```

Use the three-argument form only for explicit text/name rewrites:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/move-thread-codex/scripts/move-thread-codex.sh \
  019f02cd-f2e0-7353-b1d9-0a2c7d71bad5 \
  atodrop-kit \
  atodrop
```

The helper backs up the SQLite database and rollout JSONL, updates the target thread row in `state_5.sqlite`, replaces the old string in that thread's rollout JSONL, checkpoints SQLite, and verifies the old string is gone from those targets.

## Workflow

1. Resolve the thread first.

- For an explicit id, use it directly.
- For "this thread", use Codex thread tools to identify the current active thread. Confirm by reading recent turns and matching the user's current request.
- For a title/preview, search/list threads and require a unique match.
- If the thread cannot be resolved confidently, ask for the thread id.

Use the Codex app API when available:

```text
read_thread(threadId=...)
```

Record the current `cwd`, `title`, and whether the thread is idle.

2. Resolve the target project/path.

- If the user gives an absolute path, use it.
- If the user gives a project label such as `atodrop`, resolve it through `list_projects` when available. Require exactly one exact label match first, then exactly one path basename match.
- If multiple projects match, ask for the exact path.

3. Locate storage:

```bash
sqlite3 "$HOME/.codex/state_5.sqlite" \
  "SELECT id, cwd, rollout_path FROM threads WHERE id='<thread-id>';"
```

The sidebar/project grouping is driven primarily by `threads.cwd`. The transcript metadata also stores `cwd` in the rollout JSONL.

4. Run the helper script. For normal project moves, pass two arguments after resolving the thread and target:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/move-thread-codex/scripts/move-thread-codex.sh \
  <thread-id> \
  <target-absolute-path>
```

For a repo rename that also appears in messages, use the three-argument form with old/new name strings such as `atodrop-kit` and `atodrop`.

5. Verify through both storage and the Codex app API:

```bash
sqlite3 "$HOME/.codex/state_5.sqlite" \
  "SELECT id, cwd, rollout_path FROM threads WHERE id='<thread-id>';"
rg -n '<old-string>' '<rollout-path>' || true
```

Then call `read_thread(threadId=...)` again. If the sidebar still shows the old project, restart or refresh Codex Desktop, because the UI can cache project buckets.

## Moving The Current Thread

When the target is "this thread" or the currently active thread, warn before making changes:

```text
I can move this thread to <target>. Because this changes the active thread's stored Codex project path, the current session may need to be refreshed/reopened, or Codex Desktop may need to be restarted, before the left sidebar reflects the move. I will do the move now and then stop after verification.
```

Then perform the move as the final meaningful action in the turn. This is a preflight notice, not a blocking confirmation, unless the user explicitly asked to confirm before proceeding.

After the move, the stored metadata points at the new project path, but the already-running Codex session may still have runtime state from the old project. Tell the user to refresh/reopen the thread, or restart Codex Desktop if the sidebar does not immediately update. Do not continue doing repo work in the same turn after moving the active thread unless the user explicitly asks.

## Safety Rules

- Never touch paths containing `/.private`.
- Never mass-replace all Codex databases by default. Update the target `threads` row and its `rollout_path` JSONL only.
- Always create backups before mutation.
- Do not edit SQLite with plain text tools. Use `sqlite3` transactions.
- Do not rewrite historical git data or project files unless the user explicitly asks.
- If the helper cannot resolve a rollout path, stop and explain the exact missing metadata.
