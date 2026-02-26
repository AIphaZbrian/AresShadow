#!/usr/bin/env bash
set -euo pipefail

# Minimal placeholder script to bootstrap the MVP dev environment.
# TODO: replace with real setup once container definitions are ready.

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"

if [ ! -d "$VENV_DIR" ]; then
  if ! python3 -m venv "$VENV_DIR" >/dev/null 2>&1; then
    echo "[bootstrap] python3 -m venv failed; installing virtualenv fallback"
    python3 -m pip install --user virtualenv >/dev/null
    python3 -m virtualenv "$VENV_DIR"
  fi
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip

# Install placeholder dependencies
pip install requests python-dotenv pyyaml "psycopg[binary]"

echo "[bootstrap] virtualenv ready at $VENV_DIR"
echo "[bootstrap] add real dependency list once MVP modules are committed"
