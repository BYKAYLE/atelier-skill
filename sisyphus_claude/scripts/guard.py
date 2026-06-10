#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path
from typing import Optional

STATE_DIR = Path("/tmp/sisyphus_claude_stop_guard")

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\brm\s+-fr\b",
    r"\brm\s+-rf[v]*\b",
    r"\brm\s+-fr[v]*\b",
    r"\bgit\s+reset\s+--hard(?=$|[\s'\";|)])",
    r"\bgit\s+checkout\s+--(?=$|[\s'\";|)])",
    r"\bgit\s+clean\s+-fd(?=$|[\s'\";|)])",
    r"\bgit\s+clean\s+-fdx(?=$|[\s'\";|)])",
    r"\bpush\s+--force\b",
    r"\bpush\s+--force-with-lease\b",
    r"\bchmod\s+777\b",
    r"\bchmod\s+-R\s+777\b",
    r"\bsudo\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"\bterraform\s+apply\b",
    r"\bkubectl\s+apply\b",
    r"\bhelm\s+upgrade\b",
    r"\bvercel\b.*\s--prod\b",
    r"\bnetlify\s+deploy\b.*\s--prod\b",
    r"\bfirebase\s+deploy\b",
    r"\b(gcloud|aws)\b.*\bdeploy\b",
]

INLINE_EXECUTION_PATTERNS = [
    r"\b(?:sh|bash|zsh)\s+-c\b",
    r"\beval\b",
    r"\bpython(?:3)?\s+-c\b",
    r"\bnode\s+-e\b",
]

INLINE_DANGEROUS_SNIPPETS = [
    r"rm\s+-r[fv]+",
    r"git\s+reset\s+--hard",
    r"git\s+checkout\s+--",
    r"git\s+clean\s+-fdx?",
    r"push\s+--force(?:-with-lease)?",
    r"terraform\s+apply",
    r"kubectl\s+apply",
    r"helm\s+upgrade",
    r"vercel[^\n]*--prod",
    r"netlify\s+deploy[^\n]*--prod",
    r"firebase\s+deploy",
]

ENCODING_OR_WRAPPER_PATTERNS = [
    r"base64\s+-d",
    r"openssl\s+enc",
    r"python(?:3)?\s+- <<",
    r"node\s+- <<",
    r"\$\(",
    r"`[^`]+`",
    r"<<['\"]?(?:EOF|SH|BASH|PY|NODE)['\"]?",
]

NESTED_EXECUTION_PATTERNS = [
    r"os\.system\(",
    r"subprocess\.(?:run|Popen|call)\(",
    r"execSync\(",
    r"spawnSync\(",
    r"ProcessBuilder\(",
]

ENCODED_EXECUTION_PATTERNS = [
    r"base64\s+-d[^\n]*\|[^\n]*\b(?:sh|bash|zsh)\b",
    r"openssl\s+enc[^\n]*\|[^\n]*\b(?:sh|bash|zsh)\b",
]

VERIFICATION_PATTERNS = [
    r'"command"\s*:\s*"[^"\\]*(npm\s+(run\s+)?test)',
    r'"command"\s*:\s*"[^"\\]*(pnpm\s+(run\s+)?test)',
    r'"command"\s*:\s*"[^"\\]*(yarn\s+test)',
    r'"command"\s*:\s*"[^"\\]*(bun\s+(run\s+)?test)',
    r'"command"\s*:\s*"[^"\\]*(pytest)',
    r'"command"\s*:\s*"[^"\\]*(cargo\s+test)',
    r'"command"\s*:\s*"[^"\\]*(go\s+test)',
    r'"command"\s*:\s*"[^"\\]*(npm\s+(run\s+)?build)',
    r'"command"\s*:\s*"[^"\\]*(pnpm\s+(run\s+)?build)',
    r'"command"\s*:\s*"[^"\\]*(yarn\s+build)',
    r'"command"\s*:\s*"[^"\\]*(bun\s+(run\s+)?build)',
    r'"command"\s*:\s*"[^"\\]*(cargo\s+build)',
    r'"command"\s*:\s*"[^"\\]*(go\s+build)',
    r'"command"\s*:\s*"[^"\\]*(tsc\s+--noEmit)',
    r'"command"\s*:\s*"[^"\\]*(eslint)',
    r'"command"\s*:\s*"[^"\\]*(biome)',
]

SIMPLE_VERIFICATION_PATTERNS = [
    r'"command"\s*:\s*"[^"\\]*(cat\s+)',
    r'"command"\s*:\s*"[^"\\]*(ls\s+)',
    r'"command"\s*:\s*"[^"\\]*(stat\s+)',
]

def load_input() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def read_transcript(path_value: str) -> str:
    if not path_value:
        return ""
    try:
        return Path(path_value).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def block(message: str) -> int:
    sys.stderr.write(message + "\n")
    return 2


def is_dangerous_command(command: str) -> bool:
    if any(re.search(pattern, command, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS):
        return True

    has_inline_wrapper = any(re.search(pattern, command, re.IGNORECASE) for pattern in INLINE_EXECUTION_PATTERNS)
    has_encoded_or_nested = any(
        re.search(pattern, command, re.IGNORECASE) for pattern in ENCODING_OR_WRAPPER_PATTERNS + NESTED_EXECUTION_PATTERNS
    )

    if any(re.search(pattern, command, re.IGNORECASE) for pattern in ENCODED_EXECUTION_PATTERNS):
        return True

    if has_inline_wrapper or has_encoded_or_nested:
        if any(re.search(pattern, command, re.IGNORECASE) for pattern in INLINE_DANGEROUS_SNIPPETS):
            return True

    return False


def session_marker_path(session_id: str) -> Optional[Path]:
    if not session_id:
        return None
    return STATE_DIR / f"{session_id}.marker"


def mark_stop_warned(session_id: str) -> None:
    marker = session_marker_path(session_id)
    if not marker:
        return
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        marker.write_text("warned\n", encoding="utf-8")
    except Exception:
        pass


def was_stop_warned(session_id: str) -> bool:
    marker = session_marker_path(session_id)
    return bool(marker and marker.exists())


def clear_stop_marker(session_id: str) -> None:
    marker = session_marker_path(session_id)
    if not marker or not marker.exists():
        return
    try:
        marker.unlink()
    except Exception:
        pass


def has_verification_evidence(transcript: str) -> bool:
    verification_patterns = VERIFICATION_PATTERNS + SIMPLE_VERIFICATION_PATTERNS + [
        r'"name":"Read"',
        r'"command"\s*:\s*"[^"\\]*(test\s+-f)',
        r'"command"\s*:\s*"[^"\\]*(diff\s+)',
    ]
    return any(re.search(pattern, transcript, re.IGNORECASE) for pattern in verification_patterns)


def handle_pretooluse() -> int:
    input_data = load_input()
    if str(input_data.get("tool_name") or "") != "Bash":
        return 0

    tool_input = input_data.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    if is_dangerous_command(command):
        return block(
            "`sisyphus_claude` guard blocked a risky Bash command. "
            "Ask the user first for destructive operations, external auth, or irreversible deploy/security/billing actions."
        )

    return 0


def handle_stop() -> int:
    input_data = load_input()
    session_id = str(input_data.get("session_id") or "")
    transcript_path = str(input_data.get("transcript_path") or "")
    transcript = read_transcript(transcript_path)
    if not transcript:
        clear_stop_marker(session_id)
        return 0

    edited_patterns = [
        r'"tool_name":"Edit"',
        r'"tool_name":"Write"',
        r'"tool_name":"MultiEdit"',
        r'"name":"Edit"',
        r'"name":"Write"',
        r'"name":"MultiEdit"',
    ]
    edited = any(re.search(pattern, transcript) for pattern in edited_patterns)
    if not edited:
        clear_stop_marker(session_id)
        return 0

    if was_stop_warned(session_id):
        return 0

    verified = has_verification_evidence(transcript)
    if verified:
        clear_stop_marker(session_id)
        return 0

    mark_stop_warned(session_id)

    return block(
        "`sisyphus_claude` guard blocked the first stop after edits because clear verification evidence was not found yet. "
        "Run proportionate verification for the actual task scope, then finish again."
    )


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "pretooluse":
        return handle_pretooluse()
    if mode == "stop":
        return handle_stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
