"""Shared helpers for skill adapters.

Adapters (audit, harden, ...) share one contract: send a custom system
prompt + probe artefacts to Codex, receive a JSON verdict. All Codex
plumbing lives in codex_bridge so this module stays focused on adapter
semantics (default schema, label handling, SKILL.md loading).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from codex_bridge import (  # noqa: F401 — re-exported for adapter modules
    codex_available,
    codex_logged_in,
    codex_ready,
    invoke_codex_exec,
    resolve_codex,
)


DEFAULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ok": {"type": "boolean"},
        "severity": {"type": "string", "enum": ["minor", "major", "critical"]},
        "summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "category": {"type": "string"},
                    "severity": {"type": "string", "enum": ["minor", "major", "critical"]},
                    "message": {"type": "string"},
                    "selector": {"type": "string"},
                },
                "required": ["category", "severity", "message"],
            },
        },
    },
    "required": ["ok", "severity", "summary", "findings"],
}


def invoke_skill(
    *,
    label: str,
    prompt: str,
    schema: dict[str, Any] | None = None,
    screenshot: Path | None = None,
    timeout: float = 120.0,
    model: str | None = None,
) -> dict[str, Any]:
    """Run a skill's prompt under Codex CLI and return a labelled verdict.

    Shape matches llm_judge output so checks.py can treat every adapter
    result uniformly (same fields: label, ok, severity, summary, findings;
    or {label, skipped, ok, reason} when Codex is unavailable).
    """
    result = invoke_codex_exec(
        prompt=prompt,
        schema=schema or DEFAULT_SCHEMA,
        screenshot=screenshot,
        timeout=timeout,
        model=model,
    )
    result.setdefault("label", label)
    if not result.get("skipped"):
        result.setdefault("severity", "major")
    return result


def load_skill_prompt(skill_name: str) -> str | None:
    """Read ~/.claude/skills/<skill>/SKILL.md and return its body."""
    path = Path.home() / ".claude" / "skills" / skill_name / "SKILL.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")