"""Automatic assertion implementations.

Each check takes a RunContext (holding logs, page, combination metadata) and
returns a CheckResult (ok / severity / message). Assertions are configured
from YAML; this module translates each entry into a callable.

Supported assertions:
    noConsoleErrors          — no console.error / uncaught exception
    noConsoleWarnings        — no console.warn (default off, opt-in)
    noNetworkErrors          — no 4xx/5xx responses for same-origin requests
    noBrokenLinks            — all <a href> resolve (HEAD request, internal
                               and same-origin external)
    hasElement: <selector>   — selector present in DOM
    elementVisible: <sel>    — selector present AND visible
    elementText:
        selector: <sel>
        equals | contains | matches: <value>
    axe:
        impact: [critical, serious]   (subset of axe-core severities)
    visualDiff:
        threshold: 0.02
        baseline: "first-run" | path
        ignoreRegions: [[x,y,w,h], ...]
    securityHeaders:
        required: [content-security-policy, x-content-type-options, referrer-policy]
        requireHsts: auto | true | false
    cookieSecurity:
        requireHttpOnly: true
        requireSameSite: true
        requireSecure: auto | true | false
    noMixedContent
    noSensitiveUrlParams
    llmJudge:  (handled by llm_judge.py, stub here)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse


SEVERITY_ORDER = {"info": 0, "minor": 1, "major": 2, "critical": 3}


@dataclass
class CheckResult:
    name: str
    ok: bool
    severity: str = "major"   # info | minor | major | critical
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunContext:
    """Data accumulated during a single combination run.

    Populated by runner.py; passed to each check.
    """
    combination_id: str
    bindings: dict[str, Any]
    url: str
    console_errors: list[dict[str, Any]] = field(default_factory=list)
    console_warnings: list[dict[str, Any]] = field(default_factory=list)
    js_errors: list[dict[str, Any]] = field(default_factory=list)
    network_failures: list[dict[str, Any]] = field(default_factory=list)
    broken_links: list[dict[str, Any]] = field(default_factory=list)
    responses: list[dict[str, Any]] = field(default_factory=list)
    screenshot_path: str | None = None
    axe_violations: list[dict[str, Any]] = field(default_factory=list)
    element_state: dict[str, dict[str, Any]] = field(default_factory=dict)
    visual_diff: dict[str, Any] | None = None
    llm_judgements: list[dict[str, Any]] = field(default_factory=list)


def normalize(entry: Any) -> tuple[str, dict[str, Any]]:
    """Normalise `assertion` YAML entry to (name, config)."""
    if isinstance(entry, str):
        return entry, {}
    if isinstance(entry, dict):
        if len(entry) != 1:
            raise ValueError(f"assertion dict must have exactly one key: {entry!r}")
        name, cfg = next(iter(entry.items()))
        if cfg is None:
            cfg = {}
        elif not isinstance(cfg, (dict, str, list, bool)):
            cfg = {"value": cfg}
        if isinstance(cfg, (str, list, bool)):
            cfg = {"value": cfg}
        return name, cfg
    raise ValueError(f"invalid assertion entry: {entry!r}")


def run_check(name: str, cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    handler = _HANDLERS.get(name)
    if handler is None:
        return CheckResult(
            name=name, ok=False, severity="major",
            message=f"unknown assertion: {name!r}",
        )
    return handler(cfg, ctx)


# ----- handlers ---------------------------------------------------------------

def _no_console_errors(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    errs = ctx.console_errors + ctx.js_errors
    if not errs:
        return CheckResult("noConsoleErrors", True, "info", "no console errors")
    return CheckResult(
        "noConsoleErrors", False, "critical",
        f"{len(errs)} console/JS error(s)",
        {"samples": errs[:5]},
    )


def _no_console_warnings(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    if not ctx.console_warnings:
        return CheckResult("noConsoleWarnings", True, "info", "no warnings")
    return CheckResult(
        "noConsoleWarnings", False, "minor",
        f"{len(ctx.console_warnings)} warning(s)",
        {"samples": ctx.console_warnings[:5]},
    )


def _no_network_errors(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    if not ctx.network_failures:
        return CheckResult("noNetworkErrors", True, "info", "no network failures")
    return CheckResult(
        "noNetworkErrors", False, "major",
        f"{len(ctx.network_failures)} failing request(s)",
        {"samples": ctx.network_failures[:5]},
    )


def _no_broken_links(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    if not ctx.broken_links:
        return CheckResult("noBrokenLinks", True, "info", "no broken links")
    return CheckResult(
        "noBrokenLinks", False, "major",
        f"{len(ctx.broken_links)} broken link(s)",
        {"samples": ctx.broken_links[:10]},
    )


def _has_element(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    sel = cfg.get("value") or cfg.get("selector")
    if not sel:
        return CheckResult("hasElement", False, "major", "selector missing")
    state = ctx.element_state.get(sel, {})
    if state.get("exists"):
        return CheckResult("hasElement", True, "info", f"found: {sel}")
    return CheckResult(
        "hasElement", False, "major", f"selector not found: {sel}",
    )


def _element_visible(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    sel = cfg.get("value") or cfg.get("selector")
    if not sel:
        return CheckResult("elementVisible", False, "major", "selector missing")
    state = ctx.element_state.get(sel, {})
    if state.get("visible"):
        return CheckResult("elementVisible", True, "info", f"visible: {sel}")
    return CheckResult(
        "elementVisible", False, "major",
        f"selector not visible: {sel}",
        {"state": state},
    )


def _element_text(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    sel = cfg.get("selector")
    if not sel:
        return CheckResult("elementText", False, "major", "selector missing")
    state = ctx.element_state.get(sel, {})
    if not state.get("exists"):
        return CheckResult("elementText", False, "major", f"selector not found: {sel}")
    text = state.get("text", "")
    if "equals" in cfg and text == cfg["equals"]:
        return CheckResult("elementText", True, "info", "text equals")
    if "contains" in cfg and str(cfg["contains"]) in text:
        return CheckResult("elementText", True, "info", "text contains")
    if "matches" in cfg and re.search(cfg["matches"], text):
        return CheckResult("elementText", True, "info", "text matches")
    return CheckResult(
        "elementText", False, "major",
        f"text mismatch on {sel!r}",
        {"expected": cfg, "got": text},
    )


def _axe(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    impact_filter = set(cfg.get("impact") or ["critical", "serious"])
    filtered = [v for v in ctx.axe_violations if v.get("impact") in impact_filter]
    if not filtered:
        return CheckResult("axe", True, "info", "no a11y violations at selected impact")
    return CheckResult(
        "axe", False, "major",
        f"{len(filtered)} a11y violation(s)",
        {"samples": filtered[:10]},
    )


def _visual_diff(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    diff = ctx.visual_diff or {}
    if diff.get("baseline") == "created":
        return CheckResult("visualDiff", True, "info", "baseline created")
    threshold = float(cfg.get("threshold", 0.02))
    ratio = diff.get("ratio")
    if ratio is None:
        return CheckResult(
            "visualDiff", False, "minor",
            "no visual diff computed",
        )
    if ratio <= threshold:
        return CheckResult(
            "visualDiff", True, "info",
            f"visual diff {ratio:.4f} ≤ {threshold}",
            diff,
        )
    return CheckResult(
        "visualDiff", False, "major",
        f"visual diff {ratio:.4f} > threshold {threshold}",
        diff,
    )


def _llm_judge(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    # Populated by llm_judge.run_llm_judge and stored on ctx.llm_judgements.
    label = cfg.get("label") or cfg.get("prompt", "")[:40] or "llm"
    matches = [j for j in ctx.llm_judgements if j.get("label", "") == label]
    if not matches:
        return CheckResult(
            "llmJudge", False, "minor",
            f"no LLM judgement recorded for {label!r}",
        )
    j = matches[-1]
    if j.get("skipped"):
        return CheckResult(
            "llmJudge", True, "info",
            f"LLM judge skipped: {j.get('reason', '')}",
            j,
        )
    if j.get("ok"):
        return CheckResult(
            "llmJudge", True, "info",
            j.get("summary", "LLM pass"),
            j,
        )
    return CheckResult(
        "llmJudge", False, j.get("severity", "major"),
        j.get("summary", "LLM flagged an issue"),
        j,
    )


def _security_headers(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    resp = _primary_document_response(ctx)
    if not resp:
        return CheckResult(
            "securityHeaders", True, "info",
            "no document response headers observed; skipped",
        )

    headers = {str(k).lower(): str(v) for k, v in (resp.get("headers") or {}).items()}
    required = [str(h).lower() for h in cfg.get("required", [
        "content-security-policy",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
    ])]
    missing = [h for h in required if not headers.get(h)]

    frame_ok = bool(headers.get("x-frame-options"))
    csp = headers.get("content-security-policy", "")
    if "frame-ancestors" in csp.lower():
        frame_ok = True
    if cfg.get("requireFrameProtection", True) and not frame_ok:
        missing.append("x-frame-options or csp frame-ancestors")

    require_hsts = cfg.get("requireHsts", "auto")
    if require_hsts == "auto":
        parsed = urlparse(resp.get("url") or ctx.url)
        host = (parsed.hostname or "").lower()
        require_hsts = parsed.scheme == "https" and host not in {"localhost", "127.0.0.1", "::1"}
    if require_hsts and not headers.get("strict-transport-security"):
        missing.append("strict-transport-security")

    if not missing:
        return CheckResult(
            "securityHeaders", True, "info",
            "baseline security headers present",
            {"checked_url": resp.get("url"), "headers": _selected_headers(headers)},
        )
    return CheckResult(
        "securityHeaders", False, cfg.get("severity", "major"),
        "missing security header(s): " + ", ".join(missing),
        {"checked_url": resp.get("url"), "missing": missing, "headers": _selected_headers(headers)},
    )


def _cookie_security(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    parsed_target = urlparse(ctx.url)
    target_https = parsed_target.scheme == "https"
    require_secure = cfg.get("requireSecure", "auto")
    if require_secure == "auto":
        require_secure = target_https
    require_http_only = bool(cfg.get("requireHttpOnly", True))
    require_same_site = bool(cfg.get("requireSameSite", True))

    findings: list[dict[str, Any]] = []
    observed = 0
    for resp in ctx.responses:
        if not is_same_origin(resp.get("url", ""), ctx.url):
            continue
        set_cookie = (resp.get("headers") or {}).get("set-cookie")
        for cookie in _split_set_cookie(set_cookie):
            observed += 1
            attrs = _cookie_attrs(cookie)
            missing = []
            if require_secure and "secure" not in attrs:
                missing.append("Secure")
            if require_http_only and "httponly" not in attrs:
                missing.append("HttpOnly")
            if require_same_site and "samesite" not in attrs:
                missing.append("SameSite")
            if missing:
                findings.append({
                    "url": resp.get("url"),
                    "missing": missing,
                    "cookie": _redact_cookie(cookie),
                })

    if not observed:
        return CheckResult("cookieSecurity", True, "info", "no Set-Cookie headers observed")
    if not findings:
        return CheckResult("cookieSecurity", True, "info", f"{observed} cookie(s) meet policy")
    return CheckResult(
        "cookieSecurity", False, cfg.get("severity", "major"),
        f"{len(findings)} cookie(s) missing security attribute(s)",
        {"samples": findings[:10], "observed": observed},
    )


def _no_mixed_content(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    if urlparse(ctx.url).scheme != "https":
        return CheckResult("noMixedContent", True, "info", "target is not HTTPS; skipped")
    insecure = [
        r for r in ctx.responses
        if urlparse(r.get("url", "")).scheme == "http"
    ]
    if not insecure:
        return CheckResult("noMixedContent", True, "info", "no HTTP subresources observed")
    return CheckResult(
        "noMixedContent", False, cfg.get("severity", "major"),
        f"{len(insecure)} insecure HTTP resource(s) loaded by HTTPS page",
        {"samples": insecure[:10]},
    )


def _no_sensitive_url_params(cfg: dict[str, Any], ctx: RunContext) -> CheckResult:
    patterns = cfg.get("patterns") or [
        "access_token", "refresh_token", "id_token", "api_key", "apikey",
        "secret", "password", "passwd", "session", "jwt",
    ]
    regex = re.compile(r"(?i)(^|[?&])(" + "|".join(re.escape(p) for p in patterns) + r")=")
    leaks = []
    seen = set()
    for resp in ctx.responses:
        url = resp.get("url", "")
        if url in seen:
            continue
        seen.add(url)
        if regex.search(url):
            leaks.append(_redact_url(url, patterns))
    if not leaks:
        return CheckResult("noSensitiveUrlParams", True, "info", "no sensitive URL parameters observed")
    return CheckResult(
        "noSensitiveUrlParams", False, cfg.get("severity", "major"),
        f"{len(leaks)} URL(s) contain sensitive-looking query parameter names",
        {"samples": leaks[:10]},
    )


_HANDLERS = {
    "noConsoleErrors": _no_console_errors,
    "noConsoleWarnings": _no_console_warnings,
    "noNetworkErrors": _no_network_errors,
    "noBrokenLinks": _no_broken_links,
    "hasElement": _has_element,
    "elementVisible": _element_visible,
    "elementText": _element_text,
    "axe": _axe,
    "visualDiff": _visual_diff,
    "securityHeaders": _security_headers,
    "cookieSecurity": _cookie_security,
    "noMixedContent": _no_mixed_content,
    "noSensitiveUrlParams": _no_sensitive_url_params,
    "llmJudge": _llm_judge,
}


def _primary_document_response(ctx: RunContext) -> dict[str, Any] | None:
    same_origin_docs = [
        r for r in ctx.responses
        if r.get("resource_type") == "document" and is_same_origin(r.get("url", ""), ctx.url)
    ]
    if same_origin_docs:
        return same_origin_docs[0]
    docs = [r for r in ctx.responses if r.get("resource_type") == "document"]
    return docs[0] if docs else None


def _selected_headers(headers: dict[str, str]) -> dict[str, str]:
    names = [
        "content-security-policy",
        "strict-transport-security",
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "permissions-policy",
    ]
    return {name: headers.get(name, "") for name in names if name in headers}


def _split_set_cookie(value: str | None) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    # Playwright usually exposes a single header string. Avoid comma splitting
    # because Expires attributes contain commas; newline splitting is safe when
    # a transport preserves multiple Set-Cookie values that way.
    return [part.strip() for part in str(value).splitlines() if part.strip()]


def _redact_cookie(cookie: str) -> str:
    return re.sub(r"^([^=;]{1,80})=[^;]*", r"\1=<redacted>", cookie)


def _cookie_attrs(cookie: str) -> set[str]:
    parts = [p.strip() for p in cookie.split(";")]
    attrs = set()
    for part in parts[1:]:
        if not part:
            continue
        attrs.add(part.split("=", 1)[0].lower())
    return attrs


def _redact_url(url: str, keys: list[str]) -> str:
    redacted = url
    for key in keys:
        redacted = re.sub(
            rf"(?i)([?&]{re.escape(key)}=)[^&#]*",
            rf"\1<redacted>",
            redacted,
        )
    return redacted


# ----- link extraction helpers -----------------------------------------------

def classify_link(href: str, base: str) -> str | None:
    """Return an absolute URL to probe, or None for non-probe links.

    Non-probe: mailto:, tel:, javascript:, #anchor, empty, data:.
    Probe: http(s):, file:, and relative paths.
    """
    if not href:
        return None
    s = href.strip()
    if not s or s.startswith("#"):
        return None
    lower = s.lower()
    for bad in ("mailto:", "tel:", "javascript:", "data:", "sms:"):
        if lower.startswith(bad):
            return None
    return urljoin(base, s)


def is_same_origin(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return (pa.scheme, pa.netloc) == (pb.scheme, pb.netloc)
