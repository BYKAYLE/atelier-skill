# CHANGELOG — probe

## 2.1.0 — 2026-05-27 — Cybersecurity absorption release

- Absorbed `mukul975/Anthropic-Cybersecurity-Skills` as a Probe reference layer, not as a raw feature dump. Added a distilled 754-skill metadata index at `references/cybersecurity-skills-index.json` and the integration contract at `references/cybersecurity-skill-absorption.md`.
- Added low-side-effect runtime security assertions:
  - `securityHeaders`
  - `cookieSecurity`
  - `noMixedContent`
  - `noSensitiveUrlParams`
- Playwright response capture now records all response headers so Probe can verify security headers and cookie attributes from actual runtime traffic.
- Added `templates/security-probe-plan.example.yml` as the starter for authorized web security smoke checks.
- Clarified that Probe remains an independent QA/verification gate. Static audit stays with `security-router`; authorized offensive or infrastructure testing stays with `pentest-router`.

## 2.0.0 — 2026-04-21 — Service-review release

The probe is now built around the real use case: "I made a service, probe
should catch the errors a developer would care about." Reorganised the
agent so findings drive the verdict, not the LLM's opinion.

### Phase A: automated evidence over LLM claim
- **Agent now captures console / network / axe automatically** every step —
  regardless of what Codex decides. New `Finding` dataclass with stable
  fingerprints. Listeners attached at agent construction.
- **Ground-truth override** — if any major/critical finding is observed,
  the final `verdict` becomes `fail` even if the agent emitted
  `done(success=true)`. Three outcomes: `pass` / `warn` / `fail`. Proven
  on kansic.bykayle.com: Codex said "success", probe correctly flagged 3
  HTTP 401s + 4 a11y criticals the page was silently serving.
- **Playwright trace + HAR recorded** per run. Replay in Trace Viewer:
  `npx playwright show-trace trace.zip`.

### Phase B: service review (BFS crawl)
- New `--crawl` mode: BFS-traverse same-origin links from `--target`, run
  the agent on each page with a page-type-tailored checklist, aggregate
  findings into a single report.
- Flags: `--crawl-max-pages`, `--crawl-per-page-steps`.
- Coverage report (`coverage.json`) tracks visited vs discovered URLs;
  flags "unvisited at end" as a prompt to raise the budget.
- New files: `scripts/crawler.py`.

### Phase C: smart checks + regression DB
- **Page-type heuristics**: `_PAGE_TYPE_JS` detects form/table/modal/nav
  and emits a per-page checklist into the agent's goal (e.g. "forms found:
  try empty submit, long strings, special chars").
- **Regression fingerprint DB** at `~/.claude/skills/probe/regressions.json`.
  Every finding fingerprint persists across runs; next run tags items as
  new / recurrence / closed-this-run. Report includes "Closed" section to
  verify fixes stuck.
- New files: `scripts/regression_db.py`.

## 1.3.0 — 2026-04-21

- **3 new agent actions**:
  - `hover {index}` — mouse.move + settle, reveals hover-triggered menus
  - `drag {index, to_index?, dx?, dy?}` — mouse down → N-step move → up, works for drag-and-drop / slider handles / swipe-style gestures
  - `press_key {key}` — keyboard.press for Enter/Tab/Escape/ArrowDown etc.
  Response schema extended (all in `required`, nullable per OpenAI strict mode) with `key`, `to_index`, `dx`, `dy`.
- **Auth injection for agentic mode**:
  - `--cookies-file PATH` — Playwright-format JSON array seeded via `context.add_cookies` before navigation
  - `--local-storage-file PATH` — flat {key:value} JSON seeded via `add_init_script` before navigation
  Lets you drive the agent through login-gated flows without a live login step.
- Verified on duckduckgo.com: type_text → press_key('Enter') → URL check, 3 steps, all pass.

## 1.2.0 — 2026-04-21

- **Agentic mode added.** New CLI flag `--agentic "<goal>"` runs a
  browser-use-style loop: screenshot + numbered interactive-element list →
  Codex CLI picks one action as JSON (click / type_text / select / scroll /
  wait / navigate / go_back / find_text / done) → Playwright executes →
  repeat until `done` or `--agentic-max-steps` reached. New file
  `scripts/agent.py`; orchestrator gains `_do_agentic`. Journal written to
  `probe-runs/<ts>/agent/journal.md` with per-step screenshots +
  reasoning + action.
- Verified end-to-end: `--agentic "Find the H1 heading..."` against
  https://example.com succeeded in 1 step, correctly reading the page
  from the screenshot via Codex vision.
- Response schema uses OpenAI-strict shape: every property listed in
  `required` with nullable types for conditional fields.
- Windows cp949 console crash fixed — stdout/stderr forced to UTF-8 at
  process start.

## 1.1.0 — 2026-04-21

- **LLM judge backend swapped to Codex CLI (ChatGPT OAuth).** No more
  Anthropic API key required. `llm_judge.py` now shells out to `codex exec`
  with `--sandbox read-only --skip-git-repo-check --output-schema`,
  streaming the prompt via stdin and the screenshot via `-i`. Windows shim
  resolution handled via `shutil.which`. Graceful fallback when the CLI is
  absent or not logged in (`skipped: true` → pass).
- Defensive runner hardening: bare-string steps (e.g. `"reload"`) handled
  correctly, default timeout bounded, MutationObserver auto-disconnect
  init_script to survive apps with self-re-triggering observers, optional
  local HTTP server when target is `file://`.

## 1.0.0 — 2026-04-21

Initial release.

- Plan YAML schema: dimensions, viewports, browsers, setup, actions, assertions, strategy, parallel.
- Combinators: pairwise (greedy), full, random:N.
- Playwright runner: chromium/firefox/webkit, desktop/laptop/tablet/mobile viewports.
- Actions: reload, wait, click (w/ text filter + skipIf), type/fill, setLocalStorage, injectJS, scroll, hover.
- Assertions: noConsoleErrors, noConsoleWarnings, noNetworkErrors, noBrokenLinks, hasElement, elementVisible, elementText, axe (axe-core via CDN injection), visualDiff (Pillow), llmJudge (Claude Sonnet 4.6 vision).
- Visual diff: baseline auto-creation, pixel ratio, ignore regions, amplified diff image.
- LLM judge: JSON-constrained response, severity mapping, prompt caching.
- Auto-explore: URL → plan skeleton with discovered dimensions.
- Report: Markdown with severity icons, matrix, failure detail, reproduce scripts. Jinja template + inline fallback.
- Machine-readable `summary.json` alongside report.
- Reproduce scripts: standalone Playwright `.py` per combination.
- CLI: exit codes 0/1/2/3.
