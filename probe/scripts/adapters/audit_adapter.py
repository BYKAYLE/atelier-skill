"""audit skill adapter.

Calls the ~/.claude/skills/audit/SKILL.md prompt against the artefacts
probe collected for one combination (screenshot, console/network logs,
axe-core violations, DOM state). Returns a JSON verdict that a new
`auditCheck` assertion in checks.py converts into a CheckResult.

The audit skill is *prompt-style* (no scripts), so we inject its SKILL.md
as a system-level brief and pass a compact summary of probe's artefacts
as the user message. Codex CLI runs with an output schema, so the result
shape is stable regardless of the underlying model.

Design choices
--------------
- Non-destructive: we only *read* ~/.claude/skills/audit/SKILL.md. If the
  file is missing we return a skipped verdict so the assertion degrades
  gracefully.
- Severity mapping follows base_adapter's schema: minor / major / critical.
- Scope is intentionally narrow: probe already has axe-core for automated
  a11y; audit adds qualitative judgements (hierarchy, theming consistency,
  responsive feel) that automated tooling can't catch.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base_adapter import invoke_skill, load_skill_prompt


DEFAULT_LABEL = "audit"


AUDIT_OUTPUT_CONTRACT = """
You are running the `audit` Claude Code skill over a single probe
combination. Use the SKILL BRIEF above as your instructions, but override
any "document only, don't fix" guidance to the extent that you must still
return a structured verdict.

Respond with ONE JSON object matching the supplied schema. No prose, no
markdown, no explanation outside the JSON.

Scoring rules:
- ok=true only if there are NO critical or major findings.
- severity reflects the *worst* finding.
- Each finding must be atomic — one issue per entry. Do not aggregate.
- Prefer concrete selectors/paths in `selector` when visible. Omit if
  unknown.
- Categories to use: "a11y", "performance", "responsive", "theming",
  "hierarchy", "semantics", "other".
"""


def run_audit_adapter(
    assertion_cfg: dict[str, Any],
    context_payload: dict[str, Any],
    *,
    screenshot: Path | None = None,
    timeout: float = 120.0,
    model: str | None = None,
) -> dict[str, Any]:
    """Run the audit skill against probe artefacts for one combination.

    Parameters
    ----------
    assertion_cfg : dict
        The YAML config for this `auditCheck` assertion (optional `label`,
        `focus`, `severity`, `impact`). `focus` narrows the audit prompt
        (e.g., "forms only", "hero section").
    context_payload : dict
        Pre-built summary of the combination: bindings, console samples,
        axe violations, network failures, element snapshots, URL.
    screenshot : Path | None
        Path to the combination's screenshot. Passed to Codex as `-i`.
    """
    label = assertion_cfg.get("label") or DEFAULT_LABEL

    skill_brief = load_skill_prompt("audit")
    if not skill_brief:
        return {
            "label": label, "skipped": True, "ok": True,
            "reason": "audit SKILL.md not found — adapter degraded to skip",
        }

    focus = (assertion_cfg.get("focus") or "").strip()
    impact_filter = assertion_cfg.get("impact") or ["critical", "major"]

    artefact_block = _serialise_artefacts(context_payload)

    prompt_parts = [
        "=== SKILL BRIEF (from ~/.claude/skills/audit/SKILL.md) ===",
        skill_brief.strip(),
        "",
        "=== OUTPUT CONTRACT ===",
        AUDIT_OUTPUT_CONTRACT.strip(),
        "",
        "=== PROBE COMBINATION ARTEFACTS ===",
        artefact_block,
        "",
        "=== FOCUS ===",
        focus or "(no narrowing — full audit scope)",
        "",
        "=== IMPACT FILTER ===",
        ", ".join(impact_filter),
    ]
    prompt = "\n".join(prompt_parts)

    return invoke_skill(
        label=label,
        prompt=prompt,
        screenshot=screenshot,
        timeout=timeout,
        model=model or assertion_cfg.get("model"),
    )


def _serialise_artefacts(payload: dict[str, Any]) -> str:
    """Produce a compact, token-cheap summary of probe's RunContext."""
    def _trim(items: Any, n: int = 6) -> Any:
        if isinstance(items, list):
            return items[:n]
        return items

    compact = {
        "url": payload.get("url"),
        "bindings": payload.get("bindings", {}),
        "console_errors": _trim(payload.get("console_errors", [])),
        "console_warnings": _trim(payload.get("console_warnings", [])),
        "js_errors": _trim(payload.get("js_errors", [])),
        "network_failures": _trim(payload.get("network_failures", [])),
        "broken_links": _trim(payload.get("broken_links", [])),
        "axe_violations": _trim(payload.get("axe_violations", []), 10),
        "element_state": payload.get("element_state", {}),
    }
    return json.dumps(compact, ensure_ascii=False, indent=2, default=str)