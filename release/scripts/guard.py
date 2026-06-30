#!/usr/bin/env python3
"""release guard — PreToolUse + Stop hooks.

Adapted from sisyphus_claude guard.py with orchestrator-specific additions:
- Same dangerous command blocking (PreToolUse)
- Stop hook: verifies quality gate evidence before allowing completion
- v3.0: Playbook backup verification (v2.0 meta-rules → v3.0 playbooks)
- v4.0: Session log existence check (Incremental Recording enforcement)
"""
import json
import hashlib
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

STATE_DIR = Path("/tmp/bykayle_release_stop_guard")
SESSIONS_DIR = Path.home() / ".claude/skills/release/SOT/sessions"

# ── Dangerous Patterns (shared with sisyphus_claude) ────────────────────

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf[v]*\b", r"\brm\s+-fr[v]*\b",
    r"\bgit\s+reset\s+--hard(?=$|[\s'\";|)])",
    r"\bgit\s+checkout\s+--(?=$|[\s'\";|)])",
    r"\bgit\s+clean\s+-fd(?=$|[\s'\";|)])",
    r"\bgit\s+clean\s+-fdx(?=$|[\s'\";|)])",
    r"\bpush\s+--force\b", r"\bpush\s+--force-with-lease\b",
    r"\bchmod\s+777\b", r"\bchmod\s+-R\s+777\b",
    r"\bsudo\b", r"\bmkfs\b", r"\bdd\s+if=",
    r"\bterraform\s+apply\b", r"\bkubectl\s+apply\b",
    r"\bhelm\s+upgrade\b",
    r"\bvercel\b.*\s--prod\b",
    r"\bnetlify\s+deploy\b.*\s--prod\b",
    r"\bfirebase\s+deploy\b",
    r"\b(gcloud|aws)\b.*\bdeploy\b",
    r"\bdocker\s+compose\b[^\n;]*\bdown\b[^\n;]*\s-v\b",
    r"\bdocker\s+volume\s+(?:rm|remove|prune)\b",
    r"\bdocker\s+system\s+prune\b[^\n;]*--volumes\b",
    r"\bdocker\s+compose\b[^\n;]*\brm\b[^\n;]*\s-v\b",
    r"\bterraform\s+destroy\b",
    r"\bkubectl\s+delete\b[^\n;]*(?:pvc|persistentvolumeclaim|pv|persistentvolume|namespace|ns)\b",
    r"\bhelm\s+uninstall\b",
    r"\bprisma\s+migrate\s+reset\b",
    r"\brails\s+db:(?:drop|reset)\b",
]

INLINE_EXECUTION_PATTERNS = [
    r"\b(?:sh|bash|zsh)\s+-c\b", r"\beval\b",
    r"\bpython(?:3)?\s+-c\b", r"\bnode\s+-e\b",
]

INLINE_DANGEROUS_SNIPPETS = [
    r"rm\s+-r[fv]+", r"git\s+reset\s+--hard",
    r"git\s+checkout\s+--", r"git\s+clean\s+-fdx?",
    r"push\s+--force(?:-with-lease)?",
    r"terraform\s+apply", r"kubectl\s+apply", r"helm\s+upgrade",
    r"vercel[^\n]*--prod", r"netlify\s+deploy[^\n]*--prod",
    r"firebase\s+deploy",
    r"docker\s+compose[^\n;]*down[^\n;]*\s-v",
    r"docker\s+volume\s+(?:rm|remove|prune)",
    r"DROP\s+(?:DATABASE|SCHEMA|TABLE)",
    r"TRUNCATE\s+(?:TABLE\s+)?[A-Za-z0-9_\".`-]+",
    r"DELETE\s+FROM\s+[A-Za-z0-9_\".`-]+",
    r"db\.dropDatabase\s*\(",
    r"FLUSH(?:ALL|DB)",
]

ENCODING_OR_WRAPPER_PATTERNS = [
    r"base64\s+-d", r"openssl\s+enc",
    r"python(?:3)?\s+- <<", r"node\s+- <<",
    r"\$\(", r"`[^`]+`",
    r"<<['\"]?(?:EOF|SH|BASH|PY|NODE)['\"]?",
]

# ── Safe Patterns (오케스트레이터 직접 실행 시 허용) ──────────────────
# private-deployment-skill 크리덴셜 참조에 등록된 키체인 항목 읽기 (비파괴 작업)
SAFE_PATTERNS = [
    r"security\s+find-generic-password(?:\s+(?:-[A-Za-z](?:\s+\S+)?|\S+))*",  # macOS Keychain 읽기 전용
]

NESTED_EXECUTION_PATTERNS = [
    r"os\.system\(", r"subprocess\.(?:run|Popen|call)\(",
    r"execSync\(", r"spawnSync\(", r"ProcessBuilder\(",
]

ENCODED_EXECUTION_PATTERNS = [
    r"base64\s+-d[^\n]*\|[^\n]*\b(?:sh|bash|zsh)\b",
    r"openssl\s+enc[^\n]*\|[^\n]*\b(?:sh|bash|zsh)\b",
]

DB_CLIENT_PATTERN = r"\b(?:psql|mysql|mariadb|sqlite3|duckdb|mongosh|mongo|redis-cli|dropdb)\b"
DB_DESTRUCTIVE_SQL_PATTERN = (
    r"\b(?:DROP\s+(?:DATABASE|SCHEMA|TABLE)|TRUNCATE\s+(?:TABLE\s+)?"
    r"|DELETE\s+FROM|FLUSH(?:ALL|DB)|db\.dropDatabase\s*\(|db\.[A-Za-z0-9_]+\.drop\s*\()"
)

# ── Verification Evidence Patterns ──────────────────────────────────────

VERIFICATION_PATTERNS = [
    r'"command"\s*:\s*"[^"\\]*(npm\s+(run\s+)?test)',
    r'"command"\s*:\s*"[^"\\]*(pnpm\s+(run\s+)?test)',
    r'"command"\s*:\s*"[^"\\]*(pytest)',
    r'"command"\s*:\s*"[^"\\]*(cargo\s+test)',
    r'"command"\s*:\s*"[^"\\]*(go\s+test)',
    r'"command"\s*:\s*"[^"\\]*(npm\s+(run\s+)?build)',
    r'"command"\s*:\s*"[^"\\]*(pnpm\s+(run\s+)?build)',
    r'"command"\s*:\s*"[^"\\]*(cargo\s+build)',
    r'"command"\s*:\s*"[^"\\]*(go\s+build)',
    r'"command"\s*:\s*"[^"\\]*(tsc\s+--noEmit)',
    r'"command"\s*:\s*"[^"\\]*(eslint)',
    r'"command"\s*:\s*"[^"\\]*(biome)',
    r'"command"\s*:\s*"[^"\\]*(mypy)',
    r'"command"\s*:\s*"[^"\\]*(ruff\s+check)',
    r'"command"\s*:\s*"[^"\\]*(cargo\s+check)',
    r'"command"\s*:\s*"[^"\\]*(cargo\s+clippy)',
    r'"command"\s*:\s*"[^"\\]*(golangci-lint)',
    r'"command"\s*:\s*"[^"\\]*(docker\s+compose\s+build)',
    r'"command"\s*:\s*"[^"\\]*(compileall)',
]

SIMPLE_VERIFICATION_PATTERNS = [
    r'"command"\s*:\s*"[^"\\]*(test\s+-f)',
    r'"command"\s*:\s*"[^"\\]*(test\s+-s)',
    r'"command"\s*:\s*"[^"\\]*(wc\s+-c)',
    r'"command"\s*:\s*"[^"\\]*(jq\s+)',
    r'"command"\s*:\s*"[^"\\]*(python(?:3)?\s+-m\s+json\.tool)',
    r'"command"\s*:\s*"[^"\\]*(diff\s+)',
]

PROBE_VERIFICATION_PATTERNS = [
    r'"command"\s*:\s*"[^"\\]*(run_probe\.sh|run_probe\.py|/probe\b|probe\s+)',
    r'"command"\s*:\s*"[^"\\]*(playwright\s+test)',
    r'"command"\s*:\s*"[^"\\]*(vitest\s+run)',
    r'"command"\s*:\s*"[^"\\]*(python(?:3)?\s+-m\s+py_compile)',
    r'"command"\s*:\s*"[^"\\]*(python(?:3)?\s+-m\s+compileall)',
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


def is_exact_safe_command(command: str) -> bool:
    stripped = command.strip()
    if re.search(r"(?:;|&&|\|\||\||`|\$\(|\n)", stripped):
        return False
    return any(re.fullmatch(p, stripped, re.IGNORECASE) for p in SAFE_PATTERNS)


def is_dangerous_command(command: str) -> bool:
    if any(re.search(p, command, re.IGNORECASE) for p in DANGEROUS_PATTERNS):
        return True

    if re.search(DB_CLIENT_PATTERN, command, re.IGNORECASE) and re.search(DB_DESTRUCTIVE_SQL_PATTERN, command, re.IGNORECASE):
        return True

    if any(re.search(p, command, re.IGNORECASE) for p in ENCODED_EXECUTION_PATTERNS):
        return True

    has_wrapper = any(
        re.search(p, command, re.IGNORECASE)
        for p in INLINE_EXECUTION_PATTERNS + ENCODING_OR_WRAPPER_PATTERNS + NESTED_EXECUTION_PATTERNS
    )
    if has_wrapper:
        if any(re.search(p, command, re.IGNORECASE) for p in INLINE_DANGEROUS_SNIPPETS):
            return True

    if is_exact_safe_command(command):
        return False

    return False


def session_marker_path(session_id: str, transcript_path: str = "") -> Optional[Path]:
    raw = session_id or transcript_path
    if not raw:
        return None
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return STATE_DIR / f"{digest}.marker"


def mark_stop_warned(session_id: str, transcript_path: str = "") -> None:
    marker = session_marker_path(session_id, transcript_path)
    if not marker:
        return
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        marker.write_text("warned\n", encoding="utf-8")
    except Exception:
        pass


def was_stop_warned(session_id: str, transcript_path: str = "") -> bool:
    marker = session_marker_path(session_id, transcript_path)
    return bool(marker and marker.exists())


def clear_stop_marker(session_id: str, transcript_path: str = "") -> None:
    marker = session_marker_path(session_id, transcript_path)
    if not marker or not marker.exists():
        return
    try:
        marker.unlink()
    except Exception:
        pass


def has_verification_evidence(transcript: str) -> bool:
    all_patterns = (
        VERIFICATION_PATTERNS
        + SIMPLE_VERIFICATION_PATTERNS
        + PROBE_VERIFICATION_PATTERNS
    )
    return any(re.search(p, transcript, re.IGNORECASE) for p in all_patterns)


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
            "`release` guard blocked a risky Bash command. "
            "Ask the user first for destructive operations, external auth, "
            "or irreversible deploy/security/billing actions."
        )
    return 0


def _today_date_alternation() -> str:
    """v4.1 (260610): 실존 세션 파일은 전부 YYMMDD 형식(session-260610-*.md)인데
    구버전이 %Y-%m-%d만 인정해 매 release 세션이 stop에서 1회 오차단되던 버그 수정.
    두 형식 모두 인정한다."""
    now = datetime.now()
    return f"(?:{now.strftime('%Y-%m-%d')}|{now.strftime('%y%m%d')})"


def has_session_log_today() -> bool:
    """v4.0: Check if a session log file exists for today."""
    if not SESSIONS_DIR.exists():
        return False
    pattern = re.compile(rf"^session-{_today_date_alternation()}.*\.md$")
    return any(pattern.match(p.name) for p in SESSIONS_DIR.glob("session-*.md"))


def has_session_log_for_transcript(transcript: str) -> bool:
    """Require evidence that this transcript created or touched today's release log."""
    if not SESSIONS_DIR.exists():
        return False
    candidates = set(re.findall(rf"(?:SOT/sessions/)?(session-{_today_date_alternation()}[^\"'\s]*\.md)", transcript))
    return any((SESSIONS_DIR / Path(candidate).name).exists() for candidate in candidates)


def handle_stop() -> int:
    input_data = load_input()
    session_id = str(input_data.get("session_id") or "")
    transcript_path = str(input_data.get("transcript_path") or "")
    transcript = read_transcript(transcript_path)

    if not transcript:
        clear_stop_marker(session_id, transcript_path)
        return 0

    # Direct edits OR Agent delegation (Agent subprocesses do the actual editing)
    edited_patterns = [
        r'"tool_name":"Edit"', r'"tool_name":"Write"', r'"tool_name":"MultiEdit"',
        r'"name":"Edit"', r'"name":"Write"', r'"name":"MultiEdit"',
    ]
    delegated_patterns = [
        r'"tool_name":"Agent"', r'"name":"Agent"',
        r'"tool_name":"Skill"', r'"name":"Skill"',
    ]
    edited = any(re.search(p, transcript) for p in edited_patterns)
    delegated = any(re.search(p, transcript) for p in delegated_patterns)
    if not edited and not delegated:
        clear_stop_marker(session_id, transcript_path)
        return 0

    if was_stop_warned(session_id, transcript_path):
        return 0

    # v4.0: Check session log existence (Incremental Recording enforcement)
    # Session log should be created at Phase 0 — if missing, block once
    if not has_session_log_for_transcript(transcript):
        # Check if this is a release session (has Skill/release invocation)
        is_release_session = bool(re.search(r'"skill"\s*:\s*"release"', transcript))
        if is_release_session:
            mark_stop_warned(session_id, transcript_path)
            return block(
                "`release` guard: 이 세션의 release 로그 증거가 없습니다. "
                "Phase 0에서 SOT/sessions/session-{date}.md를 생성하세요. "
                "(self-improvement.md v4.0 Incremental Recording)"
            )

    if has_verification_evidence(transcript):
        clear_stop_marker(session_id, transcript_path)
        return 0

    # v3.0: Check playbook backup before allowing stop
    playbook_backup_pattern = r'"playbook-backups"'
    playbook_edit = re.search(r'"(playbooks/[^"]+\.md|delegation-patterns|pipeline-patterns|quality-gates)\.md"', transcript)
    if playbook_edit and not re.search(playbook_backup_pattern, transcript):
        # Playbook or references file was edited but no backup evidence found - warn
        pass  # Non-blocking: just a signal for the orchestrator

    mark_stop_warned(session_id, transcript_path)
    return block(
        "`release` guard blocked the first stop after edits because "
        "verification evidence was not found. Run quality gates or verification, "
        "then finish again."
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
