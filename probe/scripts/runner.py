"""Playwright runner — exercises one combination and returns a RunContext.

Responsibilities:
    - launch browser/context with viewport + storage init
    - navigate to target
    - execute each action (click/type/wait/reload/setLocalStorage/injectJS/fill)
    - collect console, page-error, and network logs
    - run inline element-state queries needed by declared assertions
    - capture screenshot
    - harvest links and probe for 404s
    - run axe-core (injected) for a11y

Kept synchronous (playwright.sync_api) for orchestration simplicity.
Parallelism is achieved by spawning subprocess workers (see run_probe.py).
"""
from __future__ import annotations

import json
import re
import traceback
from pathlib import Path
from typing import Any

from checks import RunContext, classify_link, is_same_origin
from plan import Plan, evaluate_skip_if, resolve_vars, viewport_size


# axe-core CDN injection — we fetch once and cache in memory.
_AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.4/axe.min.js"

# Guard against apps that install self-re-triggering MutationObservers
# (e.g. lucide.createIcons() called from a MutationObserver watching the
# same subtree it mutates). Such loops prevent Playwright CDP calls from
# running because the JS main thread never yields. We cap each observer's
# callback invocation count and auto-disconnect past the limit.
_OBS_GUARD = r"""
(function () {
  if (window.__probe_patched__) return;
  window.__probe_patched__ = true;
  const OriginalMO = window.MutationObserver;
  if (!OriginalMO) return;
  const observers = [];
  window.MutationObserver = class extends OriginalMO {
    constructor(cb) {
      super(cb);
      observers.push(this);
    }
  };
  // Disconnect every MutationObserver after 1.5s regardless of load state.
  // Apps that install self-re-triggering observers (e.g. MutationObserver
  // watching a subtree that its callback mutates) would otherwise spin the
  // main thread and block Playwright CDP commands.
  setTimeout(() => {
    for (const ob of observers) {
      try { ob.disconnect(); } catch (e) {}
    }
  }, 1500);
})();
"""


def exercise(
    plan: Plan,
    bindings: dict[str, Any],
    combo_dir: Path,
    baseline_dir: Path,
    *,
    include_llm: bool = True,
    headless: bool = True,
) -> dict[str, Any]:
    """Run one combination. Returns a result dict with RunContext + check rows."""
    from playwright.sync_api import sync_playwright, Error as PWError

    combo_id = combo_dir.name
    ctx = RunContext(
        combination_id=combo_id,
        bindings=bindings,
        url=plan.target,
    )

    combo_dir.mkdir(parents=True, exist_ok=True)

    error: str | None = None
    with sync_playwright() as p:
        browser_name = bindings.get("_browser", "chromium")
        viewport = bindings.get("_viewport", "desktop")
        launcher = getattr(p, browser_name)
        try:
            browser = launcher.launch(headless=headless)
        except PWError as e:
            return {
                "ok": False,
                "error": f"browser launch failed: {e}",
                "context": ctx,
                "checks": [],
            }

        try:
            context = browser.new_context(viewport=viewport_size(viewport))
            page = context.new_page()

            # Console + page error hooks
            def _on_console(msg):
                entry = {"type": msg.type, "text": msg.text, "location": str(msg.location)}
                if msg.type == "error":
                    ctx.console_errors.append(entry)
                elif msg.type == "warning":
                    ctx.console_warnings.append(entry)

            def _on_pageerror(exc):
                ctx.js_errors.append({"type": "pageerror", "text": str(exc)})

            page.on("console", _on_console)
            page.on("pageerror", _on_pageerror)

            def _on_response(resp):
                try:
                    status = resp.status
                    ctx.responses.append({
                        "url": resp.url,
                        "status": status,
                        "request_type": resp.request.resource_type,
                        "resource_type": resp.request.resource_type,
                        "headers": dict(resp.headers),
                    })
                    if status >= 400:
                        ctx.network_failures.append({
                            "url": resp.url,
                            "status": status,
                            "request_type": resp.request.resource_type,
                        })
                except Exception:
                    pass

            page.on("response", _on_response)

            # Apply setup BEFORE navigation (localStorage/cookies seeding).
            # To seed localStorage for the target origin we must navigate first
            # to any page on that origin, then execute, then reload. For file://
            # we can use page.add_init_script.
            seeded_ls = _collect_local_storage(plan.setup, bindings)

            # Always install observer guard first — keeps the page from
            # blocking its own event loop via MutationObserver feedback loops.
            page.add_init_script(_OBS_GUARD)

            if seeded_ls:
                init = _make_init_script(seeded_ls)
                page.add_init_script(init)

            # Navigate
            page.set_default_timeout(7000)
            page.goto(plan.target, wait_until="domcontentloaded", timeout=15000)
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except PWError:
                pass  # networkidle best-effort
            # Give the observer-guard's load handler a chance to fire and
            # disconnect self-re-triggering observers.
            page.wait_for_timeout(1200)

            # Execute remaining (non-seed) setup + actions
            steps = [s for s in plan.setup if "setLocalStorage" not in s] + plan.actions
            for step in steps:
                _run_step(page, step, bindings)

            # Harvest link targets and probe for 404s (head/get)
            _collect_links(page, plan.target, ctx)

            # Populate element_state for each assertion that references selectors
            _collect_element_state(page, plan.assertions, bindings, ctx)

            # axe-core run (if any axe assertion present)
            if _any_assertion(plan.assertions, "axe"):
                _run_axe(page, ctx)

            # Screenshot
            shot = combo_dir / "screenshot.png"
            try:
                page.screenshot(path=str(shot), full_page=True)
                ctx.screenshot_path = str(shot)
            except Exception as e:
                ctx.js_errors.append({"type": "screenshot", "text": str(e)})

            # Visual diff
            if _any_assertion(plan.assertions, "visualDiff"):
                from visual_diff import compare
                baseline_dir.mkdir(parents=True, exist_ok=True)
                cfg = _assertion_cfg(plan.assertions, "visualDiff") or {}
                baseline_name = _baseline_name(bindings)
                baseline_path = baseline_dir / f"{baseline_name}.png"
                diff_path = combo_dir / "diff.png"
                ctx.visual_diff = compare(
                    shot,
                    baseline_path,
                    diff_path,
                    ignore_regions=cfg.get("ignoreRegions"),
                )

        except PWError as e:
            error = f"playwright error: {e}\n{traceback.format_exc()}"
        except Exception as e:
            error = f"runner error: {e}\n{traceback.format_exc()}"
        finally:
            try:
                browser.close()
            except Exception:
                pass

    # Save artefacts
    (combo_dir / "console.log").write_text(
        _join_log(ctx.console_errors + ctx.console_warnings + ctx.js_errors),
        encoding="utf-8",
    )
    (combo_dir / "network.log").write_text(
        _join_log(ctx.network_failures), encoding="utf-8",
    )

    # Write reproduce script (standalone Playwright)
    (combo_dir / "reproduce.py").write_text(
        _make_reproduce_script(plan, bindings), encoding="utf-8",
    )

    return {"ok": error is None, "error": error, "context": ctx}


# ----- actions ----------------------------------------------------------------

def _run_step(page, step: Any, bindings: dict[str, Any]) -> None:
    step = resolve_vars(step, bindings)
    # Bare string shortcuts (e.g. "reload") — no skipIf, no config.
    if isinstance(step, str):
        if step == "reload":
            page.reload(wait_until="domcontentloaded")
        return
    if not isinstance(step, dict):
        return
    skip = step.get("skipIf")
    if skip and evaluate_skip_if(skip, bindings):
        return

    if step.get("reload"):
        page.reload(wait_until="domcontentloaded")
        return

    if "wait" in step:
        ms = int(step["wait"])
        page.wait_for_timeout(ms)
        return

    if "click" in step:
        cfg = step["click"] if isinstance(step["click"], dict) else {"selector": step["click"]}
        sel = cfg.get("selector")
        text = cfg.get("text")
        loc = page.locator(sel)
        if text is not None:
            loc = loc.filter(has_text=text)
        try:
            loc.first.click(timeout=3000)
        except Exception:
            pass
        return

    if "type" in step or "fill" in step:
        cfg = step.get("type") or step.get("fill")
        sel = cfg.get("selector")
        txt = cfg.get("text", "")
        try:
            page.locator(sel).first.fill(txt, timeout=3000)
        except Exception:
            pass
        return

    if "setLocalStorage" in step:
        _apply_local_storage(page, step["setLocalStorage"])
        return

    if "injectJS" in step:
        try:
            page.evaluate(step["injectJS"])
        except Exception:
            pass
        return

    if "scroll" in step:
        cfg = step["scroll"] if isinstance(step["scroll"], dict) else {"y": int(step["scroll"])}
        y = int(cfg.get("y", 0))
        try:
            page.evaluate(f"window.scrollTo(0, {y})")
        except Exception:
            pass
        return

    if "hover" in step:
        sel = step["hover"] if isinstance(step["hover"], str) else step["hover"].get("selector")
        try:
            page.locator(sel).first.hover(timeout=3000)
        except Exception:
            pass
        return


# ----- setup seeding ---------------------------------------------------------

def _collect_local_storage(setup: list[dict[str, Any]], bindings: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for step in setup:
        if "setLocalStorage" in step:
            entries = resolve_vars(step["setLocalStorage"], bindings)
            for k, v in entries.items():
                out[str(k)] = str(v)
    return out


def _make_init_script(ls: dict[str, str]) -> str:
    lines = [
        "try {",
        *[f"  window.localStorage.setItem({json.dumps(k)}, {json.dumps(v)});"
          for k, v in ls.items()],
        "} catch (e) {}",
    ]
    return "\n".join(lines)


def _apply_local_storage(page, entries: dict[str, str]) -> None:
    script = _make_init_script(entries)
    try:
        page.evaluate(script)
    except Exception:
        pass


# ----- element state + links ------------------------------------------------

def _collect_links(page, base: str, ctx: RunContext) -> None:
    try:
        hrefs = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.getAttribute('href'))",
        )
    except Exception:
        return
    seen = set()
    for h in hrefs:
        absu = classify_link(h or "", base)
        if not absu or absu in seen:
            continue
        seen.add(absu)
        # only probe same-origin (and file://) to avoid hammering external sites
        if absu.startswith("file://") or is_same_origin(absu, base):
            _probe(page, absu, ctx)


def _probe(page, url: str, ctx: RunContext) -> None:
    try:
        resp = page.request.fetch(url, method="HEAD", timeout=5000)
        if resp.status >= 400:
            # Retry with GET (some servers 405 HEAD)
            resp = page.request.fetch(url, method="GET", timeout=5000)
        if resp.status >= 400:
            ctx.broken_links.append({"url": url, "status": resp.status})
    except Exception as e:
        ctx.broken_links.append({"url": url, "error": str(e)})


def _any_assertion(assertions: list[Any], name: str) -> bool:
    for a in assertions:
        if a == name:
            return True
        if isinstance(a, dict) and name in a:
            return True
    return False


def _assertion_cfg(assertions: list[Any], name: str) -> dict[str, Any] | None:
    for a in assertions:
        if isinstance(a, dict) and name in a:
            v = a[name]
            return v if isinstance(v, dict) else {}
    return None


def _collect_element_state(page, assertions, bindings, ctx: RunContext) -> None:
    selectors: set[str] = set()
    for a in assertions:
        name, cfg = _split_assertion(a)
        if name in {"hasElement", "elementVisible"}:
            sel = cfg.get("value") or cfg.get("selector")
            if sel:
                selectors.add(resolve_vars(sel, bindings))
        elif name == "elementText":
            sel = cfg.get("selector")
            if sel:
                selectors.add(resolve_vars(sel, bindings))

    for sel in selectors:
        state: dict[str, Any] = {"exists": False, "visible": False, "text": ""}
        try:
            loc = page.locator(sel).first
            cnt = page.locator(sel).count()
            if cnt > 0:
                state["exists"] = True
                try:
                    state["visible"] = loc.is_visible()
                except Exception:
                    state["visible"] = False
                try:
                    state["text"] = (loc.inner_text(timeout=1000) or "").strip()
                except Exception:
                    pass
        except Exception as e:
            state["error"] = str(e)
        ctx.element_state[sel] = state


def _split_assertion(entry: Any) -> tuple[str, dict[str, Any]]:
    if isinstance(entry, str):
        return entry, {}
    if isinstance(entry, dict) and len(entry) == 1:
        k, v = next(iter(entry.items()))
        if v is None:
            v = {}
        elif not isinstance(v, dict):
            v = {"value": v}
        return k, v
    return "unknown", {}


# ----- axe ---------------------------------------------------------------

def _run_axe(page, ctx: RunContext) -> None:
    try:
        page.add_script_tag(url=_AXE_CDN)
        page.wait_for_function("window.axe && typeof window.axe.run === 'function'", timeout=5000)
        result = page.evaluate("async () => await window.axe.run()")
        violations = result.get("violations", []) if isinstance(result, dict) else []
        for v in violations:
            ctx.axe_violations.append({
                "id": v.get("id"),
                "impact": v.get("impact"),
                "help": v.get("help"),
                "nodes": len(v.get("nodes", [])),
            })
    except Exception as e:
        ctx.axe_violations.append({"error": str(e)})


# ----- misc --------------------------------------------------------------

def _baseline_name(bindings: dict[str, Any]) -> str:
    parts = [f"{k}={bindings[k]}" for k in sorted(bindings) if not k.startswith("_")]
    parts += [f"vp={bindings.get('_viewport', 'desktop')}", f"br={bindings.get('_browser', 'chromium')}"]
    raw = "__".join(parts) or "default"
    return re.sub(r"[^a-zA-Z0-9_=-]+", "-", raw)


def _join_log(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "(empty)\n"
    return "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n"


def _make_reproduce_script(plan: Plan, bindings: dict[str, Any]) -> str:
    resolved_setup = [resolve_vars(s, bindings) for s in plan.setup]
    resolved_actions = [resolve_vars(a, bindings) for a in plan.actions]
    vp = bindings.get("_viewport", "desktop")
    br = bindings.get("_browser", "chromium")
    return f'''"""Reproduce script for combination {bindings}.

Run:
    pip install playwright
    playwright install {br}
    python reproduce.py
"""
from playwright.sync_api import sync_playwright

BINDINGS = {json.dumps(bindings, ensure_ascii=False, indent=2)}
SETUP = {json.dumps(resolved_setup, ensure_ascii=False, indent=2)}
ACTIONS = {json.dumps(resolved_actions, ensure_ascii=False, indent=2)}
TARGET = {json.dumps(plan.target)}
VIEWPORT = {json.dumps(viewport_size(vp))}

with sync_playwright() as p:
    browser = p.{br}.launch(headless=False)
    context = browser.new_context(viewport=VIEWPORT)
    page = context.new_page()
    page.goto(TARGET)
    page.wait_for_load_state("networkidle")
    print("Reproduce ready. Bindings:", BINDINGS)
    print("Setup:", SETUP)
    print("Actions:", ACTIONS)
    input("Press enter to close...")
    browser.close()
'''
