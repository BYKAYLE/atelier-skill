"""Probe skill adapters.

Each adapter wraps a prompt-style Claude Code skill (audit, harden, ...) so
probe can invoke it as a Judge-stage assertion. Adapters preserve the
original skills intact — they only *call* them, never replace them.

The call convention mirrors probe's llm_judge: spawn Codex CLI with the
skill's SKILL.md injected as context, constrain output to a JSON schema,
parse the verdict, and push it onto RunContext.adapter_results so a matching
assertion handler in checks.py can turn it into a CheckResult.
"""

from __future__ import annotations

from .audit_adapter import run_audit_adapter

__all__ = ["run_audit_adapter"]