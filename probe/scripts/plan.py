"""Probe plan: YAML schema, loader, variable resolution.

A plan declares dimensions (named lists of values), actions to perform per
combination, and assertions to evaluate. The loader validates structure and
returns a typed Plan object. Variable substitution (${var}) happens per
combination in resolve_plan().
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


_VAR = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class PlanError(ValueError):
    pass


@dataclass
class Plan:
    target: str
    name: str = "probe"
    dimensions: dict[str, list[Any]] = field(default_factory=dict)
    viewports: list[str] = field(default_factory=lambda: ["desktop"])
    browsers: list[str] = field(default_factory=lambda: ["chromium"])
    setup: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    assertions: list[Any] = field(default_factory=list)
    strategy: str = "pairwise"
    parallel: int = 2
    output_dir: str | None = None
    path: Path | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def plan_dir(self) -> Path:
        return self.path.parent if self.path else Path.cwd()


_VIEWPORT_PRESETS = {
    "desktop": {"width": 1440, "height": 900},
    "laptop": {"width": 1280, "height": 800},
    "tablet": {"width": 834, "height": 1112},
    "mobile": {"width": 390, "height": 844},
}


def viewport_size(name: str) -> dict[str, int]:
    if name in _VIEWPORT_PRESETS:
        return _VIEWPORT_PRESETS[name]
    raise PlanError(f"unknown viewport preset: {name!r}")


def load_plan(path: str | Path) -> Plan:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise PlanError(f"plan file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    plan = _from_dict(raw)
    plan.path = p
    plan.raw = raw
    return plan


def _from_dict(d: dict[str, Any]) -> Plan:
    if "target" not in d or not isinstance(d["target"], str):
        raise PlanError("plan.target (string URL) is required")
    dims = d.get("dimensions") or {}
    if not isinstance(dims, dict):
        raise PlanError("plan.dimensions must be a mapping")
    for k, v in dims.items():
        if not isinstance(v, list) or not v:
            raise PlanError(f"dimension {k!r} must be a non-empty list")

    strategy = str(d.get("strategy", "pairwise")).lower()
    if not (strategy in {"pairwise", "full"} or strategy.startswith("random:")):
        raise PlanError(f"unknown strategy {strategy!r}; use pairwise | full | random:N")

    parallel = int(d.get("parallel", 2))
    if parallel < 1:
        raise PlanError("parallel must be >= 1")

    for vp in d.get("viewports", ["desktop"]):
        viewport_size(vp)  # validate

    for br in d.get("browsers", ["chromium"]):
        if br not in {"chromium", "firefox", "webkit"}:
            raise PlanError(f"unknown browser {br!r}")

    return Plan(
        target=d["target"],
        name=d.get("name", "probe"),
        dimensions=dims,
        viewports=list(d.get("viewports", ["desktop"])),
        browsers=list(d.get("browsers", ["chromium"])),
        setup=list(d.get("setup") or []),
        actions=list(d.get("actions") or []),
        assertions=list(d.get("assertions") or []),
        strategy=strategy,
        parallel=parallel,
        output_dir=d.get("outputDir"),
    )


def resolve_vars(value: Any, bindings: dict[str, Any]) -> Any:
    """Substitute ${var} tokens in strings anywhere in a nested structure."""
    if isinstance(value, str):
        def repl(m: re.Match[str]) -> str:
            k = m.group(1)
            if k not in bindings:
                return m.group(0)
            return str(bindings[k])
        return _VAR.sub(repl, value)
    if isinstance(value, list):
        return [resolve_vars(v, bindings) for v in value]
    if isinstance(value, dict):
        return {k: resolve_vars(v, bindings) for k, v in value.items()}
    return value


def evaluate_skip_if(expr: str, bindings: dict[str, Any]) -> bool:
    """Evaluate a simple skipIf expression against bindings.

    Supported forms:
        var == "value"
        var != "value"
        var in ["a", "b"]
        var not in ["a", "b"]

    Returns True if the step should be skipped.
    """
    if not expr or not expr.strip():
        return False
    expr = expr.strip()
    # Replace bare variable names with string literals. Only allow [a-zA-Z_]\w*
    # identifiers that match a binding key; everything else is preserved.
    def repl(m: re.Match[str]) -> str:
        name = m.group(0)
        if name in bindings:
            return repr(bindings[name])
        return name
    safe = re.sub(r"[a-zA-Z_][a-zA-Z0-9_]*", repl, expr)
    # Whitelist: allow only these tokens to reach eval.
    if re.search(r"[^\w\s\"'=!<>()\[\],.-]", safe):
        raise PlanError(f"skipIf contains disallowed characters: {expr!r}")
    try:
        return bool(eval(safe, {"__builtins__": {}}, {}))  # noqa: S307 - whitelisted
    except Exception as e:
        raise PlanError(f"skipIf evaluation failed for {expr!r}: {e}")
