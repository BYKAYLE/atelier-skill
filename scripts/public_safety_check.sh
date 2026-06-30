#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Atelier public skill safety check =="

echo "== forbidden runtime files =="
for path in SOT sessions daily logs .env .env.local .env.production; do
  if find . -path './.git' -prune -o -name "$path" -print | grep -q .; then
    find . -path './.git' -prune -o -name "$path" -print
    echo "Forbidden runtime file or directory found: $path" >&2
    exit 1
  fi
done

echo "== private key and token patterns =="
if rg -n --hidden \
  -g '!**/.git/**' \
  -g '!**/node_modules/**' \
  -g '!PUBLIC_SANITIZATION.md' \
  -g '!scripts/public_safety_check.sh' \
  -e '-----BEGIN [A-Z ]*PRIVATE KEY-----' \
  -e 'ghp_[A-Za-z0-9_]{20,}' \
  -e 'github_pat_[A-Za-z0-9_]{20,}' \
  -e '\bsk-[A-Za-z0-9_-]{20,}' \
  -e 'xox[baprs]-[A-Za-z0-9-]{20,}' \
  -e 'AIza[0-9A-Za-z_-]{20,}' \
  .; then
  echo "Potential secret value found." >&2
  exit 1
fi

echo "== machine-specific private paths =="
if rg -n --hidden \
  -g '!**/.git/**' \
  -g '!scripts/public_safety_check.sh' \
  -e '/Users/[A-Za-z0-9._-]+' \
  -e '[A-Za-z0-9._%+-]+@(gmail|naver|icloud|outlook|hotmail|daum|kakao)\.[A-Za-z]{2,}' \
  .; then
  echo "Private user path or personal contact found." >&2
  exit 1
fi

echo "OK: no hard secret values, private user paths, or runtime state found."
