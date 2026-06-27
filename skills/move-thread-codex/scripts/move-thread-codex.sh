#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage:
  move-thread-codex.sh <thread-id> <target-absolute-path>
  move-thread-codex.sh <thread-id> <old-string> <new-string>

Example:
  move-thread-codex.sh 019f02cd-f2e0-7353-b1d9-0a2c7d71bad5 \
    /path/to/atodrop

  move-thread-codex.sh 019f02cd-f2e0-7353-b1d9-0a2c7d71bad5 \
    atodrop-kit \
    atodrop
EOF
}

if [[ $# -ne 2 && $# -ne 3 ]]; then
  usage
  exit 2
fi

thread_id=$1
if [[ $# -eq 2 ]]; then
  old_value=""
  new_value=$2
  infer_old_value=1
else
  old_value=$2
  new_value=$3
  infer_old_value=0
fi
codex_home=${CODEX_HOME:-"$HOME/.codex"}
state_db="$codex_home/state_5.sqlite"

sql_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

thread_id_sql=$(sql_escape "$thread_id")

case "$old_value $new_value $state_db" in
  *"/.private"*)
    echo "Refusing to operate on forbidden private paths." >&2
    exit 1
    ;;
esac

if [[ ! -f "$state_db" ]]; then
  echo "Missing Codex state database: $state_db" >&2
  exit 1
fi

row_count=$(sqlite3 "$state_db" "SELECT COUNT(*) FROM threads WHERE id='$thread_id_sql';")
if [[ "$row_count" != "1" ]]; then
  echo "Expected exactly one thread row for $thread_id, found $row_count." >&2
  exit 1
fi

current_cwd=$(sqlite3 "$state_db" "SELECT cwd FROM threads WHERE id='$thread_id_sql';")
rollout_path=$(sqlite3 "$state_db" "SELECT rollout_path FROM threads WHERE id='$thread_id_sql';")
if [[ -z "$rollout_path" ]]; then
  echo "Thread has no rollout_path: $thread_id" >&2
  exit 1
fi
if [[ ! -f "$rollout_path" ]]; then
  echo "Missing rollout JSONL: $rollout_path" >&2
  exit 1
fi

if [[ "$infer_old_value" == "1" ]]; then
  if [[ "$new_value" != /* ]]; then
    echo "Target must be an absolute path when old-string is inferred. Resolve project labels before calling this script." >&2
    exit 2
  fi
  old_value=$current_cwd
fi

case "$old_value $new_value $state_db" in
  *"/.private"*)
    echo "Refusing to operate on forbidden private paths." >&2
    exit 1
    ;;
esac

if [[ "$old_value" == "$new_value" ]]; then
  echo "No move needed: thread $thread_id is already at $new_value"
  sqlite3 -header -column "$state_db" "SELECT id, cwd, rollout_path FROM threads WHERE id='$thread_id_sql';"
  exit 0
fi

old_value_sql=$(sql_escape "$old_value")
new_value_sql=$(sql_escape "$new_value")

timestamp=$(date +%Y%m%d-%H%M%S)
db_backup="${state_db}.bak-thread-path-${timestamp}"
jsonl_backup="${rollout_path}.bak-thread-path-${timestamp}"

sqlite3 "$state_db" ".backup '$db_backup'"
cp -p "$rollout_path" "$jsonl_backup"

sqlite3 "$state_db" <<SQL
BEGIN IMMEDIATE;
UPDATE threads
SET
  cwd = replace(cwd, '$old_value_sql', '$new_value_sql'),
  title = replace(title, '$old_value_sql', '$new_value_sql'),
  first_user_message = replace(first_user_message, '$old_value_sql', '$new_value_sql'),
  preview = replace(preview, '$old_value_sql', '$new_value_sql'),
  git_origin_url = replace(git_origin_url, '$old_value_sql', '$new_value_sql'),
  agent_path = replace(agent_path, '$old_value_sql', '$new_value_sql')
WHERE id = '$thread_id_sql';
COMMIT;
SQL

sqlite3 "$state_db" "PRAGMA wal_checkpoint(TRUNCATE);" >/dev/null

OLD_VALUE="$old_value" NEW_VALUE="$new_value" perl -0pi -e 'BEGIN { $old = $ENV{"OLD_VALUE"}; $new = $ENV{"NEW_VALUE"}; } s/\Q$old\E/$new/g' "$rollout_path"

sqlite_remaining=$(sqlite3 "$state_db" "SELECT COUNT(*) FROM threads WHERE id='$thread_id_sql' AND (instr(cwd, '$old_value_sql') > 0 OR instr(title, '$old_value_sql') > 0 OR instr(first_user_message, '$old_value_sql') > 0 OR instr(preview, '$old_value_sql') > 0 OR instr(COALESCE(git_origin_url, ''), '$old_value_sql') > 0 OR instr(COALESCE(agent_path, ''), '$old_value_sql') > 0);")
jsonl_remaining=$( (rg -F "$old_value" "$rollout_path" || true) | wc -l | tr -d ' ')

echo "SQLite backup: $db_backup"
echo "JSONL backup: $jsonl_backup"
echo "Thread row:"
sqlite3 -header -column "$state_db" "SELECT id, cwd, rollout_path FROM threads WHERE id='$thread_id_sql';"
echo "Remaining old string in target SQLite row: $sqlite_remaining"
echo "Remaining old string in rollout JSONL: $jsonl_remaining"

if [[ "$sqlite_remaining" != "0" || "$jsonl_remaining" != "0" ]]; then
  echo "Migration completed with remaining old-string references. Inspect before continuing." >&2
  exit 1
fi
