#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PY="$SKILL_DIR/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
  python3 -m venv "$SKILL_DIR/.venv"
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install playwright pyyaml pillow jinja2
  "$PY" -m playwright install chromium
fi

exec "$PY" "$SCRIPT_DIR/run_probe.py" "$@"

