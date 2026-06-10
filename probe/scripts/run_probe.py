"""Probe CLI orchestrator.

Usage:
    python run_probe.py <plan.yml>
    python run_probe.py --explore <url> [--out plan.yml]
    python run_probe.py <plan.yml> --parallel 4 --strategy full --no-llm --no-headless

Exit codes:
    0 — all pass
    1 — failures found
    2 — plan/config error
    3 — runner crash
"""
from __future__ import annotations

import argparse
import contextlib
import sys

# Force UTF-8 stdout on Windows so '—', '·', emoji, Korean etc. don't crash
# under legacy cp949 consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import functools
import http.server
import json
import os
import socket
import socketserver
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from checks import CheckResult, RunContext, normalize, run_check  # noqa: E402
from combinator import explode_combinations, generate  # noqa: E402
from llm_judge import run_llm_judge  # noqa: E402
from plan import Plan, load_plan, resolve_vars  # noqa: E402
from report import write_report  # noqa: E402
from runner import exercise  # noqa: E402

SKILL_ROOT = HERE.parent
TEMPLATE_DIR = SKILL_ROOT / "templates"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser("probe", description="Exploratory QA agent")
    ap.add_argument("plan", nargs="?", help="Path to probe-plan YAML")
    ap.add_argument("--explore", metavar="URL", help="Auto-generate a plan from URL")
    ap.add_argument("--out", help="Output path for --explore generated plan")
    ap.add_argument("--parallel", type=int, help="Override plan.parallel")
    ap.add_argument("--strategy", help="Override plan.strategy (pairwise|full|random:N)")
    ap.add_argument("--no-llm", action="store_true", help="Skip LLM judge assertions")
    ap.add_argument("--no-headless", action="store_true", help="Show browser windows")
    ap.add_argument("--output-dir", help="Override run output directory")
    ap.add_argument("--agentic", metavar="GOAL",
                    help="Free-form goal text. Runs an LLM-driven agent that drives the "
                         "browser via Codex CLI, instead of the declarative combinator flow.")
    ap.add_argument("--agentic-max-steps", type=int, default=25,
                    help="Max actions the agent may take (default: 25)")
    ap.add_argument("--target", help="Target URL (required with --agentic unless a plan is also given)")
    ap.add_argument("--cookies-file", metavar="PATH",
                    help="JSON file with Playwright-format cookies (array of "
                         "{name, value, domain, path, ...}). Seeded before navigation.")
    ap.add_argument("--local-storage-file", metavar="PATH",
                    help="JSON file with {\"key\": \"value\", ...}. Seeded for the "
                         "target origin via an init_script before navigation.")
    ap.add_argument("--crawl", action="store_true",
                    help="Service review mode: BFS-crawl same-origin links from --target, "
                         "run the agent on each page, aggregate findings into a single report.")
    ap.add_argument("--crawl-max-pages", type=int, default=10,
                    help="Max pages the crawler will visit (default: 10)")
    ap.add_argument("--crawl-per-page-steps", type=int, default=6,
                    help="Max agent steps per page (default: 6)")
    args = ap.parse_args(argv)

    if args.explore:
        return _do_explore(args)

    if args.crawl:
        return _do_crawl(args)

    if args.agentic:
        return _do_agentic(args)

    if not args.plan:
        ap.print_help()
        return 2

    try:
        plan = load_plan(args.plan)
    except Exception as e:
        print(f"[probe] plan load error: {e}", file=sys.stderr)
        return 2

    if args.parallel is not None:
        plan.parallel = args.parallel
    if args.strategy is not None:
        plan.strategy = args.strategy

    try:
        with _maybe_local_server(plan) as plan2:
            return _run(plan2, include_llm=not args.no_llm, headless=not args.no_headless,
                        output_dir_override=args.output_dir)
    except Exception:
        traceback.print_exc()
        return 3


_PAGE_TYPE_JS = r"""
() => {
  const has = sel => !!document.querySelector(sel);
  const count = sel => document.querySelectorAll(sel).length;
  return {
    has_form:     has('form') || count('input:not([type=hidden])') > 0,
    form_fields:  count('form input:not([type=hidden]), form textarea, form select'),
    has_table:    has('table') || count('[role=table]') > 0,
    has_nav:      has('nav') || has('[role=navigation]'),
    has_modal:    has('[role=dialog]') || has('.modal, [class*=modal]'),
    has_card:     count('.card, [class*=card]') >= 3,
    has_chart:    has('canvas') || has('svg'),
    h1_text:      (document.querySelector('h1') || {}).innerText || '',
    title:        document.title || '',
  };
}
"""


def _checklist_for_page(page_type: dict[str, Any]) -> str:
    """Turn page-type heuristics into an agent goal snippet so the probe
    actually tries the *right* stuff on each route."""
    lines = []
    if page_type.get("has_form"):
        lines.append(
            "폼이 보이면: (a) 빈 값으로 제출 버튼을 눌러 검증 에러가 뜨는지 확인, "
            "(b) 눈에 띄는 입력 필드에 긴 문자열(200자 이상)이나 특수문자를 넣어보기."
        )
    if page_type.get("has_modal"):
        lines.append("모달이나 다이얼로그가 보이면 열었다가 Esc 또는 닫기 버튼으로 닫아보기.")
    if page_type.get("has_table"):
        lines.append("테이블이 있으면 정렬/페이지네이션/행 클릭 중 한 가지를 시도.")
    if not lines:
        lines.append("페이지가 정상 렌더되는지 눈으로 확인하고 주요 CTA 한 번만 클릭해보기.")
    return "\n".join(f"  - {l}" for l in lines)


def _do_crawl(args) -> int:
    """Service-review mode: BFS-crawl same-origin pages and run agent per page."""
    from agent import Agent, write_journal, Finding
    from crawler import Crawler, extract_same_origin_links

    target = args.target
    if not target:
        print("[probe] --crawl requires --target <url>", file=sys.stderr)
        return 2

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_out = Path(args.output_dir) if args.output_dir else Path.cwd() / "probe-runs"
    run_dir = (base_out / ts / "crawl").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    # Auth seed
    cookies = []
    local_storage_items = {}
    if args.cookies_file:
        try:
            cookies = json.loads(Path(args.cookies_file).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[probe] cookies-file error: {e}", file=sys.stderr); return 2
    if args.local_storage_file:
        try:
            local_storage_items = json.loads(Path(args.local_storage_file).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[probe] local-storage-file error: {e}", file=sys.stderr); return 2

    crawler = Crawler(target, max_pages=args.crawl_max_pages)
    aggregate_findings: list[Finding] = []
    per_page_runs: list[dict[str, Any]] = []
    har_path = run_dir / "network.har"
    trace_path = run_dir / "trace.zip"

    print(f"[probe] service-review (crawl) mode")
    print(f"[probe] seed: {target}")
    print(f"[probe] max pages: {args.crawl_max_pages}, per-page steps: {args.crawl_per_page_steps}")
    print(f"[probe] output: {run_dir}")

    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not args.no_headless)
            try:
                context = browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    record_har_path=str(har_path),
                    record_har_content="omit",
                )
                try:
                    context.tracing.start(screenshots=True, snapshots=True, sources=False)
                except Exception:
                    pass
                if cookies:
                    try:
                        context.add_cookies(cookies)
                    except Exception as e:
                        print(f"[probe] cookie seed warning: {e}", file=sys.stderr)
                page = context.new_page()
                try:
                    from runner import _OBS_GUARD
                    page.add_init_script(_OBS_GUARD)
                except Exception:
                    pass
                if local_storage_items:
                    ls_script = "try {\n" + "\n".join(
                        f"  window.localStorage.setItem({json.dumps(k)}, {json.dumps(v)});"
                        for k, v in local_storage_items.items()
                    ) + "\n} catch (e) {}"
                    page.add_init_script(ls_script)

                page_n = 0
                while True:
                    url = crawler.next_url()
                    if not url:
                        break
                    page_n += 1
                    page_out = run_dir / f"page-{page_n:02d}"
                    page_out.mkdir(parents=True, exist_ok=True)

                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=15000)
                        try:
                            page.wait_for_load_state("networkidle", timeout=5000)
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"[probe] {page_n}. {url}  NAV_FAILED: {e}")
                        continue

                    # Harvest new links before agent starts interacting
                    new_links = extract_same_origin_links(page, target)
                    added = crawler.record_visit(url, new_links)

                    # Detect page type → generate a per-page checklist
                    try:
                        page_type = page.evaluate(_PAGE_TYPE_JS) or {}
                    except Exception:
                        page_type = {}
                    checklist = _checklist_for_page(page_type)
                    goal = (
                        f"이 페이지({url})를 사용자처럼 확인하세요.\n"
                        f"체크리스트:\n{checklist}\n"
                        "시나리오를 마쳤으면 한국어 한두 문장 요약으로 done."
                    )

                    agent = Agent(
                        page=page, goal=goal, out_dir=page_out,
                        max_steps=args.crawl_per_page_steps,
                    )
                    run = agent.loop()
                    write_journal(run, page_out)
                    aggregate_findings.extend(run.findings)
                    per_page_runs.append({
                        "page_n": page_n,
                        "url": url,
                        "verdict": run.verdict,
                        "steps": len(run.steps),
                        "findings": len(run.findings),
                        "agent_claimed": run.agent_claimed_success,
                        "summary": run.final_summary,
                        "page_type": page_type,
                        "new_links_added": added,
                    })
                    sign = {"pass": "✅", "warn": "🟡", "fail": "🔴"}.get(run.verdict, "?")
                    print(f"[probe] {page_n:2d}. {sign} {url}  "
                          f"({len(run.findings)} findings, +{added} links)")
            finally:
                try: context.tracing.stop(path=str(trace_path))
                except Exception: pass
                try: context.close()
                except Exception: pass
                try: browser.close()
                except Exception: pass
    except Exception:
        traceback.print_exc()
        return 3

    # Aggregate report + coverage
    coverage = {
        "seed": target,
        "visited_count": len(crawler.visited),
        "visited": sorted(crawler.visited),
        "discovered": crawler.discovered,
        "remaining_unvisited": crawler.remaining,
        "budget": args.crawl_max_pages,
    }
    (run_dir / "coverage.json").write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    # Dedupe findings across pages by fingerprint, keep first occurrence
    seen_fp: set[str] = set()
    unique_findings = []
    for f in aggregate_findings:
        if f.fingerprint in seen_fp:
            continue
        seen_fp.add(f.fingerprint)
        unique_findings.append(f)

    # Regression tagging — persists fingerprints across runs, tags each
    # finding as new/recurrence, and closes previously-open items no longer
    # observed.
    regression_summary = None
    try:
        from regression_db import tag_and_persist
        regression_summary = tag_and_persist(target, unique_findings)
    except Exception as e:
        print(f"[probe] regression DB warning: {e}", file=sys.stderr)

    critical = sum(1 for f in unique_findings if f.severity == "critical")
    major = sum(1 for f in unique_findings if f.severity == "major")
    minor = sum(1 for f in unique_findings if f.severity == "minor")
    if critical or major:
        verdict = "fail"
    elif minor:
        verdict = "warn"
    else:
        verdict = "pass"

    report_md = _render_crawl_report(
        target=target, verdict=verdict, pages=per_page_runs,
        findings=unique_findings, coverage=coverage,
        trace_path=trace_path, har_path=har_path,
        regression=regression_summary,
    )
    (run_dir / "report.md").write_text(report_md, encoding="utf-8")

    print("")
    sign = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[verdict]
    print(f"[probe] service-review verdict: {sign}")
    print(f"[probe] pages visited: {len(crawler.visited)} / discovered {crawler.discovered}")
    print(f"[probe] unique findings: {critical} critical / {major} major / {minor} minor")
    print(f"[probe] report: {run_dir / 'report.md'}")
    print(f"[probe] coverage: {run_dir / 'coverage.json'}")
    if trace_path.exists():
        print(f"[probe] trace: {trace_path}")
    return 0 if verdict == "pass" else 1


def _render_crawl_report(*, target, verdict, pages, findings, coverage,
                          trace_path, har_path, regression=None) -> str:
    icon = {"pass": "✅", "warn": "🟡", "fail": "🔴"}[verdict]
    crit = [f for f in findings if f.severity == "critical"]
    maj = [f for f in findings if f.severity == "major"]
    mnr = [f for f in findings if f.severity == "minor"]
    lines = [
        f"# Service review — {target}",
        "",
        f"**Verdict**: {icon} **{verdict.upper()}** (ground truth: automated evidence)",
        "",
        f"- Pages visited: **{coverage['visited_count']}** of {coverage['budget']} budget  "
        f"(discovered {coverage['discovered']}, unvisited {coverage['remaining_unvisited']})",
        f"- Unique findings: **{len(crit)} critical / {len(maj)} major / {len(mnr)} minor**",
        f"- Trace: `{trace_path}` — replay with `npx playwright show-trace <path>`",
        f"- Network HAR: `{har_path}`",
        "",
        "## Findings (deduped by fingerprint)",
        "",
    ]
    for sev, icon2, group in (("critical", "🔴", crit), ("major", "🟠", maj), ("minor", "🟡", mnr)):
        if not group:
            continue
        lines.append(f"### {icon2} {sev} ({len(group)})")
        lines.append("")
        for f in group:
            lines.append(f"- **[{f.kind}]** `{f.url}` — {f.message}  `({f.fingerprint})`")
        lines.append("")
    if not findings:
        lines.append("✅ No console / network / a11y issues observed.")
        lines.append("")

    lines.append("## Pages")
    lines.append("")
    lines.append("| # | Verdict | URL | Steps | Findings | Agent said | Summary |")
    lines.append("|---|---|---|---|---|---|---|")
    for pr in pages:
        psign = {"pass": "✅ pass", "warn": "🟡 warn", "fail": "🔴 fail"}.get(pr["verdict"], "?")
        agent_said = "success" if pr["agent_claimed"] else "not success"
        summary = (pr.get("summary") or "").replace("|", "\\|")[:80]
        lines.append(f"| {pr['page_n']} | {psign} | `{pr['url']}` | {pr['steps']} | "
                     f"{pr['findings']} | {agent_said} | {summary} |")
    lines.append("")

    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- Seed: {coverage['seed']}")
    lines.append(f"- Visited: {coverage['visited_count']} / Discovered: {coverage['discovered']}")
    if coverage["remaining_unvisited"]:
        lines.append(f"- ⚠ Unvisited at end: **{coverage['remaining_unvisited']}**  "
                     f"(raise --crawl-max-pages to cover more)")
    lines.append("")

    if regression:
        lines.append("## Regression history")
        lines.append("")
        lines.append(
            f"- **{regression['new']}** new finding(s)  ·  "
            f"**{regression['recurrence']}** recurrence(s)  ·  "
            f"**{regression['closed_this_run']}** closed this run"
        )
        lines.append(f"- DB: `{regression['db_path']}`")
        if regression.get("closed_items"):
            lines.append("")
            lines.append("### ✅ Closed (previously seen, not found this run)")
            for c in regression["closed_items"]:
                lines.append(f"- `{c['kind']}` on `{c['route']}` — {c['message'][:120]}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _do_agentic(args) -> int:
    """Run the agentic browser-use-style loop with a free-form goal."""
    from agent import Agent, write_journal

    # Resolve target
    target = args.target
    plan: Plan | None = None
    if args.plan:
        try:
            plan = load_plan(args.plan)
            target = target or plan.target
        except Exception as e:
            print(f"[probe] plan load error: {e}", file=sys.stderr)
            return 2
    if not target:
        print("[probe] --agentic requires --target <url> or a plan with target", file=sys.stderr)
        return 2

    # Build a minimal ephemeral plan just so _maybe_local_server can do its job
    if plan is None:
        plan = Plan(target=target, name="agentic")
    else:
        plan.target = target

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_out = Path(args.output_dir) if args.output_dir else (plan.plan_dir / "probe-runs")
    run_dir = (base_out / ts / "agent").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[probe] agentic mode")
    print(f"[probe] goal: {args.agentic}")
    print(f"[probe] target: {plan.target}")
    print(f"[probe] max steps: {args.agentic_max_steps}")
    print(f"[probe] output: {run_dir}")

    # Load auth seed data (if provided)
    cookies: list[dict[str, Any]] = []
    local_storage_items: dict[str, str] = {}
    if args.cookies_file:
        try:
            cookies = json.loads(Path(args.cookies_file).read_text(encoding="utf-8"))
            if not isinstance(cookies, list):
                raise ValueError("cookies file must be a JSON array")
            print(f"[probe] loaded {len(cookies)} cookie(s) from {args.cookies_file}")
        except Exception as e:
            print(f"[probe] cookies-file error: {e}", file=sys.stderr)
            return 2
    if args.local_storage_file:
        try:
            local_storage_items = json.loads(Path(args.local_storage_file).read_text(encoding="utf-8"))
            if not isinstance(local_storage_items, dict):
                raise ValueError("local-storage file must be a JSON object")
            print(f"[probe] loaded {len(local_storage_items)} localStorage key(s) from {args.local_storage_file}")
        except Exception as e:
            print(f"[probe] local-storage-file error: {e}", file=sys.stderr)
            return 2

    har_path = run_dir / "network.har"
    trace_path = run_dir / "trace.zip"

    try:
        with _maybe_local_server(plan) as plan2:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=not args.no_headless)
                try:
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 900},
                        record_har_path=str(har_path),
                        record_har_content="omit",
                    )
                    # Full-session trace: DOM snapshots + screenshots on every
                    # action, so a failed run can be replayed in Playwright's
                    # Trace Viewer (`npx playwright show-trace trace.zip`).
                    try:
                        context.tracing.start(
                            screenshots=True, snapshots=True, sources=False,
                        )
                    except Exception as e:
                        print(f"[probe] tracing start warning: {e}", file=sys.stderr)
                    if cookies:
                        try:
                            context.add_cookies(cookies)
                        except Exception as e:
                            print(f"[probe] cookie seed warning: {e}", file=sys.stderr)

                    page = context.new_page()
                    # Observer guard — same defensive patch the declarative runner uses
                    try:
                        from runner import _OBS_GUARD  # reuse the same JS blob
                        page.add_init_script(_OBS_GUARD)
                    except Exception:
                        pass
                    if local_storage_items:
                        ls_script = "try {\n" + "\n".join(
                            f"  window.localStorage.setItem({json.dumps(k)}, {json.dumps(v)});"
                            for k, v in local_storage_items.items()
                        ) + "\n} catch (e) {}"
                        page.add_init_script(ls_script)

                    page.goto(plan2.target, wait_until="domcontentloaded", timeout=15000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass

                    agent = Agent(
                        page=page, goal=args.agentic, out_dir=run_dir,
                        max_steps=args.agentic_max_steps,
                    )
                    run = agent.loop()
                finally:
                    # Stop tracing + close context so HAR is flushed
                    try:
                        context.tracing.stop(path=str(trace_path))
                    except Exception:
                        pass
                    try:
                        context.close()
                    except Exception:
                        pass
                    try:
                        browser.close()
                    except Exception:
                        pass
    except Exception:
        traceback.print_exc()
        return 3

    journal = write_journal(run, run_dir)
    verdict_icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}.get(run.verdict, "UNKNOWN")
    critical = sum(1 for f in run.findings if f.severity == "critical")
    major = sum(1 for f in run.findings if f.severity == "major")
    minor = sum(1 for f in run.findings if f.severity == "minor")
    print("")
    print(f"[probe] verdict: {verdict_icon}  ({run.stopped_reason})")
    print(f"[probe] findings: {critical} critical / {major} major / {minor} minor")
    print(f"[probe] agent claimed: {'success' if run.agent_claimed_success else 'not success'}")
    print(f"[probe] steps: {len(run.steps)}")
    print(f"[probe] journal: {journal}")
    if trace_path.exists():
        print(f"[probe] trace:   {trace_path}  (view: npx playwright show-trace {trace_path})")
    if har_path.exists():
        print(f"[probe] har:     {har_path}")
    return 0 if run.verdict == "pass" else 1


def _do_explore(args) -> int:
    from explorer import explore as do_explore

    out = Path(args.out or "./probe-plan.auto.yml").resolve()
    print(f"[probe] exploring {args.explore} → {out}")
    try:
        findings = do_explore(args.explore, out, headless=True)
    except Exception:
        traceback.print_exc()
        return 3
    print(f"[probe] wrote plan skeleton: {out}")
    print(f"[probe] discovered {len(findings.get('controls', []))} interactive elements, "
          f"{len(findings.get('candidate_dimensions', {}))} candidate dimensions")
    print("[probe] review and curate the plan, then run:  python run_probe.py " + str(out))
    return 0


@contextlib.contextmanager
def _maybe_local_server(plan: Plan):
    """If plan.target is file://, start a local http.server on a random port
    rooted at the file's directory, and rewrite the target to http://.

    Yields the plan (possibly with rewritten target).
    """
    url = plan.target
    if not url.startswith("file://"):
        yield plan
        return

    parsed = urlparse(url)
    # Turn file://C:/Users/... into C:/Users/...
    raw_path = unquote(parsed.path)
    if raw_path.startswith("/") and len(raw_path) >= 3 and raw_path[2] == ":":
        raw_path = raw_path[1:]  # strip leading slash on Windows
    file_path = Path(raw_path)
    if not file_path.exists():
        print(f"[probe] warning: file target not found ({file_path}); serving anyway")
    serve_dir = file_path.parent

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(serve_dir), **kw)

        def log_message(self, *a, **kw):
            return

    server = socketserver.ThreadingTCPServer(("127.0.0.1", port), _Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    new_url = f"http://127.0.0.1:{port}/{file_path.name}"
    print(f"[probe] auto-serving {serve_dir} at {new_url}")
    original = plan.target
    plan.target = new_url
    try:
        yield plan
    finally:
        plan.target = original
        try:
            server.shutdown()
            server.server_close()
        except Exception:
            pass


def _run(plan: Plan, *, include_llm: bool, headless: bool,
         output_dir_override: str | None) -> int:
    # Output directory
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_out = Path(output_dir_override) if output_dir_override else (
        Path(plan.output_dir) if plan.output_dir else plan.plan_dir / "probe-runs"
    )
    run_dir = (base_out / ts).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    combos_dir = run_dir / "combinations"
    baselines_dir = (plan.plan_dir / "probe-runs" / "baselines") if plan.plan_dir else run_dir / "baselines"
    baselines_dir.mkdir(parents=True, exist_ok=True)

    base_combos = generate(plan.dimensions, plan.strategy)
    combos = explode_combinations(base_combos, plan.viewports, plan.browsers)
    if not combos:
        print("[probe] no combinations generated — empty dimensions?", file=sys.stderr)
        return 2

    print(f"[probe] {plan.name}")
    print(f"[probe] target: {plan.target}")
    print(f"[probe] strategy={plan.strategy} combos={len(combos)} parallel={plan.parallel}")
    print(f"[probe] output: {run_dir}")

    # Write resolved plan snapshot
    (run_dir / "plan.resolved.yml").write_text(
        yaml.safe_dump(plan.raw, sort_keys=False, allow_unicode=True), encoding="utf-8",
    )

    def _work(idx_combo):
        idx, bindings = idx_combo
        cid = f"c{idx + 1:03d}"
        combo_dir = combos_dir / cid
        exercise_result = exercise(
            plan, bindings, combo_dir, baselines_dir,
            include_llm=include_llm, headless=headless,
        )
        ctx: RunContext = exercise_result["context"]
        runtime_error = exercise_result.get("error")

        # Optional LLM judgements
        if include_llm and ctx.screenshot_path:
            for entry in plan.assertions:
                name, cfg = normalize(entry)
                if name != "llmJudge":
                    continue
                cfg_resolved = resolve_vars(cfg, bindings)
                judgement = run_llm_judge(cfg_resolved, Path(ctx.screenshot_path), bindings)
                ctx.llm_judgements.append(judgement)

        # Run each assertion
        check_rows: list[dict[str, Any]] = []
        if runtime_error:
            check_rows.append(
                {
                    "name": "runner",
                    "ok": False,
                    "severity": "critical",
                    "message": runtime_error.splitlines()[0] if runtime_error else "runner error",
                    "details": {"trace": runtime_error},
                }
            )
        for entry in plan.assertions:
            name, cfg = normalize(entry)
            cfg = resolve_vars(cfg, bindings)
            try:
                res: CheckResult = run_check(name, cfg, ctx)
            except Exception as e:
                res = CheckResult(name, False, "minor", f"check raised: {e}")
            check_rows.append(asdict(res))

        overall = _overall(check_rows)
        # Persist per-combo result.json
        combo_dir.mkdir(parents=True, exist_ok=True)
        (combo_dir / "result.json").write_text(
            json.dumps(
                {
                    "id": cid,
                    "bindings": bindings,
                    "checks": check_rows,
                    "overall": overall,
                    "runtime_error": runtime_error,
                },
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        return {
            "id": cid,
            "bindings": bindings,
            "checks": check_rows,
            "overall": overall,
            "screenshot": _rel(combo_dir / "screenshot.png", run_dir) if ctx.screenshot_path else None,
            "reproduce": _rel(combo_dir / "reproduce.py", run_dir),
        }

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, plan.parallel)) as pool:
        futures = [pool.submit(_work, (i, c)) for i, c in enumerate(combos)]
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            sign = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[r["overall"]]
            print(f"[probe] {r['id']} {sign}  {_fmt_bindings(r['bindings'])}")

    results.sort(key=lambda r: r["id"])
    report_path = write_report(
        results,
        plan.name,
        plan.target,
        run_dir,
        template_dir=TEMPLATE_DIR,
    )

    s = _summary_counts(results)
    print("")
    print(f"[probe] DONE  total={s['total']}  pass={s['pass']}  warn={s['warn']}  fail={s['fail']}")
    print(f"[probe] report: {report_path}")

    return 1 if s["fail"] > 0 else 0


def _overall(checks: list[dict[str, Any]]) -> str:
    has_fail = any((not c["ok"]) and c["severity"] in {"major", "critical"} for c in checks)
    has_warn = any((not c["ok"]) and c["severity"] == "minor" for c in checks)
    if has_fail:
        return "fail"
    if has_warn:
        return "warn"
    return "pass"


def _summary_counts(results):
    c = {"total": len(results), "pass": 0, "warn": 0, "fail": 0}
    for r in results:
        c[r["overall"]] += 1
    return c


def _fmt_bindings(b: dict[str, Any]) -> str:
    return ", ".join(f"{k}={v}" for k, v in b.items() if not k.startswith("_"))


def _rel(p: Path, base: Path) -> str:
    try:
        return str(p.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(p)


if __name__ == "__main__":
    sys.exit(main())
