#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--reset" ]]; then
  bash "$HOME/.claude/skills/sisyphus_claude/scripts/reset_fixtures.sh"
fi

echo "[info] Use --reset to restore fixture baselines before running the suite."

echo "[1/5] node fixture baseline"
node --test "/private/tmp/sisyphus_claude_fixture_node/test/message.test.js"

echo "[2/5] python fixture baseline"
PYTHONPATH="/private/tmp/sisyphus_claude_fixture_python" python3 -m unittest discover -s "/private/tmp/sisyphus_claude_fixture_python/tests"

echo "[3/5] service fixture baseline"
npm --prefix "/private/tmp/sisyphus_claude_fixture_service" test

echo "[4/5] guard syntax"
python3 -m py_compile "$HOME/.claude/skills/sisyphus_claude/scripts/guard.py"

echo "[5/5] guard red-team checks"
python3 "$HOME/.claude/skills/sisyphus_claude/scripts/run_redteam_guard_checks.py"

echo "Smoke suite complete"
