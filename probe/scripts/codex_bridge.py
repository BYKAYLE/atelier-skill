"""Shared Codex CLI bridge for probe.

Probe's isolation contract: every LLM judgement runs under the
ChatGPT-subscription Codex CLI, NOT inside the Claude session that invoked
probe. This module is the single place that knows how to reach Codex —
`llm_judge.py`, `adapters/base_adapter.py`, and `agent.py` all delegate
here so the isolation guarantee is uniform and auditable.

Why a separate module:
- de-duplicate three near-identical `_resolve_codex` / availability checks
- make "probe → Codex only" invariant grep-able (search for any other
  LLM call in probe/scripts/ and you should find nothing)
- keep one schema contract so all JSON verdicts look the same
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def resolve_codex() -> str | None:
    """Find the codex executable. Windows PATHEXT suffixes included."""
    p = shutil.which("codex")
    if p:
        return p
    for suffix in (".cmd", ".exe", ".bat", ".ps1", ""):
        p = shutil.which(f"codex{suffix}")
        if p:
            return p
    return None


def codex_available() -> bool:
    path = resolve_codex()
    if not path:
        return False
    try:
        proc = subprocess.run(
            [path, "--version"],
            capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace",
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def codex_logged_in() -> bool:
    path = resolve_codex()
    if not path:
        return False
    try:
        proc = subprocess.run(
            [path, "login", "status"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            return False
        out = (proc.stdout or "") + (proc.stderr or "")
        return "Logged in" in out
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def codex_ready() -> tuple[bool, str]:
    """Single-call readiness probe for callers that want to fail early.

    Returns (ok, reason). When ok=True the reason is empty.
    """
    if not codex_available():
        return False, "codex CLI not found on PATH"
    if not codex_logged_in():
        return False, "codex not logged in — run `codex login`"
    return True, ""


def invoke_codex_exec(
    *,
    prompt: str,
    schema: dict[str, Any],
    screenshot: Path | None = None,
    timeout: float = 120.0,
    model: str | None = None,
) -> dict[str, Any]:
    """Run `codex exec` with an output schema. Returns a normalised dict.

    Result shapes:
        success → parsed JSON verdict merged with {"backend":"codex", "model":...}
        failure → {"ok": False, "severity": "minor", "summary": "...",
                   "findings": [], optional: stderr/raw}
        unavailable → {"skipped": True, "ok": True, "reason": "..."}

    Callers (llm_judge, adapters) add their own `label` field; this
    module stays label-agnostic.
    """
    ready, reason = codex_ready()
    if not ready:
        return {"skipped": True, "ok": True, "reason": reason}

    schema_fd, schema_path = tempfile.mkstemp(suffix=".json", prefix="probe-codex-schema-")
    out_fd, out_path = tempfile.mkstemp(suffix=".txt", prefix="probe-codex-out-")
    os.close(schema_fd)
    os.close(out_fd)
    try:
        Path(schema_path).write_text(json.dumps(schema), encoding="utf-8")

        codex = resolve_codex() or "codex"
        cmd = [
            codex, "exec",
            "--skip-git-repo-check",
            "--sandbox", "read-only",
            "--output-schema", schema_path,
            "-o", out_path,
        ]
        if screenshot and screenshot.exists():
            cmd.extend(["-i", str(screenshot)])
        if model:
            cmd.extend(["-m", model])
        cmd.append("-")  # prompt on stdin

        try:
            proc = subprocess.run(
                cmd, input=prompt, capture_output=True, text=True,
                timeout=timeout, encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False, "severity": "minor",
                "summary": f"codex exec timed out after {timeout}s",
                "findings": [],
            }
        except FileNotFoundError:
            return {
                "skipped": True, "ok": True,
                "reason": "codex not on PATH at call time",
            }

        if proc.returncode != 0:
            return {
                "ok": False, "severity": "minor",
                "summary": "codex exec failed",
                "stderr": (proc.stderr or "")[-400:],
                "findings": [],
            }

        raw = Path(out_path).read_text(encoding="utf-8", errors="replace").strip()
        parsed = extract_json(raw) or extract_json(proc.stdout or "")
        if not parsed:
            return {
                "ok": False, "severity": "minor",
                "summary": "codex response not parseable as JSON",
                "raw": raw[:400],
                "findings": [],
            }
        parsed.setdefault("findings", [])
        parsed["backend"] = "codex"
        parsed["model"] = model or "default"
        return parsed
    finally:
        for p in (schema_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    s = text.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    start = s.find("{")
    end = s.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        return json.loads(s[start : end + 1])
    except json.JSONDecodeError:
        return None
