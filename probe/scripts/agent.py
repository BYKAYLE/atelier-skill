"""Agentic browser driver.

Operates like browser-use: each step, capture the page state (screenshot +
numbered interactive-element list), ask an LLM what to do next, execute the
returned action via Playwright, repeat until `done`. Built to use the Codex
CLI (ChatGPT OAuth) as the brain, so no API key is needed.

The action taxonomy is a MVP subset inspired by browser-use:
    navigate, click, type_text, select, scroll, wait, go_back, find_text, done

Element addressing is by integer index into a per-step list of visible
interactive elements. The agent picks an index; execution uses the stored
centre coordinates.

State per step:
    - url
    - element list (numbered) — kept short + token-efficient
    - viewport size
    - last N step summaries
    - screenshot image (attached via Codex -i)

LLM response (JSON, constrained via --output-schema):
    { reasoning, action_name, <args...>, done_success? }
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llm_judge import _resolve_codex  # reuse Codex resolver


_AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.4/axe.min.js"


def _fingerprint(url: str, kind: str, message: str) -> str:
    """Stable hash used for dedupe within a run and regression DB across runs."""
    import re as _re
    from urllib.parse import urlparse
    u = urlparse(url or "")
    route = (u.path or "/").rstrip("/") or "/"
    # Normalise numbers / IDs in the message so "HTTP 500 /api/v1/orders/123"
    # and "HTTP 500 /api/v1/orders/456" share a fingerprint.
    norm = _re.sub(r"\d+", "N", message or "")[:200]
    h = hashlib.sha1(f"{route}|{kind}|{norm}".encode("utf-8")).hexdigest()
    return h[:12]


MAX_ELEMENTS_PER_STEP = 60
MAX_LABEL_LEN = 80
DEFAULT_MAX_STEPS = 25
DEFAULT_PER_STEP_TIMEOUT = 90


_ACTION_NAMES = [
    "navigate",
    "click",
    "type_text",
    "select",
    "scroll",
    "wait",
    "go_back",
    "find_text",
    "hover",
    "drag",
    "press_key",
    "done",
]


_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "reasoning", "action_name",
        "url", "index", "text", "value",
        "direction", "pages", "ms",
        "key", "to_index", "dx", "dy",
        "summary", "success",
    ],
    "properties": {
        "reasoning": {"type": "string"},
        "action_name": {"enum": _ACTION_NAMES},
        "url":       {"type": ["string", "null"]},
        "index":     {"type": ["integer", "null"]},
        "text":      {"type": ["string", "null"]},
        "value":     {"type": ["string", "null"]},
        "direction": {"type": ["string", "null"], "enum": ["up", "down", None]},
        "pages":     {"type": ["number", "null"]},
        "ms":        {"type": ["integer", "null"]},
        "key":       {"type": ["string", "null"]},
        "to_index":  {"type": ["integer", "null"]},
        "dx":        {"type": ["number", "null"]},
        "dy":        {"type": ["number", "null"]},
        "summary":   {"type": ["string", "null"]},
        "success":   {"type": ["boolean", "null"]},
    },
}


SYSTEM_PROTOCOL = """You are an autonomous browser agent driving a real web page via Playwright. Each turn:
- You receive the goal, a short history of what you already did, the current URL, a list of visible interactive elements (numbered [0]..[N-1]) with their tag, role, label, and — attached — a screenshot of the viewport.
- You must pick exactly ONE action and emit it as JSON matching the supplied schema.
- Before the action, give one short `reasoning` sentence explaining why.

Action catalogue:
  navigate      {url}                        — go to a fresh URL
  click         {index}                      — click element [index]
  type_text     {index, text}                — focus [index] and type text (overwrites existing)
  select        {index, value}               — set <select> element [index] to value
  scroll        {direction: up|down, pages}  — scroll N pages (default 1.0)
  wait          {ms}                         — pause (50..5000)
  go_back                                    — browser back button
  find_text     {text}                       — scroll so the given text is visible
  hover         {index}                      — move mouse over [index] (reveals hover menus)
  drag          {index, to_index?, dx?, dy?} — drag from [index] to another element OR by delta
  press_key     {key}                        — press a keyboard key (Enter, Tab, Escape, ArrowDown, etc.)
  done          {summary, success}           — stop. success=false if you gave up.

Rules:
- Prefer click/type_text on elements shown in the list. Do not invent indices.
- If the element you want is not listed, try `scroll` first; do not guess CSS.
- Issue `done` as soon as the goal is met. Use success=false if you are stuck.
- Keep `reasoning` under 200 chars.
- Output only the JSON object, no prose, no markdown."""


@dataclass
class StepRecord:
    step: int
    url: str
    reasoning: str
    action_name: str
    args: dict[str, Any]
    result: str
    screenshot: str | None = None
    error: str | None = None


@dataclass
class Finding:
    kind: str           # "console_error" | "js_error" | "network_4xx" | "network_5xx" | "axe_critical" | "axe_serious" | "broken_link"
    severity: str       # "minor" | "major" | "critical"
    url: str
    step: int           # agent step at which this was first seen
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    fingerprint: str = ""   # stable hash for regression DB


@dataclass
class AgentRun:
    goal: str
    steps: list[StepRecord] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)   # automated evidence
    final_summary: str = ""
    agent_claimed_success: bool = False                     # what Codex said
    success: bool = False                                   # ground truth (after override)
    verdict: str = ""                                       # "pass" | "warn" | "fail"
    stopped_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "verdict": self.verdict,
            "agent_claimed_success": self.agent_claimed_success,
            "success": self.success,
            "stopped_reason": self.stopped_reason,
            "final_summary": self.final_summary,
            "step_count": len(self.steps),
            "finding_count": len(self.findings),
            "findings": [
                {
                    "kind": f.kind,
                    "severity": f.severity,
                    "url": f.url,
                    "step": f.step,
                    "message": f.message,
                    "details": f.details,
                    "fingerprint": f.fingerprint,
                }
                for f in self.findings
            ],
            "steps": [
                {
                    "step": s.step,
                    "url": s.url,
                    "reasoning": s.reasoning,
                    "action": s.action_name,
                    "args": s.args,
                    "result": s.result,
                    "screenshot": s.screenshot,
                    "error": s.error,
                }
                for s in self.steps
            ],
        }


_ELEMENT_JS = r"""
() => {
  const sel = 'a[href], button, input:not([type="hidden"]), select, textarea, '
            + '[role="button"], [role="link"], [role="tab"], [role="menuitem"], '
            + '[role="checkbox"], [role="switch"], [role="radio"], '
            + '[contenteditable="true"], [tabindex]:not([tabindex="-1"])';
  const vh = window.innerHeight, vw = window.innerWidth;
  const out = [];
  document.querySelectorAll(sel).forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    if (r.bottom < -50 || r.top > vh + 400) return;
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') return;
    const raw = (el.innerText || el.getAttribute('aria-label') || el.value || el.placeholder || el.getAttribute('title') || '').trim();
    const label = raw.replace(/\s+/g, ' ').slice(0, %MAX_LABEL_LEN%);
    out.push({
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || null,
      type: el.getAttribute('type') || null,
      label,
      href: el.getAttribute('href') || null,
      disabled: !!el.disabled,
      x: Math.round(r.left + r.width / 2),
      y: Math.round(r.top + r.height / 2),
      w: Math.round(r.width),
      h: Math.round(r.height),
    });
  });
  return out.slice(0, %MAX_ELEMENTS%);
}
""".replace("%MAX_LABEL_LEN%", str(MAX_LABEL_LEN)).replace(
    "%MAX_ELEMENTS%", str(MAX_ELEMENTS_PER_STEP)
)


class AgentError(Exception):
    pass


class Agent:
    """Drives a Playwright page toward a natural-language goal via Codex."""

    def __init__(
        self,
        page,
        goal: str,
        out_dir: Path,
        *,
        max_steps: int = DEFAULT_MAX_STEPS,
        step_timeout: float = DEFAULT_PER_STEP_TIMEOUT,
        model: str | None = None,
    ):
        self.page = page
        self.goal = goal
        self.out_dir = out_dir
        self.max_steps = max_steps
        self.step_timeout = step_timeout
        self.model = model
        self.run = AgentRun(goal=goal)
        self._elements: list[dict[str, Any]] = []
        self._seen_finger_prints: set[str] = set()
        self._current_step: int = 0
        self._install_listeners()

    # ----- listeners / findings ---------------------------------------------

    def _install_listeners(self) -> None:
        """Attach console, pageerror, and response listeners to the agent's page
        so every automated signal is captured — regardless of what the LLM thinks."""
        try:
            self.page.on("console", self._on_console)
            self.page.on("pageerror", self._on_pageerror)
            self.page.on("response", self._on_response)
        except Exception:
            pass

    def _on_console(self, msg) -> None:
        try:
            if msg.type not in {"error", "warning"}:
                return
            text = (msg.text or "")[:500]
            # lucide / axe / dev noise suppression — keep them but marked minor
            is_error = msg.type == "error"
            kind = "console_error" if is_error else "console_warning"
            sev = "major" if is_error else "minor"
            self._add_finding(kind=kind, severity=sev, message=text,
                              details={"location": str(getattr(msg, "location", ""))})
        except Exception:
            pass

    def _on_pageerror(self, exc) -> None:
        try:
            text = str(exc)[:500]
            self._add_finding(kind="js_error", severity="critical",
                              message=text, details={})
        except Exception:
            pass

    def _on_response(self, resp) -> None:
        try:
            status = resp.status
            if status < 400:
                return
            url = resp.url
            # Skip analytics / telemetry noise commonly ignored in manual QA
            if any(s in url for s in ("/analytics", "/beacon", "/tracking", "google-analytics.com")):
                return
            rtype = getattr(resp.request, "resource_type", "") or ""
            # 4xx on documents / XHR / fetch is meaningful; ignore 404 on
            # optional resources like /favicon.ico
            if url.endswith("/favicon.ico") and status == 404:
                return
            kind = "network_5xx" if status >= 500 else "network_4xx"
            sev = "critical" if status >= 500 else "major"
            self._add_finding(kind=kind, severity=sev,
                              message=f"HTTP {status} {resp.url}",
                              details={"status": status, "url": url, "type": rtype})
        except Exception:
            pass

    def _add_finding(self, *, kind: str, severity: str, message: str,
                     details: dict[str, Any]) -> None:
        url = self._safe_url()
        fp = _fingerprint(url, kind, message)
        if fp in self._seen_finger_prints:
            return  # dedupe within a single run
        self._seen_finger_prints.add(fp)
        self.run.findings.append(Finding(
            kind=kind, severity=severity, url=url,
            step=self._current_step, message=message,
            details=details, fingerprint=fp,
        ))

    def _run_axe(self) -> None:
        """Inject axe-core and collect critical/serious violations."""
        try:
            self.page.add_script_tag(url=_AXE_CDN)
            self.page.wait_for_function(
                "window.axe && typeof window.axe.run === 'function'", timeout=5000)
            result = self.page.evaluate("async () => await window.axe.run()")
            for v in (result or {}).get("violations", []):
                impact = v.get("impact") or "minor"
                if impact not in {"critical", "serious"}:
                    continue
                kind = f"axe_{impact}"
                sev = "critical" if impact == "critical" else "major"
                msg = f"{v.get('id', 'axe')}: {v.get('help', '')} ({len(v.get('nodes', []))} nodes)"
                self._add_finding(kind=kind, severity=sev, message=msg,
                                  details={"id": v.get("id"), "help_url": v.get("helpUrl")})
        except Exception:
            pass

    # ----- public ------------------------------------------------------------

    def loop(self) -> AgentRun:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        codex = _resolve_codex()
        if not codex:
            self.run.stopped_reason = "codex CLI not found"
            self._finalise_verdict()
            return self.run

        for step_n in range(1, self.max_steps + 1):
            self._current_step = step_n
            # Periodic a11y + pre-done a11y scan
            if step_n == 1 or step_n % 5 == 0:
                self._run_axe()
            shot_path = self.out_dir / f"step-{step_n:02d}.png"
            # On the first iteration give the observer-guard init script a
            # chance to disconnect self-retriggering observers that would
            # otherwise block screenshot CDP calls.
            settle_ms = 1600 if step_n == 1 else 250
            try:
                self.page.wait_for_timeout(settle_ms)
                self.page.screenshot(path=str(shot_path), full_page=False, timeout=15000)
            except Exception as e:
                err = f"screenshot_failed: {e}"
                self._record(step_n, self._safe_url(), err, "screenshot_failed", {}, err, None, error=str(e))
                continue

            try:
                self._elements = self.page.evaluate(_ELEMENT_JS) or []
            except Exception as e:
                self._elements = []
                err = f"element enumeration failed: {e}"
                self._record(step_n, self.page.url, "enumerate_failed", "", {}, err, str(shot_path), error=err)
                self.run.stopped_reason = err
                return self.run

            prompt = self._build_prompt(step_n)
            try:
                decision = self._ask_codex(prompt, shot_path, codex)
            except AgentError as e:
                self._record(step_n, self.page.url, str(e), "llm_error", {}, "", str(shot_path), error=str(e))
                self.run.stopped_reason = f"llm error: {e}"
                return self.run

            action = decision.get("action_name")
            reasoning = decision.get("reasoning", "")
            args = {k: v for k, v in decision.items()
                    if k not in {"reasoning", "action_name"} and v is not None}

            if action == "done":
                self.run.agent_claimed_success = bool(decision.get("success", False))
                self.run.final_summary = decision.get("summary", "")
                self._record(step_n, self.page.url, reasoning, "done", args, "stopped", str(shot_path))
                self.run.stopped_reason = "done"
                # Final a11y scan before wrapping up
                self._run_axe()
                self._finalise_verdict()
                return self.run

            try:
                result = self._execute(action, args)
            except Exception as e:
                result = f"execute error: {e}"
                self._record(step_n, self.page.url, reasoning, action, args, result, str(shot_path), error=str(e))
                continue

            self._record(step_n, self.page.url, reasoning, action, args, result, str(shot_path))

        self.run.stopped_reason = "max_steps reached"
        self._finalise_verdict()
        return self.run

    def _finalise_verdict(self) -> None:
        """Ground-truth override: compute verdict from accumulated findings,
        regardless of what the LLM claimed. This is the hard assertion layer."""
        critical = sum(1 for f in self.run.findings if f.severity == "critical")
        major = sum(1 for f in self.run.findings if f.severity == "major")
        # rules:
        #   any critical finding             → fail
        #   any major finding                → fail (conservative for QA)
        #   only minor findings              → warn
        #   zero findings + agent success    → pass
        #   zero findings + agent fail/stop  → warn (couldn't finish, but nothing observed)
        if critical > 0 or major > 0:
            self.run.verdict = "fail"
            self.run.success = False
        elif any(f.severity == "minor" for f in self.run.findings):
            self.run.verdict = "warn"
            self.run.success = False
        elif self.run.agent_claimed_success:
            self.run.verdict = "pass"
            self.run.success = True
        else:
            self.run.verdict = "warn"
            self.run.success = False

    # ----- internals ---------------------------------------------------------

    def _safe_url(self) -> str:
        try:
            return self.page.url
        except Exception:
            return "(unknown)"

    def _record(self, step, url, reasoning, action, args, result, shot, error=None):
        self.run.steps.append(StepRecord(
            step=step, url=url, reasoning=reasoning,
            action_name=action, args=args, result=result,
            screenshot=shot, error=error,
        ))

    def _build_prompt(self, step_n: int) -> str:
        lines = [SYSTEM_PROTOCOL, ""]
        lines.append(f"GOAL: {self.goal}")
        lines.append("")
        lines.append(f"STEP: {step_n} / {self.max_steps}")
        try:
            lines.append(f"URL: {self.page.url}")
        except Exception:
            lines.append("URL: (unknown)")
        try:
            vw = self.page.viewport_size or {}
            lines.append(f"VIEWPORT: {vw.get('width', '?')}x{vw.get('height', '?')}")
        except Exception:
            pass
        lines.append("")
        lines.append("RECENT ACTIONS:")
        history = self.run.steps[-6:]
        if not history:
            lines.append("  (none)")
        else:
            for h in history:
                arg_str = ", ".join(f"{k}={v!r}" for k, v in h.args.items()) or "-"
                lines.append(f"  step {h.step}: {h.action_name}({arg_str}) → {h.result[:80]}")
        lines.append("")
        lines.append("INTERACTIVE ELEMENTS (visible in or near viewport):")
        if not self._elements:
            lines.append("  (none detected — try scrolling or navigating)")
        else:
            for i, el in enumerate(self._elements):
                label = el.get("label") or ""
                tag = el.get("tag")
                role = el.get("role")
                extra = f" role={role}" if role else ""
                type_ = el.get("type")
                if type_:
                    extra += f" type={type_}"
                if el.get("disabled"):
                    extra += " [disabled]"
                lines.append(f"  [{i}] <{tag}>{extra} {label!r}")
        lines.append("")
        lines.append("Return one action as JSON matching the schema.")
        return "\n".join(lines)

    def _ask_codex(self, prompt: str, screenshot: Path, codex: str) -> dict[str, Any]:
        schema_fd, schema_path = tempfile.mkstemp(suffix=".json", prefix="probe-agent-")
        out_fd, out_path = tempfile.mkstemp(suffix=".txt", prefix="probe-agent-")
        os.close(schema_fd)
        os.close(out_fd)
        try:
            Path(schema_path).write_text(json.dumps(_RESPONSE_SCHEMA), encoding="utf-8")
            cmd = [
                codex, "exec",
                "--skip-git-repo-check",
                "--sandbox", "read-only",
                "-i", str(screenshot),
                "--output-schema", schema_path,
                "-o", out_path,
                "-",
            ]
            if self.model:
                cmd[2:2] = ["-m", self.model]
            try:
                proc = subprocess.run(
                    cmd, input=prompt, capture_output=True, text=True,
                    timeout=self.step_timeout, encoding="utf-8", errors="replace",
                )
            except subprocess.TimeoutExpired as e:
                raise AgentError(f"codex exec timed out after {self.step_timeout}s") from e
            if proc.returncode != 0:
                raise AgentError(f"codex exec failed: {(proc.stderr or '')[-300:]}")
            text = Path(out_path).read_text(encoding="utf-8", errors="replace").strip()
            parsed = _extract_json(text) or _extract_json(proc.stdout or "")
            if not parsed:
                raise AgentError(f"codex response not parseable: {text[:300]}")
            if parsed.get("action_name") not in _ACTION_NAMES:
                raise AgentError(f"unknown action_name: {parsed.get('action_name')!r}")
            return parsed
        finally:
            for p in (schema_path, out_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    # ----- action executors --------------------------------------------------

    def _execute(self, action: str, args: dict[str, Any]) -> str:
        page = self.page
        if action == "navigate":
            url = args.get("url")
            if not url:
                return "skip: url missing"
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            return f"navigated to {url}"

        if action == "wait":
            ms = max(50, min(5000, int(args.get("ms", 500))))
            page.wait_for_timeout(ms)
            return f"waited {ms}ms"

        if action == "go_back":
            try:
                page.go_back(wait_until="domcontentloaded", timeout=8000)
                return "went back"
            except Exception as e:
                return f"go_back failed: {e}"

        if action == "scroll":
            direction = args.get("direction", "down")
            pages = float(args.get("pages", 1.0) or 1.0)
            dy = int((1 if direction == "down" else -1) * pages * (page.viewport_size or {}).get("height", 800))
            page.mouse.wheel(0, dy)
            page.wait_for_timeout(250)
            return f"scrolled {direction} {pages} page(s)"

        if action == "find_text":
            needle = args.get("text", "")
            if not needle:
                return "skip: text missing"
            try:
                loc = page.get_by_text(needle, exact=False).first
                loc.scroll_into_view_if_needed(timeout=5000)
                return f"scrolled to text {needle!r}"
            except Exception as e:
                return f"find_text miss: {e}"

        if action == "press_key":
            key = args.get("key") or ""
            if not key:
                return "skip: key missing"
            try:
                page.keyboard.press(key)
                page.wait_for_timeout(150)
                return f"pressed {key!r}"
            except Exception as e:
                return f"press_key failed: {e}"

        # Element-targeted actions
        idx = args.get("index")
        if idx is None or not isinstance(idx, int) or idx < 0 or idx >= len(self._elements):
            return f"skip: invalid index {idx!r} (have {len(self._elements)} elements)"
        el = self._elements[idx]

        if action == "click":
            try:
                page.mouse.click(el["x"], el["y"])
                page.wait_for_timeout(200)
                return f"clicked [{idx}] {el['label'][:50]!r}"
            except Exception as e:
                return f"click failed: {e}"

        if action == "type_text":
            text = args.get("text", "")
            try:
                page.mouse.click(el["x"], el["y"])
                # Clear existing then type
                page.keyboard.press("Control+A")
                page.keyboard.press("Delete")
                page.keyboard.type(text, delay=20)
                return f"typed into [{idx}]: {text[:40]!r}"
            except Exception as e:
                return f"type_text failed: {e}"

        if action == "hover":
            try:
                page.mouse.move(el["x"], el["y"])
                page.wait_for_timeout(300)
                return f"hovered [{idx}] {el['label'][:50]!r}"
            except Exception as e:
                return f"hover failed: {e}"

        if action == "drag":
            to_index = args.get("to_index")
            dx = args.get("dx")
            dy = args.get("dy")
            try:
                tx = ty = None
                if to_index is not None and 0 <= int(to_index) < len(self._elements):
                    tgt = self._elements[int(to_index)]
                    tx, ty = tgt["x"], tgt["y"]
                elif dx is not None or dy is not None:
                    tx = el["x"] + int(dx or 0)
                    ty = el["y"] + int(dy or 0)
                else:
                    return "skip: drag needs to_index or dx/dy"
                page.mouse.move(el["x"], el["y"])
                page.mouse.down()
                # Intermediate steps so frameworks that listen on drag events fire
                steps = 10
                for i in range(1, steps + 1):
                    page.mouse.move(
                        el["x"] + (tx - el["x"]) * i / steps,
                        el["y"] + (ty - el["y"]) * i / steps,
                    )
                page.mouse.up()
                page.wait_for_timeout(250)
                return f"dragged [{idx}] to ({tx},{ty})"
            except Exception as e:
                return f"drag failed: {e}"

        if action == "select":
            value = str(args.get("value", ""))
            try:
                # Try using DOM select value by clicking to focus then selecting
                page.evaluate(
                    "([x, y, value]) => {"
                    "  const el = document.elementFromPoint(x, y);"
                    "  const sel = el && (el.tagName === 'SELECT' ? el : el.closest('select'));"
                    "  if (!sel) return false;"
                    "  sel.value = value;"
                    "  sel.dispatchEvent(new Event('change', { bubbles: true }));"
                    "  return true;"
                    "}",
                    [el["x"], el["y"], value],
                )
                return f"selected value {value!r} at [{idx}]"
            except Exception as e:
                return f"select failed: {e}"

        return f"unknown action {action!r}"


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    s = text.strip()
    if s.startswith("```"):
        parts = s.splitlines()
        if parts and parts[0].startswith("```"):
            parts = parts[1:]
        if parts and parts[-1].startswith("```"):
            parts = parts[:-1]
        s = "\n".join(parts).strip()
    m_start = s.find("{")
    m_end = s.rfind("}")
    if m_start < 0 or m_end < m_start:
        return None
    try:
        return json.loads(s[m_start : m_end + 1])
    except json.JSONDecodeError:
        return None


def write_journal(run: AgentRun, journal_dir: Path) -> Path:
    journal_dir.mkdir(parents=True, exist_ok=True)
    md = journal_dir / "journal.md"
    verdict_icon = {"pass": "✅", "warn": "🟡", "fail": "🔴"}.get(run.verdict, "❓")
    lines = [
        f"# Agent journal — {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"**Goal**: {run.goal}",
        "",
        f"- **Verdict**: {verdict_icon} **{run.verdict.upper()}** (ground truth: automated evidence overrides LLM claim)",
        f"- **Agent claimed**: {'success' if run.agent_claimed_success else 'not success'}",
        f"- **Stopped because**: {run.stopped_reason}",
        f"- **Steps**: {len(run.steps)}  |  **Findings**: {len(run.findings)}",
        f"- **Final summary**: {run.final_summary or '—'}",
        "",
    ]

    # Findings section — put this up top so it's the first thing a reviewer sees
    if run.findings:
        lines.append("## Automated findings (ground truth)")
        lines.append("")
        by_sev = {"critical": [], "major": [], "minor": []}
        for f in run.findings:
            by_sev.setdefault(f.severity, []).append(f)
        for sev in ("critical", "major", "minor"):
            if not by_sev.get(sev):
                continue
            icon = {"critical": "🔴", "major": "🟠", "minor": "🟡"}[sev]
            lines.append(f"### {icon} {sev} ({len(by_sev[sev])})")
            lines.append("")
            for f in by_sev[sev]:
                lines.append(f"- **[{f.kind}]** step {f.step}  |  `{f.url}`  |  `{f.fingerprint}`")
                lines.append(f"  - {f.message}")
            lines.append("")
    else:
        lines.append("## Automated findings")
        lines.append("")
        lines.append("✅ No console / network / a11y issues observed during the run.")
        lines.append("")

    lines.append("## Steps")
    lines.append("")
    for s in run.steps:
        lines.append(f"### Step {s.step} — `{s.action_name}`")
        arg_str = ", ".join(f"`{k}`={v!r}" for k, v in s.args.items()) or "—"
        lines.append(f"- URL: `{s.url}`")
        lines.append(f"- Args: {arg_str}")
        lines.append(f"- Reasoning: {s.reasoning}")
        lines.append(f"- Result: {s.result}")
        if s.error:
            lines.append(f"- **Error**: {s.error}")
        if s.screenshot:
            rel = Path(s.screenshot).name
            lines.append(f"- ![step-{s.step}]({rel})")
        lines.append("")
    md.write_text("\n".join(lines), encoding="utf-8")
    (journal_dir / "run.json").write_text(
        json.dumps(run.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return md
