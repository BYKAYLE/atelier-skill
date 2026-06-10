# probe — Architecture

## Principle

Combinatorial + Agentic E2E. Two-layer judgement: free automatic checks
handle most cases; LLM judge is reserved for ambiguous visual states.

## Modules

| Module | Role |
|---|---|
| `plan.py` | YAML schema, loader, validator, `${var}` substitution, `skipIf` eval |
| `combinator.py` | pairwise (greedy IPOG-ish), full, random(N) |
| `checks.py` | `RunContext`, assertion registry, link classification |
| `runner.py` | Playwright per-combo exercise, log/state capture, screenshot, axe, reproduce script emit |
| `visual_diff.py` | Pillow pixel diff with ignore regions |
| `llm_judge.py` | Codex CLI subprocess (ChatGPT OAuth) + vision + JSON-schema output |
| `explorer.py` | Auto-analyse a URL, emit plan skeleton |
| `report.py` | Markdown report (Jinja when available, inline fallback) |
| `run_probe.py` | CLI entry + thread-pool orchestration |

## Flow

```
 ┌──── plan.yml
 │
 ▼
load_plan ─▶ generate(dims, strategy) ─▶ explode(viewports × browsers) ─▶ combos[]
                                                                             │
                                                             per combo (ThreadPool)
                                                                             ▼
                                                                   runner.exercise
                                                                    ├─ console/net hooks
                                                                    ├─ seed localStorage
                                                                    ├─ navigate + actions
                                                                    ├─ collect element state
                                                                    ├─ axe.run
                                                                    ├─ screenshot + visualDiff
                                                                    └─ emit reproduce.py
                                                                             │
                                                  ┌──────── RunContext ──────┤
                                                  ▼                          │
                                           llm_judge (optional)              │
                                                  │                          │
                                                  ▼                          ▼
                                             judgements              assertions loop
                                                                             │
                                                                             ▼
                                                                   result rows + overall
                                                                             │
                                                                             ▼
                                                                       report.py
                                                                    ┌────────┴────────┐
                                                                    ▼                 ▼
                                                               report.md        summary.json
```

## Severity model

Per assertion:
- `critical` — runtime crash, JS error, blank page
- `major`    — broken interaction, missing element, network failure
- `minor`    — a11y warnings below threshold, slight visual diff, LLM flag "low"
- `info`     — pass message

Per combination `overall`:
- any major/critical failure → `fail`
- any minor-only failure → `warn`
- everything passes → `pass`

CLI exit: 0 if zero `fail`, else 1.

## LLM judge backend (Codex CLI)

- Backend: `codex exec` subprocess with `--sandbox read-only --skip-git-repo-check`.
- Auth: ChatGPT OAuth via `codex login`. No API key in env.
- Billing: ChatGPT Plus/Pro subscription; no per-call $ cost from the user's
  perspective (rate-limited by the ChatGPT plan).
- Model: whatever Codex CLI picks by default (currently `gpt-5.4`). Override
  per-assertion with `llmJudge.model: gpt-5` etc.
- Image input: screenshot passed as `-i <path>`. Prompt (protocol + bindings
  + user question) streamed via stdin with `-` positional.
- JSON output: `--output-schema` points at a temp file describing the
  required shape (`ok`, `severity`, `summary`, `findings`); the final
  message is read from `-o <temp>` and parsed.
- Disable: `--no-llm` CLI flag or omit `llmJudge` from assertions.
- Graceful fallback: absent CLI or not logged in → assertion silently
  marked `skipped: true` and treated as pass.

## Extension points

- New assertions: add handler to `_HANDLERS` in `checks.py` and populate any
  needed data in `RunContext` from `runner.py`.
- New action verbs: extend `_run_step` in `runner.py`.
- New strategies: add to `generate()` in `combinator.py`.
- CI integration: subprocess `run_probe.py`, parse `summary.json`.

## Known trade-offs

- `file://` URLs have quirky origin behaviour; prefer static server for
  reliable localStorage & fetch.
- Pairwise hides 3+ way interactions; use `strategy: full` for small dim
  spaces.
- Thread-pool parallelism means N Playwright browser processes — each
  consumes ~200MB. Keep `parallel` ≤ CPU cores.
- Visual diff is pixel-based; dynamic content (timestamps, animations)
  causes noise. Use `ignoreRegions`.
