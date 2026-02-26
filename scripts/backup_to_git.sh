#!/usr/bin/env bash
set -euo pipefail

# ARES backup: commit & push code/config/docs changes to Git.
# Notes:
# - Secrets/runtime are excluded by .gitignore (.ssh/, memory/, tmp/, logs/, .openclaw/)
# - This script is safe to run frequently; it no-ops when there are no changes.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

BRANCH="${BACKUP_BRANCH:-main}"
REMOTE="${BACKUP_REMOTE:-origin}"

# Ensure we're on the intended branch
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current_branch" != "$BRANCH" ]]; then
  echo "[backup] switching branch: $current_branch -> $BRANCH" >&2
  git checkout "$BRANCH" >/dev/null
fi

# Stage changes (gitignore will prevent secrets/runtime)
git add -A

# If nothing staged, exit
if git diff --cached --quiet; then
  echo "[backup] no changes to commit"
  exit 0
fi

ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
host="$(hostname 2>/dev/null || echo unknown)"
msg="backup(ares): auto-sync ${ts} (${host})"

git commit -m "$msg"

# Push if remote exists
if git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "[backup] pushing to ${REMOTE}/${BRANCH}"
  git push "$REMOTE" "$BRANCH"
else
  echo "[backup] remote '$REMOTE' not configured; committed locally only" >&2
fi
