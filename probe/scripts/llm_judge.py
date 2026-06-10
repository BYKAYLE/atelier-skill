"""LLM judge via Codex CLI (ChatGPT OAuth).

Invokes `codex exec` as a subprocess with the screenshot attached via `-i`.
Constrains the output to a JSON schema, reads the last message from a temp
file, parses it, and stores the verdict on RunContext.llm_judgements.

No API key required — relies on the user being logged in with `codex login`
(ChatGPT OAuth). Sandbox is forced to read-only so the judge cannot modify
the filesystem or run shell commands.
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
def _resolve_codex() -> str | None:
    """Find the codex executable. On Windows shutil.which honours PATHEXT and
    will locate codex.cmd / codex.exe; on POSIX it finds the bare `codex`."""
    p = shutil.which("codex")
    if p:
        return p
    # Fallback for Windows environments with odd PATHEXT handling
    for suffix in (".cmd", ".exe", ".bat", ".ps1", ""):
        p = shutil.which(f"codex{suffix}")
        if p:
            return p
    return None


SEVERITY_BY_LEVEL = {"low": "minor", "medium": "major", "high": "critical"}


JUDGE_PROTOCOL = """You are an exploratory QA judge. You receive a screenshot of a web
feature under a specific state combination, plus a user-supplied question
about that screenshot.

Your job: decide whether the screenshot represents a broken, visually
incoherent, or semantically wrong rendering of the feature under the given
state. You are not grading aesthetics — you are catching:
  - layout breaks (overflow, z-index, misalignment)
  - state inconsistencies (label says A but value shows B)
  - broken text rendering (tofu, overlapping glyphs, wrong language)
  - missing content that should be there given the state
  - UI elements that contradict the combination bindings

Respond ONLY with a single JSON object matching the supplied schema. No
prose, no markdown, no explanation outside the JSON. If the screenshot
looks fine given the state, ok=true and findings=[]. Use "major" by default
when ok=false. Reserve "critical" for clearly broken renders (blank page,
all text overlapping, console-errorish UI).
"""


_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ok": {"type": "boolean"},
        "severity": {"type": "string", "enum": ["minor", "major", "critical"]},
        "summary": {"type": "string"},
        "findings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["ok", "severity", "summary", "findings"],
}


def run_llm_judge(
    assertion_cfg: dict[str, Any],
    screenshot: Path,
    bindings: dict[str, Any],
    *,
    model: str | None = None,
    timeout: float = 90.0,
) -> dict[str, Any]:
    label = assertion_cfg.get("label") or assertion_cfg.get("prompt", "")[:40] or "llm"

    if not _codex_available():
        return {
            "label": label, "skipped": True, "ok": True,
            "reason": "codex CLI not found on PATH",
        }
    if not _codex_logged_in():
        return {
            "label": label, "skipped": True, "ok": True,
            "reason": "codex not logged in — run `codex login`",
        }
    if not screenshot.exists():
        return {
            "label": label, "skipped": True, "ok": True,
            "reason": f"screenshot missing: {screenshot}",
        }

    user_prompt = assertion_cfg.get("prompt") or (
        "Does this look like a correctly rendered state of the feature?"
    )
    level = assertion_cfg.get("severity", "medium")
    default_severity = SEVERITY_BY_LEVEL.get(level, "major")
    model = model or assertion_cfg.get("model")

    state_text = "\n".join(
        f"- {k} = {v}" for k, v in sorted(bindings.items()) if not k.startswith("_")
    )
    meta_text = "\n".join(
        f"- {k} = {v}" for k, v in sorted(bindings.items()) if k.startswith("_")
    )

    full_prompt = (
        f"{JUDGE_PROTOCOL}\n\n"
        f"State bindings:\n{state_text or '(none)'}\n\n"
        f"Runtime:\n{meta_text or '(none)'}\n\n"
        f"User question:\n{user_prompt}\n"
    )

    schema_fd, schema_path = tempfile.mkstemp(suffix=".json", prefix="probe-schema-")
    out_fd, out_path = tempfile.mkstemp(suffix=".txt", prefix="probe-llm-")
    os.close(schema_fd)
    os.close(out_fd)
    try:
        Path(schema_path).write_text(json.dumps(_SCHEMA), encoding="utf-8")

        codex = _resolve_codex() or "codex"
        cmd = [
            codex, "exec",
            "--skip-git-repo-check",
            "--sandbox", "read-only",
            "-i", str(screenshot),
            "--output-schema", schema_path,
            "-o", out_path,
            "-",  # read prompt from stdin
        ]
        if model:
            cmd[2:2] = ["-m", model]

        try:
            proc = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return {
                "label": label, "ok": False, "severity": "minor",
                "summary": f"codex exec timed out after {timeout}s",
            }
        except FileNotFoundError:
            return {
                "label": label, "skipped": True, "ok": True,
                "reason": "codex not on PATH at call time",
            }

        if proc.returncode != 0:
            return {
                "label": label, "ok": False, "severity": "minor",
                "summary": "codex exec failed",
                "stderr": (proc.stderr or "")[-400:],
            }

        last = Path(out_path).read_text(encoding="utf-8", errors="replace").strip()
        parsed = _extract_json(last) or _extract_json(proc.stdout or "")
        if not parsed:
            return {
                "label": label, "ok": False, "severity": "minor",
                "summary": "codex response not parseable as JSON",
                "raw": last[:400],
            }
        return {
            "label": label,
            "ok": bool(parsed.get("ok", False)),
            "severity": parsed.get("severity", default_severity),
            "summary": parsed.get("summary", ""),
            "findings": parsed.get("findings", []),
            "backend": "codex",
            "model": model or "default",
        }
    finally:
        for p in (schema_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def _codex_available() -> bool:
    try:
        proc = subprocess.run(
            [_resolve_codex() or "codex", "--version"],
            capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace",
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _codex_logged_in() -> bool:
    try:
        proc = subprocess.run(
            [_resolve_codex() or "codex", "login", "status"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            return False
        out = (proc.stdout or "") + (proc.stderr or "")
        return "Logged in" in out
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _extract_json(text: str) -> dict[str, Any] | None:
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
