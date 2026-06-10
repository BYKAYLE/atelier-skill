#!/usr/bin/env python3
"""stella_qwen.py — Stella ↔ Gemma 4 Bridge

스텔라의 판단/기획 작업을 로컬 Gemma 4 (MLX + BK-Med LoRA) 모델에 위임하는 브릿지.
Claude Code(릴리스)와 Gemma 4(스텔라)의 역할 분리를 실현.

Usage:
  stella_qwen.py think <prompt>       — Gemma 4에게 판단/기획 요청
  stella_qwen.py decide <context>     — 의사결정 요청 (decision-framework 포함)
  stella_qwen.py review <report>      — 릴리스 완료보고 검토 요청
  stella_qwen.py chat <message>       — 자유 대화
  stella_qwen.py health               — 모델 서버 상태 확인
  stella_qwen.py config               — 현재 설정 출력

Environment:
  STELLA_GEMMA_HOST     — MLX API host (default: http://localhost:8800)
  STELLA_GEMMA_MODEL    — Model ID (default: auto-detect)
  STELLA_GEMMA_TIMEOUT  — Request timeout in seconds (default: 120)
  STELLA_GEMMA_MAXTOK   — Max tokens (default: 4096)

Legacy STELLA_QWEN_* variables are accepted as aliases for older configs.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────

def env_with_legacy(primary: str, legacy: str, default: str) -> str:
    return os.environ.get(primary) or os.environ.get(legacy) or default


GEMMA_HOST = env_with_legacy("STELLA_GEMMA_HOST", "STELLA_QWEN_HOST", "http://localhost:8800")
GEMMA_MODEL = env_with_legacy("STELLA_GEMMA_MODEL", "STELLA_QWEN_MODEL", "")  # auto-detect if empty
GEMMA_TIMEOUT = int(env_with_legacy("STELLA_GEMMA_TIMEOUT", "STELLA_QWEN_TIMEOUT", "120"))
GEMMA_MAX_TOKENS = int(env_with_legacy("STELLA_GEMMA_MAXTOK", "STELLA_QWEN_MAXTOK", "4096"))
GEMMA_TEMP = float(env_with_legacy("STELLA_GEMMA_TEMP", "STELLA_QWEN_TEMP", "0.3"))

STELLA_ROOT = Path.home() / ".claude" / "skills" / "stella"
SOT = STELLA_ROOT / "SOT"
FRAMEWORK_MD = SOT / "stella-decision-framework.md"
USER_MD = SOT / "memory" / "USER.md"
STELLA_MD = SOT / "memory" / "STELLA.md"

# ── Stella System Prompt ──────────────────────────────────────────────────

STELLA_SYSTEM = """당신은 "스텔라" — 바이케일 대표님의 디지털 분신이자 AI 프로덕트 오너입니다.

핵심 역할:
- 대표님의 판단 패턴과 취향을 학습하여 대표님처럼 판단
- 릴리스(실행 오케스트레이터, Claude 기반)에게 WHAT/WHY를 지시
- 완료보고를 검증하고 고도화 방향을 제시

규칙:
- 반드시 존댓말(합쇼체/해요체) 사용
- 판단의 근거를 항상 명시
- 대표님의 기존 교정/선호와 일치하도록 답변
- 간결하고 실행 가능한 지시를 우선
"""


# ── API Helpers ───────────────────────────────────────────────────────────

def detect_model() -> str:
    """Auto-detect available model from MLX server."""
    if GEMMA_MODEL:
        return GEMMA_MODEL
    try:
        req = urllib.request.Request(f"{GEMMA_HOST}/v1/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = data.get("data", [])
            for m in models:
                mid = m.get("id", "")
                if "gemma" in mid.lower():
                    return mid
            if models:
                return models[0].get("id", "")
    except Exception:
        pass
    return "gemma-4-26B-A4B-it-4bit"


def call_gemma(messages: list, max_tokens: int = None, temperature: float = None) -> dict:
    """Call Gemma 4 via OpenAI-compatible API."""
    model = detect_model()
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens or GEMMA_MAX_TOKENS,
        "temperature": temperature or GEMMA_TEMP,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{GEMMA_HOST}/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=GEMMA_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        return {"error": f"Gemma server unreachable: {e}"}
    except Exception as e:
        return {"error": str(e)}


def extract_response(result: dict) -> str:
    """Extract text from API response (Gemma 4 uses 'reasoning' + 'content')."""
    if "error" in result:
        return f"[ERROR] {result['error']}"
    try:
        msg = result["choices"][0]["message"]
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning") or ""
        if content:
            return content
        if reasoning:
            return reasoning
        return f"[ERROR] Empty response: {json.dumps(msg)[:200]}"
    except (KeyError, IndexError):
        return f"[ERROR] Unexpected response format: {json.dumps(result)[:200]}"


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        return ""


# ── Modes ─────────────────────────────────────────────────────────────────

def health() -> int:
    """Check Gemma server health."""
    model = detect_model()
    result = call_gemma(
        [{"role": "user", "content": "안녕하세요. 상태 확인입니다. '정상'이라고만 답하세요."}],
        max_tokens=20,
    )
    response = extract_response(result)
    if response.startswith("[ERROR]"):
        print("STELLA-GEMMA: OFFLINE")
        print(f"  Host: {GEMMA_HOST}")
        print(f"  Model: {model}")
        print(f"  Error: {response}")
        return 1
    print("STELLA-GEMMA: ONLINE")
    print(f"  Host: {GEMMA_HOST}")
    print(f"  Model: {model}")
    print(f"  Response: {response}")
    return 0


def config() -> int:
    """Print current config."""
    model = detect_model()
    print(f"Host: {GEMMA_HOST}")
    print(f"Model: {model}")
    print(f"Timeout: {GEMMA_TIMEOUT}s")
    print(f"Max tokens: {GEMMA_MAX_TOKENS}")
    print(f"Temperature: {GEMMA_TEMP}")
    return 0


def think(prompt: str) -> int:
    """General thinking/planning request."""
    messages = [
        {"role": "system", "content": STELLA_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    result = call_gemma(messages)
    print(extract_response(result))
    return 0


def decide(context: str) -> int:
    """Decision request with framework context."""
    framework = safe_read(FRAMEWORK_MD)
    user_profile = safe_read(USER_MD)

    system = STELLA_SYSTEM + "\n\n"
    if framework:
        system += f"## 판단 프레임워크\n{framework[:2000]}\n\n"
    if user_profile:
        system += f"## 대표님 프로필\n{user_profile[:1000]}\n\n"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"아래 상황에 대해 판단해주세요:\n\n{context}"},
    ]
    result = call_gemma(messages)
    print(extract_response(result))
    return 0


def review(report: str) -> int:
    """Review release completion report."""
    framework = safe_read(FRAMEWORK_MD)

    system = STELLA_SYSTEM + """

## 리뷰 기준
릴리스 완료보고를 검토합니다. 아래 축으로 점수를 매기세요:
- 기능 완성도 (요구사항 충족)
- 품질 (코드/산출물 품질)
- 검증 (테스트/빌드 증거)
- 종합 점수 (85점 이상이면 승인, 미만이면 고도화 지시)

출력 형식:
1. 점수표
2. 부족 항목 (있으면)
3. 고도화 지시 또는 승인
"""
    if framework:
        system += f"\n## 판단 프레임워크\n{framework[:1500]}\n"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"릴리스 완료보고:\n\n{report}"},
    ]
    result = call_gemma(messages)
    print(extract_response(result))
    return 0


def chat(message: str) -> int:
    """Free-form chat with Stella persona."""
    stella_mem = safe_read(STELLA_MD)
    system = STELLA_SYSTEM
    if stella_mem:
        system += f"\n\n## 스텔라 기억\n{stella_mem[:1000]}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": message},
    ]
    result = call_gemma(messages)
    print(extract_response(result))
    return 0


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: stella_qwen.py <mode> [args]")
        print("Modes: think, decide, review, chat, health, config")
        return 1

    mode = sys.argv[1]

    if mode == "health":
        return health()
    elif mode == "config":
        return config()
    elif mode in ("think", "decide", "review", "chat"):
        prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else sys.stdin.read().strip()
        if not prompt:
            print(f"Error: {mode} requires input text")
            return 1
        dispatch = {"think": think, "decide": decide, "review": review, "chat": chat}
        return dispatch[mode](prompt)
    else:
        print(f"Unknown mode: {mode}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
