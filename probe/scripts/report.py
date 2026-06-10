"""Markdown report generator.

Writes report.md summarising all combinations. Uses a Jinja template when
available, otherwise falls back to a minimal inline renderer.
"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    Environment = None


SEV_ORDER = {"critical": 3, "major": 2, "minor": 1, "info": 0}
SEV_ICON = {"critical": "🔴", "major": "🟠", "minor": "🟡", "info": "⚪"}


def write_report(
    results: list[dict[str, Any]],
    plan_name: str,
    plan_target: str,
    out_dir: Path,
    template_dir: Path | None = None,
) -> Path:
    summary = _summarise(results)
    context = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "plan_name": plan_name,
        "plan_target": plan_target,
        "summary": summary,
        "results": results,
        "SEV_ICON": SEV_ICON,
    }

    report_path = out_dir / "report.md"
    if Environment and template_dir and (template_dir / "report.md.jinja").exists():
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(disabled_extensions=("md", "jinja")),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        tpl = env.get_template("report.md.jinja")
        report_path.write_text(tpl.render(**context), encoding="utf-8")
    else:
        report_path.write_text(_inline_render(context), encoding="utf-8")

    # Emit a machine-readable JSON summary alongside.
    (out_dir / "summary.json").write_text(
        json.dumps(_serialisable(summary), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report_path


def _summarise(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r["overall"] == "pass")
    warned = sum(1 for r in results if r["overall"] == "warn")
    failed = sum(1 for r in results if r["overall"] == "fail")
    severities = {"critical": 0, "major": 0, "minor": 0}
    for r in results:
        for c in r["checks"]:
            if not c["ok"] and c["severity"] in severities:
                severities[c["severity"]] += 1
    return {
        "total": total,
        "passed": passed,
        "warned": warned,
        "failed": failed,
        "severities": severities,
    }


def _inline_render(ctx: dict[str, Any]) -> str:
    s = ctx["summary"]
    lines = [
        f"# probe · {ctx['plan_name']}",
        "",
        f"- **Target**: `{ctx['plan_target']}`",
        f"- **Generated**: {ctx['generated_at']}",
        f"- **Combinations**: {s['total']}  ·  "
        f"✅ pass {s['passed']}  ·  🟡 warn {s['warned']}  ·  🔴 fail {s['failed']}",
        "",
        f"**Severity counts** — critical {s['severities']['critical']}, "
        f"major {s['severities']['major']}, minor {s['severities']['minor']}",
        "",
        "## Matrix",
        "",
        "| # | Bindings | VP | Browser | Result | Failing checks |",
        "|---|---|---|---|---|---|",
    ]
    for r in ctx["results"]:
        b = r["bindings"]
        b_str = ", ".join(f"`{k}`={v}" for k, v in sorted(b.items()) if not k.startswith("_"))
        vp = b.get("_viewport", "")
        br = b.get("_browser", "")
        sign = {"pass": "✅", "warn": "🟡", "fail": "🔴"}[r["overall"]]
        failing = ", ".join(c["name"] for c in r["checks"] if not c["ok"]) or "—"
        lines.append(f"| {r['id']} | {b_str} | {vp} | {br} | {sign} {r['overall']} | {failing} |")

    lines.append("")
    # Failed cases detail
    failures = [r for r in ctx["results"] if r["overall"] == "fail"]
    if failures:
        lines.append("## Failures")
        lines.append("")
        for r in failures:
            lines.append(f"### {r['id']} — {_fmt_bindings(r['bindings'])}")
            lines.append("")
            if r.get("screenshot"):
                lines.append(f"![screenshot]({r['screenshot']})")
                lines.append("")
            for c in r["checks"]:
                if c["ok"]:
                    continue
                icon = SEV_ICON.get(c["severity"], "⚪")
                lines.append(f"- {icon} **{c['name']}** ({c['severity']}) — {c['message']}")
                details = c.get("details") or {}
                if details:
                    snippet = json.dumps(details, ensure_ascii=False, indent=2)
                    if len(snippet) > 800:
                        snippet = snippet[:800] + "…"
                    lines.append("  <details><summary>details</summary>\n\n```json\n" + snippet + "\n```\n</details>")
            lines.append("")
            lines.append(f"Reproduce: `{r.get('reproduce', '')}`")
            lines.append("")

    lines.append("## Warnings")
    lines.append("")
    warns = [r for r in ctx["results"] if r["overall"] == "warn"]
    if not warns:
        lines.append("(none)")
    else:
        for r in warns:
            lines.append(f"- {r['id']} — " + ", ".join(
                f"{c['name']} ({c['severity']})" for c in r["checks"] if not c["ok"]
            ))

    return "\n".join(lines) + "\n"


def _fmt_bindings(b: dict[str, Any]) -> str:
    return " · ".join(
        f"{k}={v}" for k, v in sorted(b.items()) if not k.startswith("_")
    ) or "(no dims)"


def _serialisable(obj: Any) -> Any:
    if is_dataclass(obj):
        return _serialisable(asdict(obj))
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (list, tuple)):
        return [_serialisable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _serialisable(v) for k, v in obj.items()}
    return obj
