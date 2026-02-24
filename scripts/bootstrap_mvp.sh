#!/usr/bin/env bash
set -euo pipefail

# Minimal placeholder script to bootstrap the MVP dev environment.
# TODO: replace with real setup once container definitions are ready.

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip

# Install placeholder dependencies
pip install requests python-dotenv

echo "[bootstrap] virtualenv ready at $VENV_DIR"
echo "[bootstrap] add real dependency list once MVP modules are committed"
