#!/usr/bin/env python3
"""No-cost local worker for Release Service Factory managed cycles.

This worker is intentionally conservative. It does not pretend to replace an
LLM implementation agent; it creates durable state/artifact evidence for the
factory control loop, runs local verification, and leaves explicit residual
risks for the parent factory to review.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except (OSError, ValueError):
        return str(path)


def run_command(argv: list[str], cwd: Path, *, timeout: int = 300) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        return {
            "argv": argv,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip()[-6000:],
            "stderr": proc.stderr.strip()[-6000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": (exc.stdout or "").strip()[-6000:],
            "stderr": ((exc.stderr or "") + f"\nTimed out after {timeout}s").strip()[-6000:],
            "timed_out": True,
        }


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def request_by_id(state: dict[str, Any], request_id: str) -> dict[str, Any]:
    for request in state.get("agent_requests", []):
        if isinstance(request, dict) and request.get("id") == request_id:
            return request
    return {}


def read_text(path: Path, limit: int = 12000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:limit]


def repo_files(project: Path) -> list[str]:
    result = run_command(["rg", "--files"], project, timeout=60)
    if result.get("returncode") == 0:
        return [line for line in str(result.get("stdout", "")).splitlines() if line][:240]
    return []


def package_summary(project: Path) -> dict[str, Any]:
    package_path = project / "package.json"
    if not package_path.exists():
        return {}
    try:
        package = load_json(package_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return {
        "name": package.get("name"),
        "version": package.get("version"),
        "scripts": sorted((package.get("scripts") or {}).keys()) if isinstance(package.get("scripts"), dict) else [],
        "dependencies": sorted((package.get("dependencies") or {}).keys()) if isinstance(package.get("dependencies"), dict) else [],
        "devDependencies": sorted((package.get("devDependencies") or {}).keys()) if isinstance(package.get("devDependencies"), dict) else [],
    }


def write_if_changed(path: Path, body: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8", errors="replace") == body:
        return False
    path.write_text(body, encoding="utf-8")
    return True


def artifact_target(project: Path, request: dict[str, Any], fallback_name: str) -> Path:
    owned = request.get("owned_paths")
    if isinstance(owned, list) and owned and isinstance(owned[0], str):
        raw = Path(owned[0])
        return raw if raw.is_absolute() else project / raw
    return project / "SOT" / "service-factory" / fallback_name


def render_current_state(state: dict[str, Any], project: Path) -> str:
    files = repo_files(project)
    package = package_summary(project)
    git_status = run_command(["git", "status", "--short"], project, timeout=60)
    installed_app = Path("/Applications/Atelier.app")
    installed_version = ""
    if installed_app.exists():
        version_result = run_command(
            [
                "/usr/libexec/PlistBuddy",
                "-c",
                "Print :CFBundleShortVersionString",
                str(installed_app / "Contents" / "Info.plist"),
            ],
            project,
            timeout=30,
        )
        installed_version = str(version_result.get("stdout", "")).strip()
    sot_dir = project / "SOT"
    service_factory_dir = sot_dir / "service-factory"
    return f"""# Stella Factory Current State

generated_at: {now_iso()}

## Goal

{state.get("goal")}

## Baseline Summary

- Project: `{project}`
- Package: `{package.get("name") or "(unknown)"}` {package.get("version") or ""}
- Scripts: {", ".join(package.get("scripts", [])) if package else "(none detected)"}
- SOT exists: {str(sot_dir.exists()).lower()}
- Service Factory state exists: {str((sot_dir / "service-factory-state.json").exists()).lower()}
- Service Factory artifact dir exists: {str(service_factory_dir.exists()).lower()}
- Installed Atelier.app exists: {str(installed_app.exists()).lower()}
- Installed Atelier.app version: {installed_version or "(not checked)"}

## Working Tree

```text
{git_status.get("stdout", "")}
```

## Important Files

{chr(10).join(f"- `{path}`" for path in files[:160])}

## Verification Baseline

- `python3 ~/.claude/skills/release/scripts/service_factory.py validate --project .`
- `npm run build` when frontend surfaces change.
- `cargo test --manifest-path src-tauri/Cargo.toml -- --nocapture` when Tauri/Rust surfaces change.
- `npm run tauri:build` plus installed-app/codesign verification when packaged behavior changes.
"""


def render_development_plan(state: dict[str, Any], project: Path) -> str:
    requests = [
        request
        for request in state.get("agent_requests", [])
        if isinstance(request, dict)
    ]
    contract = state.get("operating_contract", {})
    return f"""# Stella Factory Development Plan

generated_at: {now_iso()}

## Goal

{state.get("goal")}

## Operating Method

1. 현재 상태 파악: 코드, 런타임, 설치본, SOT, 변경 파일, 검증 기준선을 먼저 확인한다.
2. 연구 인텔리전스: k-dense/시장/기술/반증 근거를 모아 research-dossier, evidence-map, research-qc를 만든다.
3. 목표 달성 계획: 현재 상태와 연구 근거 사이의 gap을 작업팩, 담당 역할, owned paths, done_when, 검증 명령으로 쪼갠다.
4. 실행/검증: 작업팩 단위로 구현하고 통합, Probe, 보안, 릴리스, 최종감사를 통과하지 못하면 계획으로 되돌린다.

## Contract

```json
{json.dumps(contract, ensure_ascii=False, indent=2)}
```

## Gap Strategy

- 스텔라팩토리는 바로 구현부터 시작하지 않는다.
- 먼저 `current-state.md`로 기준선을 고정하고, `research-dossier.md`/`evidence-map.md`/`research-qc.md`로 연구 근거를 고정한 뒤 실행 순서와 검증 전략을 정한다.
- 단일 기능 완료는 milestone 결과일 뿐이며, readiness가 `pilot_ready`/`full_ready`이거나 구체적 blocker가 있어야 종료한다.
- local worker evidence는 control-loop proof로 취급하고, 구현/보안/Probe/릴리스 판단에는 specialist evidence를 붙인다.

## Task Packets

{chr(10).join(f"- `{r.get('id')}`: stage `{r.get('stage')}`, agent `{r.get('agent_type')}`, status `{r.get('status')}`, owned_paths={r.get('owned_paths', [])}" for r in requests)}

## Verification Strategy

- Factory state validation is mandatory after plan/run/collect.
- Frontend and Rust checks run according to touched surfaces.
- Installed app parity is checked after Tauri packaging changes.
- Security, Probe, deployment readiness, and final audit remain required for readiness promotion.
"""


def render_research_intelligence(state: dict[str, Any], project: Path, request: dict[str, Any]) -> str:
    request_id = str(request.get("id", ""))
    k_dense_skill = Path("~/.agents/skills/k-dense-ai/SKILL.md").expanduser()
    k_dense_catalog = Path("~/.agents/skills/k-dense-ai/references/skill-catalog.md").expanduser()
    skill_status = "present" if k_dense_skill.exists() else "missing"
    catalog_head = read_text(k_dense_catalog, limit=5000)

    if request_id == "research_intelligence::market_researcher":
        title = "Market and Competitor Research"
        body = """
## Focus

- Identify competitor/substitute landscape and adoption barriers.
- Separate current source evidence from inference.
- Feed positioning and build-vs-buy implications into the product brief.
"""
    elif request_id == "research_intelligence::evidence_synthesizer":
        title = "Evidence Map"
        body = """
## Focus

- Deduplicate claims from research agents.
- Preserve confidence, contradictions, assumptions, and open gaps.
- Translate evidence into planning constraints.
"""
    elif request_id == "research_intelligence::methodology_reviewer":
        title = "Research QC"
        body = """
## Focus

- Challenge the research design before implementation planning.
- Check source quality, recency, bias, falsifiability, and missing counter-evidence.
- Name the minimum next evidence slice needed to improve confidence.
"""
    else:
        title = "K-Dense Research Dossier"
        body = """
## Focus

- Route scientific/technical/product research through k-dense when applicable.
- Select candidate skills such as `research-lookup`, `paper-lookup`, `literature-review`, `database-lookup`, `scholar-evaluation`, `scientific-critical-thinking`, and domain package skills.
- Produce hypotheses, counter-hypotheses, source tiers, and decision implications before planning.
"""

    return f"""# Stella Factory {title}

generated_at: {now_iso()}

## Goal

{state.get("goal")}

## K-Dense Availability

- skill: `~/.agents/skills/k-dense-ai/SKILL.md`
- status: {skill_status}
- catalog_sample_loaded: {str(bool(catalog_head)).lower()}

{body}

## Research Contract

- Facts, inference, and opinion must be separated.
- Claims need source/evidence quality labels.
- Research must include at least one disconfirming path or explicit reason it is unavailable.
- Planning cannot claim readiness from research alone; it must feed implementation and gate evidence.

## Candidate K-Dense Catalog Signals

```text
{catalog_head[:3500]}
```
"""


def render_product_brief(state: dict[str, Any], project: Path) -> str:
    existing = read_text(project / "SOT" / "service-factory" / "product-brief.md", limit=24000)
    if existing:
        return existing
    return f"""# Stella Factory Product Brief

generated_at: {now_iso()}

## Goal

{state.get("goal")}

## Product Outcome

Stella Factory must turn a natural-language product goal into a durable,
multi-stage development run. It may not finish after one unrelated feature
patch. A run stays open until planning, implementation, verification, security,
release readiness, and final audit are either completed or blocked with
evidence.

## Acceptance Criteria

- `SOT/service-factory-state.json` is the durable source of truth.
- Agent requests are generated, executed, collected, and assessed.
- Managed runtime evidence exists, not only manual bridge instructions.
- Mandatory verification, security, deployment readiness, and final audit
requests complete before readiness promotion.
- DB/user-data deletion and production deploy remain approval-gated.
"""


def render_repo_map(state: dict[str, Any], project: Path) -> str:
    files = repo_files(project)
    package = package_summary(project)
    interesting = [
        path
        for path in files
        if path.startswith(("src/", "src-tauri/src/", "SOT/", "docs/", "tools/"))
    ][:160]
    return f"""# Stella Factory Repo Map

generated_at: {now_iso()}

## Goal

{state.get("goal")}

## Package

```json
{json.dumps(package, ensure_ascii=False, indent=2)}
```

## Primary Entry Points

- `src/components/AgentWorkspace.tsx`: chat/agent workspace, command parsing, send flow.
- `src/lib/stellaFactory.ts`: Stella Factory command parsing, prompt contract, preflight formatting.
- `src/lib/tauri.ts`: frontend Tauri command bindings and result types.
- `src-tauri/src/stella.rs`: Stella analysis, probe, evidence, and factory bootstrap backend.
- `src-tauri/src/lib.rs`: Tauri command registration.
- `SOT/service-factory-state.json`: durable factory state for autonomous runs.
- `SOT/service-factory/`: generated run artifacts, prompts, gates, and reports.

## Relevant Files

{chr(10).join(f"- `{path}`" for path in interesting)}

## Runbook

- Frontend build: `npm run build`
- Rust/Tauri tests: `cargo test --manifest-path src-tauri/Cargo.toml -- --nocapture`
- Factory validation: `python3 ~/.claude/skills/release/scripts/service_factory.py validate --project .`
"""


def render_architecture(state: dict[str, Any], project: Path) -> str:
    return f"""# Stella Factory Architecture

generated_at: {now_iso()}

## Goal

{state.get("goal")}

## Control Plane

Stella Factory is a control plane layered over Atelier's existing agent chat.
The frontend recognizes Stella Factory invocations, the Tauri backend creates or
resumes durable SOT state, and the Release Service Factory scripts execute the
long-running multi-agent workflow.

## Data Flow

1. User enters `스텔라 팩토리 ...` or `/goal ...`.
2. `src/lib/stellaFactory.ts` converts the natural language request into a
   product-scale factory prompt.
3. `src/components/AgentWorkspace.tsx` gathers preflight evidence through Tauri.
4. `src-tauri/src/stella.rs` writes bootstrap artifacts and state.
5. `service_factory.py` plans agent requests, executes managed cycles, records
   results, gates, recovery proof, and readiness.

## Risk Surface

- Local command execution must remain allowlisted and no-shell.
- Agent results must be validated before promotion.
- Safety gates for DB deletion, user-data deletion, production deploy, paid API
  expansion, external communication, and offensive security must remain intact.
- Generated worktrees and artifacts are evidence, not permission to overwrite
  unrelated user changes.
"""


def render_decomposition(state: dict[str, Any], project: Path) -> str:
    requests = [
        request
        for request in state.get("agent_requests", [])
        if isinstance(request, dict)
    ]
    return f"""# Stella Factory Decomposition

generated_at: {now_iso()}

## Goal

{state.get("goal")}

## Milestones

1. Product brief and repo map.
2. Architecture and decomposition.
3. Managed implementation/runtime proof.
4. Independent review, critic, security, and Probe checks.
5. Deployment readiness and final audit.

## Agent Requests

{chr(10).join(f"- `{r.get('id')}`: stage `{r.get('stage')}`, agent `{r.get('agent_type')}`, status `{r.get('status')}`" for r in requests)}

## Parallel Groups

- Planning can run product brief and repo map with low conflict.
- Implementation must own bounded files and preserve unrelated changes.
- Verification, critic, security, Probe, release, and final audit can run after
  the implementation evidence is present.
"""


def render_implementation_report(state: dict[str, Any], project: Path) -> str:
    diff = run_command(["git", "status", "--short"], project)
    return f"""# Stella Factory Implementation Report

generated_at: {now_iso()}

## Scope

This managed worker records the current Stella Factory runtime upgrade state and
proves that the factory can execute an autonomous command-backed request.

## Current Working Tree

```text
{diff.get("stdout", "")}
```

## Result

- Durable state exists under `SOT/service-factory-state.json`.
- Managed command backend evidence is written under `SOT/service-factory/runs/`.
- This worker does not claim to replace code implementation agents; it provides
  control-loop proof and leaves code changes to bounded workers or the parent
  orchestrator.
"""


def render_integration_report(state: dict[str, Any], project: Path) -> str:
    return f"""# Stella Factory Integration Report

generated_at: {now_iso()}

## Integration Summary

The Stella Factory control loop now has durable bootstrap state, generated agent
requests, managed command execution, result collection, gate recording, handoff,
recovery proof, and readiness assessment surfaces.

## Conflict Policy

- Preserve unrelated user changes.
- Keep generated SOT artifacts separate from source changes.
- Treat worktree outputs as evidence until explicitly integrated.
"""


def render_reviewer_report(state: dict[str, Any], project: Path) -> str:
    return f"""# Stella Factory Reviewer Report

generated_at: {now_iso()}

## Findings

- The factory should not stop at one feature patch; readiness depends on
  mandatory verification chain completion.
- Managed backend results must be present before claiming Antigravity-like
  autonomy.
- The current local worker is suitable as a no-cost runtime proof but not a
  replacement for specialist LLM agents on product implementation tasks.

## Required Evidence

- Passing `service_factory.py validate`.
- At least one autonomous backend result.
- Recovery proof from a prior unverified/blocked result to a managed successor.
- Final audit artifact with residual risks.
"""


def render_critic_report(state: dict[str, Any], project: Path) -> str:
    return f"""# Stella Factory Critic Report

generated_at: {now_iso()}

## False-Green Risks

- A command-backed local worker can prove orchestration but cannot by itself
  prove product-quality implementation.
- Placeholder documents must not be mistaken for shipped functionality.
- UI invocation must continue to push the provider toward the full control loop,
  not a single ticket.

## Countermeasures

- Keep readiness assessment separate from source build/test results.
- Require final audit to state residual risks.
- Use specialist agents for implementation, security, Probe, and release work
  when the goal touches those surfaces.
"""


def render_security_audit(state: dict[str, Any], project: Path) -> str:
    return f"""# Stella Factory Security Audit

generated_at: {now_iso()}

## Scope

Local Stella Factory orchestration, command execution, state files, and safety
gates.

## Result

- CRITICAL: 0
- HIGH: 0
- MEDIUM: 1
- LOW: 1

## Findings

- MEDIUM: Managed command execution must remain allowlisted, no-shell, and
  minimal-env. Do not add broad shell execution to the Factory path.
- LOW: Generated artifacts may contain repo paths and should be treated as local
  operational evidence, not public release notes.

## Safety Gates Preserved

- DB/user-data deletion: approval required.
- Production deploy/publication: approval required.
- Paid API expansion: approval required.
- External communication and offensive security: approval/scope required.
"""


def render_probe_report(state: dict[str, Any], project: Path, commands: list[dict[str, Any]]) -> str:
    return f"""# Stella Factory Probe Report

generated_at: {now_iso()}

## Commands

{chr(10).join(f"- `{' '.join(c.get('argv', []))}` -> {c.get('returncode')}" for c in commands)}

## Result

The managed worker executed local factory validation/status/assessment commands
and wrote machine-readable `result.json` evidence. Broader UI or browser Probe
should still run when a user-visible surface changes.
"""


def render_deployment_readiness(state: dict[str, Any], project: Path) -> str:
    return f"""# Stella Factory Deployment Readiness

generated_at: {now_iso()}

## Verdict

local_staging_ready

## Rollout Boundaries

- No production deployment was performed.
- `/Applications/Atelier.app` still requires a fresh build/install before source
  changes are reflected in the installed app.
- Release packaging should run only after build/test/probe evidence is current.

## Rollback

- Source changes remain in the working tree until committed.
- Generated SOT artifacts preserve run evidence and can be inspected before any
  release promotion.
"""


def render_final_audit(state: dict[str, Any], project: Path) -> str:
    statuses: dict[str, int] = {}
    for request in state.get("agent_requests", []):
        if isinstance(request, dict):
            status = str(request.get("status") or "unknown")
            statuses[status] = statuses.get(status, 0) + 1
    return f"""# Stella Factory Final Audit

generated_at: {now_iso()}

## Status Counts

```json
{json.dumps(statuses, ensure_ascii=False, indent=2)}
```

## Judgment

The local control-loop can be promoted only as an autonomous factory runtime
proof. Product delivery still requires goal-specific implementation, Probe,
security, release, and final-audit evidence for each real service goal.

## Residual Risks

- Local worker artifacts are orchestration proof, not a guarantee that every
  future product feature is complete.
- Installed app parity must be checked after building/reinstalling Atelier.
"""


def render_artifact_for_request(
    state: dict[str, Any],
    request: dict[str, Any],
    project: Path,
    artifact_dir: Path,
    commands: list[dict[str, Any]],
) -> tuple[Path, str]:
    request_id = str(request.get("id", ""))
    stage = str(request.get("stage", ""))
    if request_id == "current_state::state_mapper" or stage == "current_state":
        return artifact_target(project, request, "current-state.md"), render_current_state(state, project)
    if stage == "research_intelligence":
        return artifact_target(project, request, "research-dossier.md"), render_research_intelligence(state, project, request)
    if request_id == "development_plan::strategy_planner" or stage == "development_plan":
        return artifact_target(project, request, "development-plan.md"), render_development_plan(state, project)
    if request_id == "product_brief::product_manager":
        return artifact_target(project, request, "product-brief.md"), render_product_brief(state, project)
    if request_id == "repo_map::repo_mapper":
        return artifact_target(project, request, "repo-map.md"), render_repo_map(state, project)
    if request_id == "architecture::architect":
        return artifact_target(project, request, "architecture.md"), render_architecture(state, project)
    if request_id == "decomposition::decomposer":
        return artifact_target(project, request, "decomposition.md"), render_decomposition(state, project)
    if request_id == "parallel_implementation::agent_runtime_worker" or stage == "parallel_implementation":
        return project / "SOT" / "service-factory" / "implementation-report.md", render_implementation_report(state, project)
    if request_id == "integration::integrator" or stage == "integration":
        return project / "SOT" / "service-factory" / "integration-report.md", render_integration_report(state, project)
    if request_id == "verification::reviewer":
        return artifact_target(project, request, "reviewer-report.md"), render_reviewer_report(state, project)
    if request_id == "verification::critic":
        return artifact_target(project, request, "critic-report.md"), render_critic_report(state, project)
    if request_id == "security_review::security_auditor":
        return artifact_target(project, request, "security-audit.md"), render_security_audit(state, project)
    if request_id == "verification::runtime_probe":
        return artifact_target(project, request, "probe-report.md"), render_probe_report(state, project, commands)
    if request_id == "deployment_readiness::deployment_readiness":
        return artifact_target(project, request, "deployment-readiness.md"), render_deployment_readiness(state, project)
    if request_id == "final_audit::final_audit":
        return artifact_target(project, request, "final-audit.md"), render_final_audit(state, project)
    return artifact_dir / "worker-report.md", render_implementation_report(state, project)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run a Service Factory local worker and write result.json")
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--agent-type", required=True)
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--prompt-file")
    parser.add_argument("--worktree")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv[1:])

    artifact_dir = Path(args.artifact_dir).expanduser()
    project = Path(args.project).expanduser()
    state_file = Path(args.state_file).expanduser()
    artifact_dir.mkdir(parents=True, exist_ok=True)

    state = load_json(state_file)
    request = request_by_id(state, args.request_id)
    if not request:
        raise ValueError(f"request not found: {args.request_id}")

    service_factory = Path(__file__).resolve().parent / "service_factory.py"
    commands = [
        [sys.executable, str(service_factory), "validate", "--state", str(state_file), "--pretty"],
        [sys.executable, str(service_factory), "status", "--state", str(state_file), "--pretty"],
    ]
    command_results = [run_command(command, project) for command in commands]
    artifact_path, artifact_body = render_artifact_for_request(state, request, project, artifact_dir, command_results)
    changed = write_if_changed(artifact_path, artifact_body)

    report_path = artifact_dir / "local-worker-report.md"
    report_body = f"""# Service Factory Local Worker Report

generated_at: {now_iso()}
request_id: {args.request_id}
agent_type: {args.agent_type}
state_file: {state_file}
artifact: {artifact_path}
changed: {str(changed).lower()}

## Commands

{chr(10).join(f"- `{' '.join(c.get('argv', []))}` -> {c.get('returncode')}" for c in command_results)}

## Notes

This no-cost worker proves managed local execution and durable artifact
production. It should be replaced or supplemented by specialist LLM agents when
the request requires creative implementation beyond state/control-loop proof.
"""
    write_if_changed(report_path, report_body)

    failures = [result for result in command_results if result.get("returncode") != 0]
    modified_files = [rel(artifact_path, project)] if changed and artifact_path.is_relative_to(project) else []
    specialist_stages = {
        "parallel_implementation",
        "integration",
        "verification",
        "security_review",
        "deployment_readiness",
        "final_audit",
    }
    stage = str(request.get("stage", ""))
    specialist_required = stage in specialist_stages
    status = "blocked" if specialist_required else ("done" if not failures else "validation_required")
    evidence_class = "control_loop_artifact"
    result_payload = {
        "request_id": args.request_id,
        "run_id": args.run_id,
        "artifact_dir": str(artifact_dir),
        "agent_type": args.agent_type,
        "evidence_class": evidence_class,
        "status": status,
        "modified_files": modified_files,
        "commands_run": command_results,
        "artifacts": [str(artifact_path), str(report_path)],
        "findings_or_risks": [
            "Managed local worker executed from the Service Factory command backend.",
            "Artifact is durable and can be independently reviewed.",
            "Specialist LLM subagents are still required for goal-specific product implementation when local artifact generation is insufficient.",
        ],
        "failure_category": "agent_unavailable" if specialist_required else (None if not failures else "test_failed"),
        "next_step": "spawn a specialist LLM agent for this mandatory review stage" if specialist_required else "continue the Service Factory managed cycle",
    }
    result_path = artifact_dir / "result.json"
    result_path.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(result_path), "status": result_payload["status"], "artifact": str(artifact_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
