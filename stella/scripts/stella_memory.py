#!/usr/bin/env python3
"""stella_memory.py — Stella Adaptive Memory System v2

Rebuilt to fix 7 critical defects from v1 audit:
  1. SOT write detection false positives (independent check)
  2. JSON Unicode escape corruption (regex on raw JSON)
  3. Duplicate detection too aggressive (50-char prefix)
  4. Harvest→compress order (noise evicts core memories)
  5. Over-matching Korean patterns (everyday words trigger)
  6. Double stop-hook blocking (stella + release)
  7. /tmp state without session isolation

Modes:
  phase0      — Session start: load SOT into context
  guard       — PreToolUse hook: blocks until phase0 done
  nudge       — PostToolUse hook: reminds L0 saves
  search      — Cross-session keyword search (L1)
  stop        — Session end: gates + daily log + compress (L4)
  selfassess  — Self-assessment report (L5)

Hook wiring (SKILL.md):
  PreToolUse  → guard   (Bash only)
  PostToolUse → nudge   (Bash only)
  Stop        → stop
"""

import json
import hashlib
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

# ── Paths ────────────────────────────────────────────────────────────────

STELLA_ROOT = Path.home() / ".claude" / "skills" / "stella"
SOT = STELLA_ROOT / "SOT"
MEMORY_DIR = SOT / "memory"
DAILY_DIR = MEMORY_DIR / "daily"
PRESERVATION_INDEX = MEMORY_DIR / "preservation-index.md"
PLAYBOOKS_DIR = SOT / "playbooks"

STELLA_MD = MEMORY_DIR / "STELLA.md"
USER_MD = MEMORY_DIR / "USER.md"
CORRECTIONS_MD = SOT / "corrections.md"
FRAMEWORK_MD = SOT / "stella-decision-framework.md"
PLAYBOOK_INDEX = PLAYBOOKS_DIR / "_index.md"
PERFORMANCE_MD = SOT / "performance.md"

STELLA_LIMIT = 2200
USER_LIMIT = 1375
SECTION_SEP = "\n§\n"

# Fix #7: Session-isolated state dir using PID + session_id
# Falls back to PID-based isolation if no session_id available
_SESSION_ID = os.environ.get("CLAUDE_SESSION_ID", str(os.getpid()))
STATE_DIR = Path("/tmp/stella_memory_state") / _SESSION_ID
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Also keep a shared dir for cross-session counters
SHARED_STATE = Path("/tmp/stella_memory_state") / "_shared"
SHARED_STATE.mkdir(parents=True, exist_ok=True)

# ── Utilities ────────────────────────────────────────────────────────────

def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        return ""

def safe_write(path: Path, content: str) -> bool:
    """Atomic write: tmpfile → rename. Returns True on success."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmpfile = path.parent / f".{path.name}.tmp.{os.getpid()}"
        tmpfile.write_text(content, encoding="utf-8")
        tmpfile.replace(path)  # atomic on POSIX
        return True
    except Exception as e:
        sys.stderr.write(f"stella_memory: write failed {path}: {e}\n")
        try:
            tmpfile.unlink(missing_ok=True)
        except Exception:
            pass
        return False

def load_stdin() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}

def append_unique_line(filepath: Path, line: str) -> None:
    current = safe_read(filepath)
    lines = current.splitlines() if current else []
    if line in lines:
        return
    next_content = (current + "\n" if current else "") + line
    safe_write(filepath, next_content)

def scoped_marker(name: str, transcript_path: str = "") -> Path:
    """Session-scoped marker; transcript path is stable across repeated stop hooks."""
    raw = os.environ.get("CLAUDE_SESSION_ID") or transcript_path or _SESSION_ID
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return SHARED_STATE / f"{name}_{digest}"

def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def marker_time_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def char_count(text: str) -> int:
    return len(text)


def topic_words(text: str) -> set:
    """Extract topic words — Korean 2+ chars, English proper/acronym, paths."""
    words = set()
    for w in text.split():
        w_clean = w.strip(",.;:()[]")
        if re.match(r'[\uac00-\ud7af]{2,}', w_clean):  # Korean 2+ chars
            words.add(w_clean)
        elif re.match(r'[A-Z][A-Za-z]+', w_clean):  # Proper/acronym
            words.add(w_clean)
        elif '/' in w_clean or '.' in w_clean:  # Paths
            words.add(w_clean)
        elif re.match(r'[a-z]{3,}', w_clean):  # lowercase English 3+ chars
            words.add(w_clean.lower())
    return words


def score_section(query: str, section: str) -> float:
    """§ 섹션과 쿼리의 관련성 점수 (0.0~1.0), Jaccard similarity."""
    query_words = set(topic_words(query))
    section_words = set(topic_words(section))
    if not query_words or not section_words:
        return 0.3  # 기본값
    intersection = query_words & section_words
    union = query_words | section_words
    return len(intersection) / len(union) if union else 0.3


# Fix #2: Proper JSON transcript parsing instead of regex
def extract_user_messages(transcript: str) -> List[str]:
    """Extract user messages from Claude Code transcript JSON properly."""
    messages = []
    try:
        data = json.loads(transcript)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("role") == "user":
                    content = item.get("content", "")
                    if isinstance(content, str):
                        messages.append(content)
                    elif isinstance(content, list):
                        # Content can be array of {type, text} blocks
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                messages.append(block.get("text", ""))
    except (json.JSONDecodeError, TypeError):
        # Fallback: try line-by-line JSON objects (JSONL format)
        for line in transcript.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if isinstance(item, dict) and item.get("role") == "user":
                    content = item.get("content", "")
                    if isinstance(content, str):
                        messages.append(content)
            except (json.JSONDecodeError, TypeError):
                continue
    return messages


# Fix #1: Check SOT writes by finding Write/Edit tool calls WITH SOT path in same call
# Fix #10 (260610, Opus 4.8 검토): 기억 표면을 stella/SOT만이 아니라 release/SOT,
# auto-memory, bk-wiki 이벤트 로그까지 인정. Bash 경유 저장(heredoc/append)도 인정.
# 근거: release 세션이 release SOT에 기록해도 stella 게이트가 오탐 차단하던 마찰 해소.
MEMORY_SURFACE_PATTERN = (
    r"(?:stella/SOT/|release/SOT/|bk-wiki/raw/|session-events\.jsonl"
    r"|projects/[^\"'\\s]{0,120}/memory/|MEMORY\.md)"
)


def check_sot_writes_in_transcript(transcript: str) -> bool:
    """Check if any memory-surface files were actually written (not just read)."""
    try:
        data = json.loads(transcript)
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                tool = item.get("tool_name") or item.get("name") or ""
                if tool not in ("Write", "Edit", "MultiEdit"):
                    continue
                tool_input = item.get("tool_input", {})
                file_path = str(tool_input.get("file_path", "") or tool_input.get("path", ""))
                if re.search(MEMORY_SURFACE_PATTERN, file_path):
                    return True
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: regex but require tool+path in close proximity (within 500 chars)
    write_sot_pattern = (
        r'"(?:tool_name|name)"\s*:\s*"(?:Write|Edit|MultiEdit)"[^}]{0,500}'
        + MEMORY_SURFACE_PATTERN
    )
    if re.search(write_sot_pattern, transcript, re.DOTALL):
        return True

    # Bash 경유 저장: echo >> / cat > / tee 가 기억 표면을 향하면 저장으로 인정
    bash_write_pattern = (
        r"(?:>>|cat\s*>|tee\s)(?:[^\"\n]|\\\"){0,250}?" + MEMORY_SURFACE_PATTERN
    )
    return bool(re.search(bash_write_pattern, transcript))


def transcript_did_work(transcript: str) -> bool:
    """세션이 실제 작업(편집/위임)을 했는지. 순수 질의응답이면 False."""
    return bool(re.search(
        r'"(?:tool_name|name)"\s*:\s*"(?:Write|Edit|MultiEdit|NotebookEdit|Agent|Skill)"',
        transcript,
    ))


# Fix #3: Smart duplicate detection — compare semantic key, not prefix
def append_to_memory(filepath: Path, entry: str, limit: int) -> None:
    """Append a § delimited entry with smart dedup and limit management."""
    current = safe_read(filepath)
    new_entry = entry.strip()
    
    if not new_entry:
        return

    # Extract semantic key: first meaningful phrase (ignore timestamps/prefixes)
    def semantic_key(text: str) -> str:
        # Strip [timestamp], §, whitespace
        cleaned = re.sub(r'^\[.*?\]\s*', '', text.strip())
        cleaned = re.sub(r'^§\s*', '', cleaned)
        cleaned = re.sub(r'\(\d{6}\)\s*$', '', cleaned)  # Remove (YYMMDD)
        return cleaned.strip()[:80]

    new_key = semantic_key(new_entry)
    if not new_key:
        return

    # Check existing sections for semantic overlap
    sections = current.split("§") if current else []
    for i, section in enumerate(sections):
        existing_key = semantic_key(section)
        if not existing_key:
            continue
        new_topics = topic_words(new_key)
        existing_topics = topic_words(existing_key)
        common = new_topics & existing_topics

        if existing_key == new_key:
            return

    # No overlap — append
    if current:
        combined = current + SECTION_SEP + new_entry
    else:
        combined = new_entry

    if char_count(combined) > limit:
        append_unique_line(
            PRESERVATION_INDEX,
            f"- [{now_str()}] soft-limit exceeded for {filepath.name}: {char_count(combined)} chars (limit {limit}); no memory data removed.",
        )

    safe_write(filepath, combined)


# ── Phase 0 ──────────────────────────────────────────────────────────────

def get_file_age_days(filepath: Path) -> Optional[int]:
    try:
        if not filepath.exists():
            return None
        mtime = filepath.stat().st_mtime
        return int((datetime.now().timestamp() - mtime) / 86400)
    except Exception:
        return None

def get_session_count() -> int:
    perf = safe_read(PERFORMANCE_MD)
    return len(re.findall(r'^\|', perf, re.MULTILINE)) - 1  # Subtract header row

def get_last_evolution_session() -> int:
    evo = safe_read(SOT / "evolution-log.md")
    patterns = [
        r'세션\s*카운트\s*[:#]\s*(\d+)',
        r'[Ss]ession\s*[:#]\s*(\d+)',
        r'세션\s*#\s*(\d+)',
    ]
    all_matches = []
    for p in patterns:
        all_matches.extend(re.findall(p, evo))
    return int(max(all_matches, key=int)) if all_matches else 0


# Fix: Use SHARED_STATE for markers that must be visible across processes
# phase0 and guard/nudge run as separate processes with different PIDs
PHASE0_MARKER = SHARED_STATE / "stella_phase0_done"
TOOL_COUNTER = SHARED_STATE / "stella_tool_count"

def mark_phase0_done() -> None:
    # Fix #7: Store start timestamp instead of date for midnight safety
    payload = {
        "timestamp": marker_time_str(),
        "display_time": now_str(),
        "session_id": os.environ.get("CLAUDE_SESSION_ID", ""),
    }
    safe_write(PHASE0_MARKER, json.dumps(payload, ensure_ascii=False))
    safe_write(TOOL_COUNTER, "0")


def is_phase0_done_for_current_session() -> bool:
    """최근 4시간 내에 phase0가 실행되었는지 확인.
    SHARED_STATE에 있으므로 프로세스 간 공유 가능.
    4시간 제한으로 이전 세션의 마커가 재사용되는 것을 방지."""
    content = safe_read(PHASE0_MARKER)
    if not content:
        return False
    try:
        marker_payload = json.loads(content)
        marker_session = marker_payload.get("session_id", "")
        current_session = os.environ.get("CLAUDE_SESSION_ID", "")
        if current_session and marker_session and marker_session != current_session:
            return False
        timestamp = marker_payload.get("timestamp", "")
    except (json.JSONDecodeError, TypeError, AttributeError):
        timestamp = content.strip()

    for fmt in ("%Y%m%d_%H%M%S", "%Y-%m-%d %H:%M"):
        try:
            marker_time = datetime.strptime(timestamp, fmt)
            age_hours = (datetime.now() - marker_time).total_seconds() / 3600
            return age_hours < 4  # 4시간 내 마커만 유효
        except (ValueError, TypeError):
            continue
    return False


def _split_stella_sections(stella_text: str) -> List[str]:
    """STELLA.md를 § 구분자로 섹션 분리. 줄 시작 '§ ' 또는 '\n§\n' 모두 지원."""
    # 줄 시작 § 패턴 (실제 STELLA.md 포맷: "§ 내용...")
    lines = stella_text.strip().split("\n")
    sections = []
    current = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("§") and current:
            sections.append("\n".join(current).strip())
            current = [stripped]
        elif stripped.startswith("§"):
            current = [stripped]
        elif stripped:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())
    # Fallback: § 인라인 구분자
    if not sections and "§" in stella_text:
        sections = [s.strip() for s in stella_text.split("§") if s.strip()]
    if not sections and stella_text.strip():
        sections = [stella_text.strip()]
    return sections


def _smart_load_stella(stella_text: str, query: str, top_n: int = 5) -> str:
    """쿼리 관련성 상위 top_n개 § 섹션만 반환."""
    sections = _split_stella_sections(stella_text)
    if not sections:
        return ""
    if len(sections) <= top_n:
        return stella_text  # 섹션 수가 top_n 이하면 전체 반환

    scored = [(score_section(query, sec), i, sec) for i, sec in enumerate(sections)]
    scored.sort(key=lambda x: (-x[0], x[1]))  # 점수 내림차순, 동점이면 원래 순서
    top = scored[:top_n]
    top.sort(key=lambda x: x[1])  # 원래 순서로 재정렬

    omitted = len(sections) - top_n
    header = f"[Relevance-Scored: {len(sections)}개 중 상위 {top_n}개 로드, {omitted}개 생략]"
    body = "\n§\n".join(item[2] for item in top)
    return f"{header}\n\n{body}"


def phase0() -> int:
    # 쿼리 인자 확인 (sys.argv[2]가 있으면 스마트 로드)
    query = sys.argv[2] if len(sys.argv) > 2 else ""

    sections = []

    stella = safe_read(STELLA_MD)
    if stella:
        if query:
            loaded = _smart_load_stella(stella, query)
            sections.append(f"## STELLA MEMORY (환경·도구·인사이트)\n{loaded}")
        else:
            sections.append(f"## STELLA MEMORY (환경·도구·인사이트)\n{stella}")

    # USER.md는 항상 전체 출력 (pinned)
    user = safe_read(USER_MD)
    if user:
        sections.append(f"## USER PROFILE (대표님 성향·기대) [PINNED]\n{user}")

    framework = safe_read(FRAMEWORK_MD)
    if framework:
        sections.append(f"## DECISION FRAMEWORK (판단 기준)\n{framework}")

    corrections = safe_read(CORRECTIONS_MD)
    if corrections:
        lines = corrections.strip().split("\n")
        recent = "\n".join(lines[-15:]) if len(lines) > 15 else corrections
        sections.append(f"## RECENT CORRECTIONS (최근 교정)\n{recent}")

    index = safe_read(PLAYBOOK_INDEX)
    if index:
        sections.append(f"## PLAYBOOK INDEX\n{index}")

    if DAILY_DIR.exists():
        for f in sorted(DAILY_DIR.glob("*.md"), reverse=True)[:3]:
            content = safe_read(f)
            if content:
                sections.append(f"## DAILY LOG: {f.stem}\n{content}")

    # Health Dashboard
    session_count = get_session_count()
    stella_age = get_file_age_days(STELLA_MD)
    user_age = get_file_age_days(USER_MD)
    last_evo = get_last_evolution_session()
    sessions_since_evo = max(0, session_count - last_evo)

    try:
        cumulative_tools = int(safe_read(SHARED_STATE / "stella_cumulative_tools") or "0")
    except ValueError:
        cumulative_tools = 0

    health = ["## ★ MEMORY HEALTH DASHBOARD"]
    health.append(f"  STELLA.md 마지막 수정: {stella_age}일 전" if stella_age is not None else "  STELLA.md: 없음")
    health.append(f"  USER.md 마지막 수정: {user_age}일 전" if user_age is not None else "  USER.md: 없음")
    health.append(f"  세션 카운트: {session_count} | 누적 도구 호출: {cumulative_tools}회")
    health.append(f"  L5 마지막 실행: 세션 #{last_evo} ({sessions_since_evo}세션 전)")
    health.append(f"  L5 트리거: {sessions_since_evo}세션/5 + {cumulative_tools}도구/50")

    l5_overdue = sessions_since_evo >= 5 and cumulative_tools >= 50
    if l5_overdue:
        health.append("  ⚠ L5 Self-Evolution 트리거!")
    if stella_age and stella_age > 7:
        health.append(f"  ⚠ STELLA.md {stella_age}일간 미갱신")
    if user_age and user_age > 7:
        health.append(f"  ⚠ USER.md {user_age}일간 미갱신")

    sections.append("\n".join(health))

    if sections:
        print("=" * 60)
        print(f"STELLA SOT CONTEXT — Phase 0 Load ({now_str()})")
        print("=" * 60)
        print("\n\n".join(sections))
        print("=" * 60)
        print()
        print("★ L0 ACTIVE: 매 턴 후 기억할 것이 있으면 SOT 파일에 즉시 저장하라.")
        print("  교정→USER.md, 환경사실→STELLA.md, 절차→playbooks/.")
        print("  한 줄 요약 + § 구분 + (YYMMDD). 세션 종료 시 SOT 저장 0건이면 1회 차단.")
        if l5_overdue:
            print(f"  ⚠ L5 밀림 — 세션 종료 전 반드시 실행 필요!")
    else:
        print("STELLA SOT: Empty — first session.")
        print("★ L0 ACTIVE: 이 세션부터 학습 시작.")

    mark_phase0_done()
    safe_write(SHARED_STATE / "stella_session_count", str(session_count + 1))

    return 0


# ── Guard ─────────────────────────────────────────────────────────────────

GUARD_BLOCK_PREFIX = "stella_guard_blocks"


def guard() -> int:
    data = load_stdin()

    # Fix #7+#8: Check marker for CURRENT session (cross-session isolation)
    if is_phase0_done_for_current_session():
        return 0

    tool_input = data.get("tool_input", {})
    command = str(tool_input.get("command", ""))
    if "stella_memory" in command and "phase0" in command:
        return 0

    # Fix #10 (260610): dead-loop 방지 fail-open.
    # phase0 스크립트 자체가 고장나면 모든 Bash가 영구 차단되던 구조
    # (260505 권한 dead-loop 사고와 동일 클래스). 같은 세션에서 2회 차단 후엔
    # 경고만 남기고 통과시킨다 — 거부 2회 초과 재시도 금지 룰과 정합.
    blocks_marker = scoped_marker(GUARD_BLOCK_PREFIX, str(data.get("transcript_path", "")))
    try:
        block_count = int(safe_read(blocks_marker) or "0")
    except ValueError:
        block_count = 0

    if block_count >= 2:
        sys.stderr.write(
            "stella guard: Phase 0 미실행 상태로 2회 차단됨 — fail-open 통과 "
            "(dead-loop 방지). 가능하면 phase0를 실행하세요.\n"
        )
        return 0

    safe_write(blocks_marker, str(block_count + 1))
    sys.stderr.write(
        "stella guard: Phase 0 미실행. "
        "`python3 ~/.claude/skills/stella/scripts/stella_memory.py phase0` 실행 필요.\n"
    )
    return 2


# ── Nudge ─────────────────────────────────────────────────────────────────

NUDGE_INTERVAL = 10

def nudge() -> int:
    data = load_stdin()

    count = 0
    try:
        count = int(TOOL_COUNTER.read_text().strip())
    except Exception:
        pass

    # Check SOT write in this specific tool call (not whole transcript)
    tool_name = str(data.get("tool_name", ""))
    tool_input = data.get("tool_input", {})

    is_sot_write = False
    if tool_name in ("Write", "Edit", "MultiEdit"):
        fp = str(tool_input.get("file_path", "") or tool_input.get("path", ""))
        if "stella/SOT/" in fp:
            is_sot_write = True

    if is_sot_write:
        safe_write(TOOL_COUNTER, "0")
        return 0

    count += 1
    safe_write(TOOL_COUNTER, str(count))

    # Cumulative (shared across sessions)
    try:
        cum = int(safe_read(SHARED_STATE / "stella_cumulative_tools") or "0")
    except ValueError:
        cum = 0
    safe_write(SHARED_STATE / "stella_cumulative_tools", str(cum + 1))

    if count > 0 and count % NUDGE_INTERVAL == 0:
        sys.stderr.write(
            f"stella L0 nudge: {count}회 도구 호출 동안 SOT 저장 없음. "
            "기억할 것이 있으면 저장하세요.\n"
        )

    return 0


# ── Stop (L4) ─────────────────────────────────────────────────────────────

STOP_WARNED_PREFIX = "stella_stop_warned"
L5_FORCED_PREFIX = "stella_l5_forced"

def stop() -> int:
    data = load_stdin()
    transcript_path = data.get("transcript_path", "")
    stop_warned = scoped_marker(STOP_WARNED_PREFIX, transcript_path)
    l5_forced = scoped_marker(L5_FORCED_PREFIX, transcript_path)

    transcript = ""
    if transcript_path:
        try:
            transcript = Path(transcript_path).read_text(encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            sys.stderr.write(f"stella_memory: transcript not found: {transcript_path}\n")
        except Exception as e:
            sys.stderr.write(f"stella_memory: transcript read error: {e}\n")

    # ── Gate 1: L0 — SOT 저장 0건이면 1회 차단 ──────────────────────────
    # Fix #6: Only run stella gate, don't conflict with release guard
    # Release guard checks for verification evidence (test/build)
    # Stella gate checks for memory saves — different concerns, both valid
    # Fix #10 (260610): 순수 질의응답(편집/위임 0건) 세션은 게이트 면제.
    # 기억할 작업 자체가 없는 세션을 차단해 빈 턴만 낭비하던 마찰 제거.
    if transcript and transcript_did_work(transcript):
        has_sot_writes = check_sot_writes_in_transcript(transcript)

        if not has_sot_writes and not stop_warned.exists():
            safe_write(stop_warned, now_str())
            sys.stderr.write(
                "stella L0 gate: SOT 저장 기록 없음. "
                "기억할 것이 없으면 다시 종료하세요.\n"
            )
            return 2

    # ── Gate 2: L5 ───────────────────────────────────────────────────────
    try:
        current_session = int(safe_read(SHARED_STATE / "stella_session_count") or "0")
    except ValueError:
        current_session = 0

    try:
        cumulative_tools = int(safe_read(SHARED_STATE / "stella_cumulative_tools") or "0")
    except ValueError:
        cumulative_tools = 0

    last_evo = get_last_evolution_session()
    sessions_since_evo = current_session - last_evo
    l5_due = sessions_since_evo >= 5 and cumulative_tools >= 50
    has_evo_record = False

    if l5_due:
        evo_content = safe_read(SOT / "evolution-log.md")

        session_pats = [
            f"세션\\s*카운트\\s*[:#]\\s*{current_session}",
            f"[Ss]ession\\s*[:#]\\s*{current_session}",
            f"세션\\s*#\\s*{current_session}",
        ]
        has_evo_record = any(re.search(p, evo_content) for p in session_pats)

        defer_pats = [f"(?:DEFER|defer|이월).*{current_session}"]
        has_defer = any(re.search(p, evo_content, re.IGNORECASE) for p in defer_pats)

        if has_defer:
            sys.stderr.write(f"stella L5: DEFER 확인 — 다음 세션에서 실행 필요.\n")
        elif has_evo_record:
            pass
        else:
            if not l5_forced.exists():
                safe_write(l5_forced, now_str())
                sys.stderr.write(
                    f"stella L5 gate: {sessions_since_evo}세션, {cumulative_tools}도구 — "
                    f"selfassess 실행 후 evolution-log.md에 세션 #{current_session} 기록 필요. "
                    f"긴급 시 DEFER — 세션 #{current_session} 기록.\n"
                )
                return 2
            # 두 번째 이후: 경고만 출력하고 통과 (무한 블로킹 방지)
            sys.stderr.write(f"stella L5: 세션 #{current_session} 기록 미완 — 통과.\n")

    # ── Gates passed ──────────────────────────────────────────────────────
    # stop_warned / l5_forced 마커는 세션별로 유지:
    # 같은 transcript의 반복 stop 호출만 통과시키고, 다음 세션에는 새 marker를 사용한다.

    if l5_due and has_evo_record:
        safe_write(SHARED_STATE / "stella_cumulative_tools", "0")

    # ── Preservation check ────────────────────────────────────────────────
    # Memory limits are now soft. Never remove or rewrite older entries to make room.
    for filepath, limit, label in [
        (STELLA_MD, STELLA_LIMIT, "STELLA"),
        (USER_MD, USER_LIMIT, "USER"),
    ]:
        content = safe_read(filepath)
        if char_count(content) > int(limit * 0.9):
            append_unique_line(
                PRESERVATION_INDEX,
                f"- [{now_str()}] {label} memory above soft limit: {char_count(content)} chars (limit {limit}); no sections removed.",
            )

    # Step 2: NO automatic harvest — L0 is agent-driven, not regex
    # The old harvest used regex patterns (defect 5) that produced noise
    # Agent's explicit Write calls are the only memory source now

    # ── Daily Log ────────────────────────────────────────────────────────
    # Fix #9 (260411): 사용자 턴 0인 빈 세션은 daily/performance에 기록하지 않는다.
    # 자동 hook trigger (cron, wiki-ingest, claude-sync)가 stop hook을 분단위로 호출하면서
    # 가짜 세션이 폭주해 corrections/performance가 신뢰할 수 없는 상태가 되는 것을 차단.
    user_msgs_for_session = extract_user_messages(transcript) if transcript else []
    is_empty_session = len(user_msgs_for_session) == 0

    if is_empty_session:
        # 빈 세션은 daily/performance/세션카운트 모두 건드리지 않고 조용히 종료
        sys.stderr.write("stella_memory L4: empty session (user_turns=0) — skip recording\n")
        return 0

    daily_file = DAILY_DIR / f"{today_str()}.md"
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

    summary = [f"# Stella Daily — {today_str()}\n"]
    if transcript:
        tool_count = transcript.count('"tool_name"')
        summary.append(f"- 도구 호출: {tool_count}회, 사용자 턴: {len(user_msgs_for_session)}회")

    existing = safe_read(daily_file)
    if existing:
        new_content = existing + f"\n\n## 세션 {now_str()}\n" + "\n".join(summary[1:])
    else:
        new_content = "\n".join(summary)
    safe_write(daily_file, new_content)

    # ── Old daily preservation index (30+ days) ──────────────────────────
    if DAILY_DIR.exists():
        cutoff = datetime.now() - timedelta(days=30)
        for f in DAILY_DIR.glob("*.md"):
            try:
                fdate = datetime.strptime(f.stem, "%Y-%m-%d")
                if fdate < cutoff:
                    content = safe_read(f)
                    if content and len(content) > 50:
                        lines = [l for l in content.split("\n") if l.strip() and not l.startswith("#")]
                        if lines:
                            append_unique_line(
                                PRESERVATION_INDEX,
                                f"- [{now_str()}] retained old daily log {f.name}: {lines[0][:100]}",
                            )
            except ValueError:
                continue

    # ── Performance tracking ─────────────────────────────────────────────
    perf = safe_read(PERFORMANCE_MD)
    tool_count = transcript.count('"tool_name"') if transcript else 0
    user_turns = len(extract_user_messages(transcript)) if transcript else 0
    perf_row = f"\n| {now_str()} | {tool_count} | {user_turns} | {today_str()}.md | |"
    safe_write(PERFORMANCE_MD, perf + perf_row)

    updated = safe_read(PERFORMANCE_MD)
    session_total = len(re.findall(r'^\| 20', updated, re.MULTILINE))
    updated = re.sub(r'총 세션: \d+', f'총 세션: {session_total}', updated)
    safe_write(PERFORMANCE_MD, updated)

    sys.stderr.write("stella_memory L4: session wrap-up complete\n")
    return 0


# ── Search (L1) ──────────────────────────────────────────────────────────

def search(query: str) -> int:
    if not query:
        print("Usage: stella_memory.py search <keyword>")
        return 1

    results = []
    keywords = query.lower().split()

    for dir_path, label_prefix in [
        (DAILY_DIR, "daily"),
        (PLAYBOOKS_DIR, "playbooks"),
    ]:
        if dir_path and dir_path.exists():
            for f in sorted(dir_path.glob("*.md"), reverse=True):
                if f.name == "_index.md":
                    continue
                content = safe_read(f)
                for i, line in enumerate(content.split("\n")):
                    if any(kw in line.lower() for kw in keywords):
                        results.append(f"[{label_prefix}/{f.stem}:{i+1}] {line.strip()}")

    for md_file, label in [(CORRECTIONS_MD, "corrections"), (STELLA_MD, "STELLA"), (USER_MD, "USER")]:
        content = safe_read(md_file)
        if content:
            for section in content.split("§"):
                if any(kw in section.lower() for kw in keywords):
                    results.append(f"[{label}] {section.strip()[:200]}")

    if results:
        print(f"Found {len(results)} matches for '{query}':\n")
        for r in results[:30]:
            print(f"  {r}")
    else:
        print(f"No matches for '{query}'.")

    return 0


# ── Selfassess (L5) ─────────────────────────────────────────────────────

def selfassess() -> int:
    print("=" * 60)
    print("STELLA L5 — Self-Assessment Report")
    print("=" * 60)

    corrections = safe_read(CORRECTIONS_MD)
    if corrections:
        # Parse table rows (| date | context | ... |) — skip header/separator
        data_lines = [l.strip() for l in corrections.split("\n")
                      if l.strip().startswith("| 2") and not l.strip().startswith("| 날짜")]
        print(f"\n## 교정 분석 ({len(data_lines)}건)")

        # Step 1: 반복 키워드 (단순)
        words = {}
        for line in data_lines:
            for word in re.findall(r'[\uac00-\ud7af]{2,}', line):
                words[word] = words.get(word, 0) + 1
        frequent = sorted(words.items(), key=lambda x: -x[1])[:10]
        if frequent:
            print("  반복 키워드:")
            for word, count in frequent:
                if count >= 2:
                    print(f"    {word}: {count}회")

        # Step 2: 승격 후보 식별 (Fix #10, 260411)
        # corrections.md 헤더의 "같은 교정 2회 시 USER.md 승격" 정책 자동화.
        # 같은 "맥락(2번째 컬럼)" 또는 같은 "학습(5번째 컬럼)" 핵심 키워드가 2회+ 반복되면 후보.
        promotion_candidates: Dict[str, List[str]] = {}
        for line in data_lines:
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) < 5:
                continue
            # cols[0]=날짜, cols[1]=맥락, cols[2]=원래판단, cols[3]=교정, cols[4]=학습, cols[5]=승격
            context_key = cols[1][:30]  # 맥락 첫 30자를 키로
            learn_key_words = set(re.findall(r'[\uac00-\ud7af]{3,}', cols[4]))
            # 이미 승격된 항목은 후보에서 제외
            already_promoted = len(cols) > 5 and ("승격" in cols[5] or "USER.md" in cols[5])

            if not already_promoted:
                # 학습 키워드의 핵심 단어(3+자) 시그니처
                signature = " ".join(sorted(learn_key_words))[:80] if learn_key_words else context_key
                if signature:
                    promotion_candidates.setdefault(signature, []).append(cols[0])

        repeated = {k: v for k, v in promotion_candidates.items() if len(v) >= 2}
        if repeated:
            print(f"\n  ⚠ 승격 후보 {len(repeated)}건 (2회+ 반복, 미승격):")
            for sig, dates in list(repeated.items())[:5]:
                print(f"    [{', '.join(dates)}] {sig[:70]}")
            print("  → corrections.md 검토 + USER.md 승격 권장")
        else:
            print("\n  승격 후보: 없음 (모든 2회+ 패턴이 이미 승격됨)")
    else:
        print("\n## 교정 분석: 기록 없음")

    stella_size = char_count(safe_read(STELLA_MD))
    user_size = char_count(safe_read(USER_MD))
    print(f"\n## 메모리 상태")
    print(f"  STELLA.md: {stella_size}/{STELLA_LIMIT} ({stella_size*100//max(STELLA_LIMIT,1)}%)")
    print(f"  USER.md: {user_size}/{USER_LIMIT} ({user_size*100//max(USER_LIMIT,1)}%)")

    daily_count = len(list(DAILY_DIR.glob("*.md"))) if DAILY_DIR.exists() else 0
    pb_count = max(0, len(list(PLAYBOOKS_DIR.glob("*.md"))) - 1) if PLAYBOOKS_DIR.exists() else 0
    print(f"  Daily logs: {daily_count}개 | Playbooks: {pb_count}개")

    session_count = get_session_count()
    print(f"  총 세션: {session_count}회")

    print("\n" + "=" * 60)
    return 0


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: stella_memory.py <mode> [args]")
        print("Modes: phase0, guard, nudge, search <query>, stop, selfassess")
        return 1

    mode = sys.argv[1]
    dispatch = {
        "phase0": phase0,
        "guard": guard,
        "nudge": nudge,
        "search": lambda: search(" ".join(sys.argv[2:])),
        "stop": stop,
        "selfassess": selfassess,
    }
    fn = dispatch.get(mode)
    if fn:
        return fn()
    sys.stderr.write(f"Unknown mode: {mode}\n")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
