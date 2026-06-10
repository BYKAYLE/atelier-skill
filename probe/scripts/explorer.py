"""Auto-explore: open a URL, inventory interactive elements, propose a plan.

Heuristics:
    - Find <button>, <a[href]>, <input>, <select>, <textarea>, [role=button]
    - Group by visible labels / aria-label / text
    - Detect toggles (pairs), tabs (radiogroups), segmented controls (.seg button)
    - Look for common state stores: localStorage keys referenced by scripts
    - Emit a plan skeleton with dimensions from discovered controls

The output is a best-guess YAML. User should curate before running.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


def explore(url: str, out_path: Path, headless: bool = True) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    findings: dict[str, Any] = {
        "target": url,
        "controls": [],
        "localstorage_keys": [],
        "candidate_dimensions": {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            page = browser.new_context().new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_load_state("networkidle", timeout=7000)

            # 1. Interactive controls with visible labels
            controls = page.evaluate(r"""
            () => {
              const sel = 'button, a[href], input, select, textarea, [role="button"], [role="tab"]';
              const out = [];
              document.querySelectorAll(sel).forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width < 2 || rect.height < 2) return;
                const label = (el.innerText || el.getAttribute('aria-label') || el.placeholder || el.value || '').trim();
                if (!label) return;
                out.push({
                  tag: el.tagName.toLowerCase(),
                  role: el.getAttribute('role') || null,
                  type: el.getAttribute('type') || null,
                  classes: el.className && typeof el.className === 'string' ? el.className.split(/\s+/).slice(0, 3) : [],
                  label: label.slice(0, 60),
                  href: el.getAttribute('href') || null,
                });
              });
              return out;
            }
            """)
            findings["controls"] = controls

            # 2. localStorage keys currently present (from any init script)
            try:
                keys = page.evaluate("() => Object.keys(window.localStorage || {})")
                findings["localstorage_keys"] = keys or []
            except Exception:
                pass

            # 3. Segmented-control dimension detection
            seg_groups = page.evaluate(r"""
            () => {
              const groups = [];
              document.querySelectorAll('.seg, [role="tablist"], [role="radiogroup"]').forEach(g => {
                const items = Array.from(g.querySelectorAll('button, [role="tab"], [role="radio"]'))
                  .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim())
                  .filter(Boolean)
                  .slice(0, 8);
                if (items.length >= 2) groups.push(items);
              });
              return groups;
            }
            """)
            for i, items in enumerate(seg_groups or []):
                key = _slugify(items[0]) or f"dim{i+1}"
                findings["candidate_dimensions"][key] = items

            # 4. Theme toggle heuristic
            has_theme = page.evaluate(r"""
            () => !!document.querySelector('[data-theme], .theme-toggle, [aria-label*="theme" i]')
            """)
            if has_theme and "theme" not in findings["candidate_dimensions"]:
                findings["candidate_dimensions"]["theme"] = ["dark", "light"]

        finally:
            browser.close()

    plan = _to_plan(findings)
    out_path.write_text(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return findings


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    return s.strip("_")


def _to_plan(findings: dict[str, Any]) -> dict[str, Any]:
    dims = findings.get("candidate_dimensions") or {}
    actions: list[dict[str, Any]] = []

    if "theme" in dims:
        actions.append({"setLocalStorage": {"kr.theme": "${theme}"}})
        actions.append("reload")

    plan = {
        "target": findings["target"],
        "name": "auto-explored probe",
        "dimensions": dims or {"stub": ["a", "b"]},
        "viewports": ["desktop"],
        "browsers": ["chromium"],
        "setup": actions if actions else [],
        "actions": [{"wait": 300}],
        "assertions": [
            "noConsoleErrors",
            "noNetworkErrors",
            "noBrokenLinks",
            {"axe": {"impact": ["critical", "serious"]}},
        ],
        "strategy": "pairwise",
        "parallel": 2,
    }

    # Emit candidate-control summary as a YAML comment-compatible block by
    # attaching a '_discovered' key the user can delete.
    plan["_discovered"] = {
        "localstorage_keys": findings.get("localstorage_keys", []),
        "control_count": len(findings.get("controls", [])),
        "sample_controls": [c["label"] for c in findings.get("controls", [])[:15]],
    }
    return plan
