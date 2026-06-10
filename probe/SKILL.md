---
name: probe
description: Exploratory QA agent — generates combinatorial state matrices, drives a real browser via Playwright to exercise a web feature across every combination, runs automatic + LLM assertions, and emits a single Markdown report with screenshots and reproduce scripts. Use when the user wants more than unit tests — actual "using the feature from many angles" QA. Triggers: "프로브", "/probe", "조합 검증", "탐색적 QA", "exploratory qa", "probe feature", "combinatorial test".
user-invocable: true
args:
  - name: plan
    description: Path to probe-plan YAML. Omit with --explore to auto-generate a plan from the target URL.
    required: false
  - name: target
    description: Target URL or file path (overrides plan.target when combined with --explore).
    required: false
---

# probe — Exploratory QA Agent

**What it does**: takes a declarative "probe plan" (dimensions + actions + assertions), generates pairwise combinations, drives a real browser via Playwright, captures console/network/DOM/response-header state for each combination, runs layered automatic + LLM assertions, and writes a single Markdown report with screenshots and per-failure reproduce scripts.

## When to invoke

The user wants to:
- verify a web feature works across combinations of inputs/states ("여러 방면에서 기능을 동작해봐")
- find UI bugs that only surface in specific state crosses (theme × viewport × locale, etc.)
- catch regressions after a refactor without writing N explicit tests
- generate a QA report for a release

**Do NOT invoke** for: code-level review (use `/review`), pure static security audit (use `security-router`), full penetration testing or exploit execution (use `pentest-router` with explicit authorization), design critique (use `critique`), or unit test writing.

Invoke Probe for security only when it is acting as a low-side-effect verification gate over a real UI/API surface: security headers, cookie flags, mixed content, sensitive URL parameters, role/state smoke checks, or remediation evidence after a security fix.

## Flow (4 stages)

```
 Plan ─▶ Combinate ─▶ Exercise ─▶ Judge ─▶ Report
  YAML    pairwise     Playwright   auto + LLM   Markdown
```

1. **Plan** — user supplies YAML declaring `target`, `dimensions`, `actions`, `assertions`. Or `--explore` mode: probe auto-analyses the target and proposes a plan.
2. **Combinate** — pairwise by default (N-wise / full / random also available).
3. **Exercise** — Playwright launches a browser per parallel slot, seeds state (localStorage/cookies/viewport), navigates, runs actions, collects logs, screenshots.
4. **Judge** — two layers: (a) automatic checks (console errors, network 4xx/5xx, broken links, element presence, a11y via axe-core, visual diff against baseline); (b) LLM judge via Codex CLI (ChatGPT OAuth, vision input, JSON-schema-constrained output) — optional, flagged per-assertion.
5. **Report** — single Markdown at `<plan-dir>/probe-runs/<timestamp>/report.md` with: summary, matrix, failed-case details (screenshots + console tails + reproduce `.py` script).

## Setup (first run only)

`scripts/run_probe.sh` creates a skill-local `.venv` and installs the Python dependencies automatically if they are missing. Manual setup:

```bash
pip install playwright pyyaml pillow jinja2
playwright install chromium
# optional: firefox webkit
```

For LLM judge, the skill shells out to the **Codex CLI** (ChatGPT OAuth). Install:

```bash
npm install -g @openai/codex
codex login   # one-time browser flow, signs in with your ChatGPT account
```

No API key required; usage counts against the ChatGPT subscription. If the CLI is absent or not logged in, `llmJudge` assertions are silently skipped (treated as pass with `skipped: true`).

## Invocation

```bash
# With an explicit plan
~/.claude/skills/probe/scripts/run_probe.sh <plan.yml>

# Auto-explore a target and generate a plan
~/.claude/skills/probe/scripts/run_probe.sh --explore <url>

# Quick run with overrides
~/.claude/skills/probe/scripts/run_probe.sh <plan.yml> --parallel 4 --strategy full --no-llm
```

Skill invocation (Claude Code):
- `/probe <plan>` — run existing plan
- `/probe --explore <url>` — auto-generate plan, save, run

## Probe plan schema (abbreviated)

```yaml
target: "file:///C:/path/to/app.html"     # or http(s)://
name: "Dashboard Probe"

dimensions:
  theme: [dark, light]
  variant: [A, B, C]
  filter: [all, crypto, stocks]

viewports: [desktop, mobile]               # optional
browsers: [chromium]                       # chromium | firefox | webkit

setup:                                     # runs once per combination
  - setLocalStorage:
      "kr.theme": "${theme}"
      "kr.variant": "${variant}"

actions:                                   # runs per combination
  - reload
  - wait: 300
  - click:
      selector: '.seg button'
      text: "${filter}"
      skipIf: 'variant != "B"'
  - type: { selector: '#journal', text: "probe ${_id}" }

assertions:
  - noConsoleErrors
  - noNetworkErrors
  - noBrokenLinks
  - securityHeaders: { requireHsts: auto }
  - cookieSecurity: { requireSecure: auto, requireHttpOnly: true, requireSameSite: true }
  - noMixedContent
  - noSensitiveUrlParams
  - hasElement: '.card'
  - elementVisible: '.sidebar'
  - axe: { impact: ['critical', 'serious'] }
  - visualDiff: { threshold: 0.02 }
  - llmJudge:
      prompt: "Does this dashboard look coherent and functional?"
      severity: medium

strategy: pairwise                         # pairwise | full | random:N
parallel: 3
outputDir: null                            # default: <plan-dir>/probe-runs/<ts>
```

## How Claude should use this skill

When the user invokes probe:

1. **If they supplied a plan path** — run `run_probe.py <plan>` and relay the report path.
2. **If they supplied a URL only** — run `run_probe.py --explore <url>`, show them the proposed YAML, confirm, then run.
3. **If they describe what to test in natural language** — draft a YAML plan yourself, save to `<project>/probe.yml`, show to user, run after confirmation.
4. **After run** — summarise failures inline (top 3), cite report path, offer next actions (fix highest-severity issue, re-run after fix, expand coverage).

Exit codes: 0 = all pass, 1 = failures found, 2 = plan/config error, 3 = runner crash.

## Integration with other skills

- `release` — probe can gate releases. Invoke via its guard.py.
- `security-router` — finds code/static security issues; probe verifies runtime behavior and remediation evidence.
- `pentest-router` — owns authorized offensive or infrastructure testing; probe consumes/smoke-verifies the resulting safe surface.
- `audit` — audit finds static issues; probe finds dynamic/interaction issues. Run both.
- `autonomous-dev` — in S-Phase QA, probe covers feature-level exploratory testing.

## Cybersecurity skill absorption

Probe includes a distilled index of `mukul975/Anthropic-Cybersecurity-Skills` at `references/cybersecurity-skills-index.json` and the absorption rules in `references/cybersecurity-skill-absorption.md`. Use that index as a routing/reference layer, not as a script launcher. Load at most a few matching skills, extract defensive verification criteria, then translate them into Probe assertions or LLM-judge prompts.

Built-in low-side-effect security assertions:

- `securityHeaders` — checks baseline document response headers: CSP, HSTS when applicable, `X-Content-Type-Options`, frame protection, referrer policy, and permissions policy.
- `cookieSecurity` — checks observed same-origin `Set-Cookie` headers for `Secure`, `HttpOnly`, and `SameSite` policy.
- `noMixedContent` — flags HTTP subresources loaded by HTTPS targets.
- `noSensitiveUrlParams` — flags sensitive-looking tokens or secrets in observed URLs.

Do not auto-run upstream offensive scripts or workflows from Probe. Credential dumping, password cracking, C2 setup, exploit execution, broad scanning, malware detonation, and social-engineering operations require explicit security scope and must route outside Probe.

## Output layout

```
<plan-dir>/probe-runs/<YYYYMMDD-HHMMSS>/
├── report.md                 ← start here
├── plan.resolved.yml         ← plan with ${vars} resolved per combination
├── combinations/
│   ├── c001/
│   │   ├── result.json       ← structured result
│   │   ├── screenshot.png
│   │   ├── console.log
│   │   ├── network.log
│   │   └── reproduce.py      ← standalone Playwright script
│   └── c002/...
└── baselines/                ← visual baselines (first run creates)
```

## Known limits (v1)

- File URLs with CORS-restricted localStorage may behave differently from http:// — prefer a local static server for fidelity.
- LLM judge is opinion, not truth. Use it to *flag* cases, then eyeball screenshots.
- Dynamic content (timestamps, animations) breaks visual diff — use `ignoreRegions` in visualDiff assertion.
- Pairwise hides higher-order interactions. Use `strategy: full` when combination count < 50.
