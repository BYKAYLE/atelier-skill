#!/usr/bin/env python3
"""Create and validate Release Service Factory state files."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


QUEUE_STATES = {"queued", "in_progress", "blocked", "validation_required", "done", "discarded"}
FACTORY_STATES = {"draft", "running", "blocked", "validation_required", "done", "discarded", "interrupted"}
GATE_STATUSES = {"pending", "approved", "rejected", "not_applicable"}
LEASE_MODES = {"read", "write", "review", "integrate"}
REQUEST_STATUSES = {"queued", "running", "completed", "failed", "blocked", "cancelled", "validation_required"}
RESULT_STATUSES = {"completed", "failed", "blocked", "validation_required"}
GATE_RESULT_STATUSES = {"passed", "failed", "blocked", "skipped", "timeout"}
AUTONOMOUS_BACKENDS = {"command", "codex-exec"}
SCRIPT_DIR = Path(__file__).resolve().parent
RELEASE_DIR = SCRIPT_DIR.parent
AGENTS_DIR = Path("~/.codex/agents").expanduser()
STELLA_COMMAND_OWNER = "Stella"
RELEASE_EXECUTION_CONTROLLER = "Release"

# 260602 — dynamic_workflow spawn_runtime backend (Architecture-First: 신규 모듈 분리, 본 파일은 thin wiring).
# v0.2 `foundation_ready_but_not_autonomous` 의 비어있는 spawn_runtime 자리에 Claude Code Workflow 도구의
# parallel/pipeline fan-out 을 연결한다. 본 파일은 dispatch 명령 등록 + 신규 backend 모듈로의 호출만 담당.
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from service_factory_dynamic_workflow_backend import (  # noqa: E402  (facade import after sys.path setup)
    collect_dispatch_requests as _dw_collect_dispatch_requests,
    write_dispatch as _dw_write_dispatch,
    DEFAULT_MAX_PARALLEL as _DW_DEFAULT_MAX_PARALLEL,
)

# 260603 — file_leases seeder (Architecture-First: 신규 모듈, 본 파일은 thin wiring).
# service-factory.md 의 "Release 는 stage 시작 전에 file_leases 를 상태 파일에 남긴다" 약속이
# v0.2 에서 미구현이었음. agent_request 의 owned_paths 가 이미 박혀 있으므로 그 데이터를
# state["file_leases"] ledger 로 흡수하는 한 줄 호출만 추가.
from service_factory_file_leases_seeder import (  # noqa: E402
    seed_file_leases_from_requests as _fl_seed_file_leases_from_requests,
    file_leases_blockers as _fl_file_leases_blockers,
    detect_write_conflicts as _fl_detect_write_conflicts,
)
from service_factory_intake_contract import (  # noqa: E402
    INTAKE_FIELDS as _IC_FIELDS,
    build_intake_contract as _ic_build_contract,
    set_contract_field as _ic_set_field,
    intake_gate as _ic_intake_gate,
)

SENSITIVE_COMMAND_RULES = [
    ("db_data_deletion", re.compile(r"\b(drop\s+database|drop\s+table|truncate\s+table|delete\s+from\b|mongo\s+.*dropDatabase|redis-cli\s+flush(all|db))\b", re.IGNORECASE)),
    ("destructive_filesystem", re.compile(r"(^|[;&|]\s*)(?:\S*/)?rm\s+(-[^\s]*r[^\s]*f|-rf|-fr)\b|(^|[;&|]\s*)(?:\S*/)?trash\s+.*(--force|-f)", re.IGNORECASE)),
    ("production_deploy", re.compile(r"\b(vercel\s+--prod|firebase\s+deploy|gcloud\s+app\s+deploy|kubectl\s+(apply|delete|rollout)|helm\s+(install|upgrade|uninstall)|terraform\s+(apply|destroy)|pulumi\s+up|flyctl\s+deploy|railway\s+up)\b", re.IGNORECASE)),
    ("paid_api_budget", re.compile(r"\b(stripe\s+.*(create|update)|openai\s+.*(fine[_-]?tunes?|batches?)|anthropic\s+.*batches?)\b", re.IGNORECASE)),
    ("external_communication", re.compile(r"\b(gh\s+pr\s+merge|gh\s+release\s+create|git\s+push|curl\s+.*(slack|discord|telegram|sendgrid|mailgun)|aws\s+ses|mailgun)\b", re.IGNORECASE)),
    ("offensive_security", re.compile(r"\b(nmap|masscan|sqlmap|metasploit|msfconsole|hydra|gobuster|ffuf|nikto)\b", re.IGNORECASE)),
]

RUN_FAILURE_CATEGORIES = {
    "permission_blocked",
    "command_timeout",
    "command_failed",
    "agent_unavailable",
    "spawn_backend_missing",
    "unsafe_request",
    "quota_exhausted",
    "test_failed",
    "merge_conflict",
    "agent_stalled",
    "unknown",
    "insufficient_evidence",
    "child_result_trust_boundary",
}

INTERPRETER_EXECUTABLES = {"python", "python3", "python3.14", "node", "bash", "sh", "zsh", "ruby", "perl", "osascript"}
ALLOWED_PYTHON_SCRIPTS = {
    SCRIPT_DIR / "service_factory.py",
    SCRIPT_DIR / "service_factory_local_verifier.py",
    SCRIPT_DIR / "service_factory_local_worker.py",
}

APPROVAL_GATES = [
    "db_data_deletion",
    "production_deploy",
    "paid_api_budget",
    "external_communication",
    "offensive_security",
]

BASE_ROLES = [
    {
        "id": "sentinel",
        "owner": "Stella",
        "kind": "sentinel",
        "purpose": "Request normalization, priority, and boundary decisions",
        "spawn_policy": "external_entrypoint",
    },
    {
        "id": "orchestrator",
        "owner": RELEASE_EXECUTION_CONTROLLER,
        "kind": "execution_controller",
        "purpose": "State ledger, dispatch/collect, gates, and delivery control under Stella command",
        "spawn_policy": "local",
    },
    {
        "id": "research_director",
        "owner": "k-dense-researcher",
        "kind": "researcher",
        "purpose": "K-Dense-backed research intelligence, evidence map, hypothesis framing, and source-quality routing before product planning",
        "spawn_policy": "required_after_current_state",
    },
    {
        "id": "research_synthesizer",
        "owner": "knowledge-synthesizer",
        "kind": "researcher",
        "purpose": "Non-redundant synthesis of research, market, technical, and counter-evidence before implementation planning",
        "spawn_policy": "after_research_inputs",
    },
    {
        "id": "research_methodologist",
        "owner": "research-methodologist",
        "kind": "reviewer",
        "purpose": "Research methodology, bias, falsifiability, and evidence-quality review before planning depends on the research lane",
        "spawn_policy": "after_research_inputs",
    },
    {
        "id": "architect",
        "owner": "architect-reviewer",
        "kind": "planner",
        "purpose": "Architecture and long-term boundary review",
        "spawn_policy": "dynamic_when_architecture_or_cross_surface",
    },
    {
        "id": "builder",
        "owner": "fullstack-developer",
        "kind": "worker",
        "purpose": "Implementation across bounded files and surfaces",
        "spawn_policy": "dynamic_per_surface",
    },
    {
        "id": "reviewer",
        "owner": "reviewer",
        "kind": "reviewer",
        "purpose": "Independent correctness and regression review",
        "spawn_policy": "after_worker_output",
    },
    {
        "id": "runtime_auditor",
        "owner": "Probe",
        "kind": "auditor",
        "purpose": "Independent UI/API/runtime smoke and security assertions",
        "spawn_policy": "required_when_url_ui_or_runtime_surface",
    },
    {
        "id": "security_auditor",
        "owner": "security-router",
        "kind": "auditor",
        "purpose": "Static/code security and specialist security routing",
        "spawn_policy": "required_for_auth_data_security_or_final_security",
    },
]

SURFACE_ROLE_RULES = [
    ("scientific_research_worker", "k-dense-researcher", ["k-dense", "scientific research", "논문", "연구", "학술", "database lookup", "evidence", "hypothesis"]),
    ("research_synthesis_worker", "knowledge-synthesizer", ["synthesis", "evidence map", "가설", "근거", "research qc", "methodology"]),
    ("agent_runtime_worker", "tooling-engineer", ["service factory", "autonomous product delivery", "spawn", "dispatch", "collect", "agent_requests", "에이전트", "자율 개발"]),
    ("orchestration_reviewer", "workflow-orchestrator", ["orchestration", "workflow", "handoff", "watchdog", "readiness", "오케스트레이션", "최종목표"]),
    ("frontend_worker", "frontend-developer", ["frontend", "ui", "react", "next", "vue", "screen", "dashboard", "화면", "프론트"]),
    ("backend_worker", "backend-developer", ["backend", "api", "server", "fastapi", "django", "백엔드", "서버"]),
    ("desktop_worker", "electron-pro", ["tauri", "electron", "desktop", "macos", "앱", "데스크탑"]),
    ("mobile_worker", "mobile-developer", ["ios", "android", "mobile", "모바일"]),
    ("data_worker", "data-engineer", ["etl", "pipeline", "warehouse", "data", "데이터", "ingestion"]),
    ("database_reviewer", "database-administrator", ["database", "db", "sql", "postgres", "mysql", "migration", "데이터베이스"]),
    ("devops_worker", "devops-engineer", ["deploy", "docker", "kubernetes", "ci", "cd", "cloud", "배포", "인프라"]),
    ("sre_reviewer", "sre-engineer", ["slo", "latency", "monitoring", "alert", "reliability", "장애", "운영"]),
    ("performance_reviewer", "performance-engineer", ["performance", "slow", "latency", "perf", "성능", "느림"]),
    ("security_specialist", "security-auditor", ["auth", "oauth", "permission", "secret", "security", "보안", "권한", "인증"]),
    ("payment_reviewer", "payment-integration", ["payment", "billing", "checkout", "subscription", "결제", "구독"]),
]

FOUNDRY_ROLE_RULES = [
    ("browser_extension_worker", "browser-extension-engineer", ["browser extension", "chrome extension", "extension", "브라우저 확장", "크롬 확장"], "Build and review browser extension manifests, background scripts, content scripts, permissions, and store packaging."),
    ("webgpu_worker", "webgpu-engineer", ["webgpu", "shader", "wgsl", "gpu shader", "그래픽 파이프라인"], "Build and review WebGPU, shader, and browser graphics pipeline work."),
    ("vector_search_worker", "vector-search-engineer", ["vector db", "벡터", "embedding search", "rag", "semantic search"], "Build and review vector search, retrieval, embedding indexing, and RAG evaluation paths."),
    ("llm_eval_reviewer", "llm-evaluation-engineer", ["eval", "evaluation harness", "llm judge", "모델 평가", "평가셋"], "Design and review model evaluation harnesses, datasets, scoring, and regression gates."),
    ("realtime_collab_worker", "realtime-collaboration-engineer", ["collaboration", "multi-user", "presence", "crdt", "실시간 협업"], "Build and review realtime collaboration, presence, conflict resolution, and sync flows."),
]

STAGE_AGENT_BLUEPRINTS = [
    {
        "id": "state_mapper",
        "stage": "current_state",
        "agent_type": "code-mapper",
        "kind": "explorer",
        "owned_paths": ["SOT/service-factory/current-state.md"],
        "success_criteria": ["current repo/runtime/SOT/install state", "verification baseline", "known constraints"],
    },
    {
        "id": "research_director",
        "stage": "research_intelligence",
        "agent_type": "k-dense-researcher",
        "kind": "planner",
        "owned_paths": ["SOT/service-factory/research-dossier.md"],
        "success_criteria": ["k-dense skill routing plan", "literature/database/source strategy", "hypotheses and counter-hypotheses", "evidence quality tiers"],
    },
    {
        "id": "market_researcher",
        "stage": "research_intelligence",
        "agent_type": "market-researcher",
        "kind": "planner",
        "owned_paths": ["SOT/service-factory/market-research.md"],
        "success_criteria": ["competitor/substitute landscape", "adoption and positioning risks", "freshness and source caveats"],
    },
    {
        "id": "evidence_synthesizer",
        "stage": "research_intelligence",
        "agent_type": "knowledge-synthesizer",
        "kind": "planner",
        "owned_paths": ["SOT/service-factory/evidence-map.md"],
        "success_criteria": ["deduplicated claims", "confidence levels", "decision implications", "unresolved conflicts"],
    },
    {
        "id": "methodology_reviewer",
        "stage": "research_intelligence",
        "agent_type": "research-methodologist",
        "kind": "reviewer",
        "owned_paths": ["SOT/service-factory/research-qc.md"],
        "success_criteria": ["research design critique", "bias and falsification checks", "minimum next evidence slice"],
    },
    {
        "id": "strategy_planner",
        "stage": "development_plan",
        "agent_type": "project-manager",
        "kind": "planner",
        "owned_paths": ["SOT/service-factory/development-plan.md"],
        "success_criteria": ["gap analysis", "ordered task packets", "execution and verification strategy"],
    },
    {
        "id": "product_manager",
        "stage": "product_brief",
        "agent_type": "product-manager",
        "kind": "planner",
        "owned_paths": ["SOT/service-factory/product-brief.md"],
        "success_criteria": ["acceptance criteria", "user-visible core loop", "non-goals and forbidden actions"],
    },
    {
        "id": "repo_mapper",
        "stage": "repo_map",
        "agent_type": "code-mapper",
        "kind": "explorer",
        "owned_paths": ["SOT/service-factory/repo-map.md"],
        "success_criteria": ["entrypoints", "run commands", "high-risk surfaces"],
    },
    {
        "id": "architect",
        "stage": "architecture",
        "agent_type": "architect-reviewer",
        "kind": "planner",
        "owned_paths": ["SOT/service-factory/architecture.md"],
        "success_criteria": ["service boundaries", "data flow", "risk surface", "rollback assumptions"],
    },
    {
        "id": "decomposer",
        "stage": "decomposition",
        "agent_type": "project-manager",
        "kind": "planner",
        "owned_paths": ["SOT/service-factory/decomposition.md"],
        "success_criteria": ["task breakdown", "file ownership", "parallel groups", "blocked dependencies"],
    },
    {
        "id": "builder",
        "stage": "parallel_implementation",
        "agent_type": "fullstack-developer",
        "kind": "worker",
        "owned_paths": [],
        "success_criteria": ["goal-specific implementation diff", "modified files", "local verification evidence"],
    },
    {
        "id": "integrator",
        "stage": "integration",
        "agent_type": "fullstack-developer",
        "kind": "integrator",
        "owned_paths": [],
        "success_criteria": ["integrated diff", "build/test rerun", "handoff to reviewers"],
    },
    {
        "id": "reviewer",
        "stage": "verification",
        "agent_type": "reviewer",
        "kind": "reviewer",
        "owned_paths": ["SOT/service-factory/reviewer-report.md"],
        "success_criteria": ["behavioral correctness", "regression risk", "real verification evidence"],
    },
    {
        "id": "critic",
        "stage": "verification",
        "agent_type": "risk-manager",
        "kind": "critic",
        "owned_paths": ["SOT/service-factory/critic-report.md"],
        "success_criteria": ["false-green risks", "mock-only risks", "missing rollback or edge cases"],
    },
    {
        "id": "security_auditor",
        "stage": "security_review",
        "agent_type": "security-auditor",
        "kind": "auditor",
        "owned_paths": ["SOT/service-factory/security-audit.md"],
        "success_criteria": ["CRITICAL=0", "HIGH=0 or exception", "scope and evidence"],
    },
    {
        "id": "runtime_probe",
        "stage": "verification",
        "agent_type": "Probe",
        "kind": "auditor",
        "owned_paths": ["SOT/service-factory/probe-report.md"],
        "success_criteria": ["probe exit code", "summary.json pass/fail", "report.md path"],
    },
    {
        "id": "deployment_readiness",
        "stage": "deployment_readiness",
        "agent_type": "deployment-engineer",
        "kind": "auditor",
        "owned_paths": ["SOT/service-factory/deployment-readiness.md"],
        "success_criteria": ["staging or skip reason", "rollback plan", "release blockers"],
    },
    {
        "id": "final_audit",
        "stage": "final_audit",
        "agent_type": "reviewer",
        "kind": "auditor",
        "owned_paths": ["SOT/service-factory/final-audit.md"],
        "success_criteria": ["gate summary", "known issues", "delivery report", "residual risks"],
    },
]

STAGES = [
    ("intake", ["sentinel", "orchestrator"], [], ["goal", "success_criteria", "constraints"]),
    ("current_state", ["architect"], ["intake"], ["repo_runtime_sot_install_baseline"]),
    ("research_intelligence", ["research_director", "research_synthesizer", "research_methodologist"], ["current_state"], ["research_dossier", "evidence_map", "research_qc"]),
    ("development_plan", ["orchestrator", "architect"], ["research_intelligence"], ["gap_analysis", "task_packets", "verification_strategy"]),
    ("product_brief", ["orchestrator"], ["development_plan"], ["acceptance_criteria"]),
    ("repo_map", ["architect"], ["product_brief"], ["code_map", "runbook"]),
    ("architecture", ["architect"], ["repo_map"], ["architecture_decisions", "risk_surface"]),
    ("decomposition", ["orchestrator"], ["architecture"], ["task_breakdown", "file_ownership", "parallel_groups"]),
    ("parallel_implementation", ["builder"], ["decomposition"], ["modified_files", "local_verification"]),
    ("integration", ["orchestrator", "builder"], ["parallel_implementation"], ["integrated_diff", "conflict_resolution"]),
    ("verification", ["reviewer", "runtime_auditor"], ["integration"], ["tests", "build", "probe_or_skip_reason"]),
    ("security_review", ["security_auditor", "runtime_auditor"], ["verification"], ["static_security", "runtime_security_or_skip_reason"]),
    ("deployment_readiness", ["orchestrator"], ["security_review"], ["staging_smoke_or_skip_reason", "rollback_plan"]),
    ("final_audit", ["orchestrator", "reviewer"], ["deployment_readiness"], ["gate_summary", "known_issues", "delivery_report"]),
]

OPERATING_PHASES = [
    {
        "id": "current_state",
        "name": "Current State Discovery",
        "rule": "Inspect the real repo, runtime, installed app, SOT, dirty paths, existing capabilities, risks, and verification baseline before deciding implementation.",
        "artifacts": ["SOT/service-factory/current-state.md"],
    },
    {
        "id": "research_intelligence",
        "name": "Research Intelligence and Hypothesis QC",
        "rule": "Before product planning, run K-Dense-backed research, market/technical evidence gathering, hypothesis framing, counter-evidence search, and methodology review. Planning must cite this research lane instead of relying on unsupported intuition.",
        "artifacts": ["SOT/service-factory/research-dossier.md", "SOT/service-factory/evidence-map.md", "SOT/service-factory/research-qc.md"],
    },
    {
        "id": "development_plan",
        "name": "Goal-to-Plan Strategy",
        "rule": "Convert the goal, current-state baseline, and research intelligence into a gap analysis, ordered task packets, role assignments, owned paths, done_when, and verification strategy.",
        "artifacts": ["SOT/service-factory/development-plan.md"],
    },
    {
        "id": "execution_verification",
        "name": "Execution and Evidence Loop",
        "rule": "Execute bounded task packets, integrate changes, run Probe/security/release/final-audit gates, and loop back to planning on failure or missing evidence.",
        "artifacts": ["SOT/service-factory/progress.jsonl", "SOT/service-factory/artifact-review.md", "SOT/service-factory/antigravity-readiness.md"],
    },
]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def factory_id() -> str:
    return "sf-" + datetime.now().strftime("%Y%m%d-%H%M%S")


def run_id() -> str:
    return "sf-run-" + datetime.now().strftime("%Y%m%d-%H%M%S")


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return cleaned or "item"


def canonical_artifact_dir(project: Path, request: dict[str, Any], run_id_value: str) -> Path:
    return project / "SOT" / "service-factory" / "runs" / run_id_value / slug(str(request.get("id", "request")))


def stage_spec_map() -> dict[str, tuple[str, list[str], list[str], list[str]]]:
    return {stage_id: (stage_id, roles, depends_on, done_requires) for stage_id, roles, depends_on, done_requires in STAGES}


def make_stage(stage_id: str, roles: list[str], depends_on: list[str], done_requires: list[str], *, index: int) -> dict[str, Any]:
    return {
        "id": stage_id,
        "state": "in_progress" if index == 0 else "queued",
        "roles": roles,
        "depends_on": depends_on,
        "done_requires": done_requires,
        "artifacts": [],
    }


def ensure_operating_contract(state: dict[str, Any]) -> bool:
    changed = False
    contract = state.get("operating_contract")
    if not isinstance(contract, dict) or contract.get("version") != "state-plan-execute-v1":
        state["operating_contract"] = {
            "version": "state-plan-execute-v1",
            "required_order": ["current_state", "research_intelligence", "development_plan", "execution_verification"],
            "rule": "Always inspect current state first, then run research intelligence and hypothesis QC, then write a goal-to-plan strategy, then execute and verify. Do not start implementation before current-state, research, and development-plan artifacts exist unless the user explicitly requests a trivial one-shot task.",
            "phases": OPERATING_PHASES,
        }
        changed = True
    else:
        desired_contract = {
            "required_order": ["current_state", "research_intelligence", "development_plan", "execution_verification"],
            "rule": "Always inspect current state first, then run research intelligence and hypothesis QC, then write a goal-to-plan strategy, then execute and verify. Do not start implementation before current-state, research, and development-plan artifacts exist unless the user explicitly requests a trivial one-shot task.",
            "phases": OPERATING_PHASES,
        }
        for key, value in desired_contract.items():
            if contract.get(key) != value:
                contract[key] = value
                changed = True

    stages = state.get("stages")
    if not isinstance(stages, list):
        state["stages"] = []
        stages = state["stages"]
        changed = True

    existing = {str(stage.get("id")): stage for stage in stages if isinstance(stage, dict)}
    spec = stage_spec_map()
    rebuilt: list[dict[str, Any]] = []
    for index, (stage_id, roles, depends_on, done_requires) in enumerate(STAGES):
        stage = existing.get(stage_id)
        if not isinstance(stage, dict):
            stage = make_stage(stage_id, roles, depends_on, done_requires, index=index)
            changed = True
        else:
            for key, value in {
                "roles": roles,
                "depends_on": depends_on,
                "done_requires": done_requires,
            }.items():
                if stage.get(key) != value:
                    stage[key] = value
                    changed = True
            stage.setdefault("artifacts", [])
        rebuilt.append(stage)

    for stage in stages:
        if isinstance(stage, dict) and str(stage.get("id")) not in spec:
            rebuilt.append(stage)
    if rebuilt != stages:
        state["stages"] = rebuilt
        changed = True
    return changed


def default_state_path(project: Path) -> Path:
    return project / "SOT" / "service-factory-state.json"


def project_name(project: Path) -> str:
    return project.resolve().name


def detect_roles(goal: str) -> list[dict[str, Any]]:
    normalized = goal.lower()
    roles: list[dict[str, Any]] = []
    seen = {role["id"] for role in BASE_ROLES}

    for role_id, owner, keywords in SURFACE_ROLE_RULES:
        if role_id in seen:
            continue
        if any(keyword.lower() in normalized for keyword in keywords):
            roles.append(
                {
                    "id": role_id,
                    "owner": owner,
                    "kind": "worker" if role_id.endswith("_worker") else "reviewer",
                    "purpose": f"Dynamic specialist for goal keywords: {', '.join(keywords[:3])}",
                    "spawn_policy": "dynamic_when_surface_detected",
                }
            )
            seen.add(role_id)

    return BASE_ROLES + roles


def agent_manifest_exists(agent_type: str) -> bool:
    if agent_type == "Probe":
        return True
    return (AGENTS_DIR / f"{agent_type}.toml").exists()


def foundry_roles(goal: str) -> list[dict[str, Any]]:
    normalized = goal.lower()
    roles: list[dict[str, Any]] = []
    for role_id, proposed_agent, keywords, purpose in FOUNDRY_ROLE_RULES:
        if any(keyword.lower() in normalized for keyword in keywords):
            roles.append(
                {
                    "id": role_id,
                    "proposed_agent": proposed_agent,
                    "purpose": purpose,
                    "keywords": keywords,
                    "manifest_exists": agent_manifest_exists(proposed_agent),
                }
            )
    return roles


def role_by_id(roles: list[dict[str, Any]], role_id: str) -> dict[str, Any] | None:
    for role in roles:
        if role.get("id") == role_id:
            return role
    return None


def build_agent_requests(state: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    roles = state.get("roles", [])
    goal = str(state.get("goal", ""))
    requests: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    seen_agents: set[tuple[str, str]] = set()

    for blueprint in STAGE_AGENT_BLUEPRINTS:
        agent_type = blueprint["agent_type"]
        key = (blueprint["stage"], agent_type)
        if key in seen_agents:
            continue
        seen_agents.add(key)
        available = agent_manifest_exists(agent_type)
        if not available:
            missing.append(
                {
                    "needed_for": blueprint["stage"],
                    "agent_type": agent_type,
                    "reason": "No installed agent manifest found",
                    "suggested_action": "create_agent_manifest",
                }
            )
        requests.append(build_agent_request(state, blueprint, available=available))

    for role in roles:
        role_id = str(role.get("id", ""))
        if role_id in {"sentinel", "orchestrator", "research_director", "research_synthesizer", "research_methodologist", "architect", "builder", "reviewer", "runtime_auditor", "security_auditor"}:
            continue
        agent_type = str(role.get("owner", ""))
        stage = "parallel_implementation" if role.get("kind") == "worker" else "verification"
        if role_id.startswith("devops") or role_id.startswith("sre"):
            stage = "deployment_readiness"
        if role_id.startswith("database") or role_id.startswith("payment") or role_id.startswith("security"):
            stage = "security_review"
        key = (stage, agent_type)
        if key in seen_agents:
            continue
        seen_agents.add(key)
        blueprint = {
            "id": role_id,
            "stage": stage,
            "agent_type": agent_type,
            "kind": role.get("kind", "worker"),
            "owned_paths": [],
            "success_criteria": [str(role.get("purpose", "surface-specific delivery"))],
        }
        available = agent_manifest_exists(agent_type)
        if not available:
            missing.append(
                {
                    "needed_for": stage,
                    "agent_type": agent_type,
                    "reason": f"Dynamic role {role_id} has no installed manifest",
                    "suggested_action": "create_agent_manifest",
                }
            )
        requests.append(build_agent_request(state, blueprint, available=available))

    for foundry in foundry_roles(goal):
        if foundry.get("manifest_exists"):
            continue
        missing.append(
            {
                "needed_for": "parallel_implementation",
                "agent_type": foundry["proposed_agent"],
                "reason": f"Goal includes uncovered capability: {foundry['id']}",
                "purpose": foundry["purpose"],
                "suggested_action": "create_agent_manifest",
                "proposed_manifest": proposed_manifest(foundry["proposed_agent"], foundry["purpose"]),
            }
        )

    return requests, missing


def build_agent_request(state: dict[str, Any], blueprint: dict[str, Any], *, available: bool) -> dict[str, Any]:
    request_id = f"{blueprint['stage']}::{blueprint['id']}"
    prompt_path = f"SOT/service-factory/agent-prompts/{request_id.replace('::', '--')}.md"
    return {
        "id": request_id,
        "stage": blueprint["stage"],
        "agent_type": blueprint["agent_type"],
        "kind": blueprint["kind"],
        "status": "queued",
        "available": available,
        "owned_paths": blueprint.get("owned_paths", []),
        "success_criteria": blueprint.get("success_criteria", []),
        "prompt_path": prompt_path,
        "spawn_policy": "spawn_when_stage_unblocked" if available else "foundry_required_before_spawn",
    }


def build_agent_blueprints_from_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Represent task-scoped specialist designs separately from spawned work."""
    blueprints: list[dict[str, Any]] = []
    seen: set[str] = set()
    for request in state.get("agent_requests", []):
        if not isinstance(request, dict) or not request.get("id"):
            continue
        request_id = str(request.get("id"))
        seen.add(request_id)
        available = bool(request.get("available"))
        blueprints.append(
            {
                "id": request_id,
                "stage": request.get("stage"),
                "agent_type": request.get("agent_type"),
                "kind": request.get("kind"),
                "source": "agent_request",
                "available": available,
                "manifest_status": "installed_or_builtin" if available else "missing_manifest",
                "prompt_path": request.get("prompt_path"),
                "owned_paths": request.get("owned_paths", []),
                "success_criteria": request.get("success_criteria", []),
                "definition": "Task-scoped AgentBlueprint; not an AgentInstance until a spawn/run/result exists.",
            }
        )

    for item in state.get("missing_capabilities", []):
        if not isinstance(item, dict):
            continue
        agent_type = str(item.get("agent_type") or "")
        if not agent_type:
            continue
        blueprint_id = f"foundry::{agent_type}"
        if blueprint_id in seen:
            continue
        seen.add(blueprint_id)
        blueprints.append(
            {
                "id": blueprint_id,
                "stage": item.get("needed_for"),
                "agent_type": agent_type,
                "kind": "manifest_candidate",
                "source": "missing_capability",
                "available": False,
                "manifest_status": "proposed_manifest" if item.get("proposed_manifest") else "missing_manifest",
                "purpose": item.get("purpose") or item.get("reason"),
                "suggested_action": item.get("suggested_action"),
                "definition": "Reusable AgentManifest candidate requested by Stella when the goal needs an uncovered specialist.",
            }
        )
    return blueprints


def build_agent_instances_from_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Represent actual spawned/running/completed work separately from blueprints."""
    instances: list[dict[str, Any]] = []
    request_by_id = {
        str(request.get("id")): request
        for request in state.get("agent_requests", [])
        if isinstance(request, dict) and request.get("id")
    }
    for result in state.get("agent_results", []):
        if not isinstance(result, dict):
            continue
        request_id = str(result.get("request_id") or "")
        if not request_id:
            continue
        instance_id = str(result.get("instance_id") or f"{result.get('run_id') or 'run'}::{request_id}")
        request = request_by_id.get(request_id, {})
        instances.append(
            {
                "id": instance_id,
                "blueprint_id": request_id,
                "request_id": request_id,
                "agent_type": result.get("agent_type") or request.get("agent_type"),
                "runtime": result.get("backend") or state.get("runtime", {}).get("backend"),
                "run_id": result.get("run_id"),
                "status": result.get("status"),
                "artifact_dir": result.get("artifact_dir"),
                "artifact_paths": result.get("artifact_paths", []),
                "evidence_class": result.get("evidence_class")
                or (result.get("child_result") if isinstance(result.get("child_result"), dict) else {}).get("evidence_class"),
                "failure_category": result.get("failure_category"),
                "definition": "Actual AgentInstance evidence from a run/result artifact.",
            }
        )

    runtime = state.get("runtime") if isinstance(state.get("runtime"), dict) else {}
    for request in state.get("agent_requests", []):
        if not isinstance(request, dict) or request.get("status") not in {"dispatched", "running"}:
            continue
        request_id = str(request.get("id") or "")
        if not request_id:
            continue
        run_id_value = request.get("last_run_id") or runtime.get("last_run_id") or "pending"
        instance_id = f"{run_id_value}::{request_id}"
        if any(instance.get("id") == instance_id for instance in instances):
            continue
        instances.append(
            {
                "id": instance_id,
                "blueprint_id": request_id,
                "request_id": request_id,
                "agent_type": request.get("agent_type"),
                "runtime": runtime.get("backend") or "codex_bridge",
                "run_id": run_id_value,
                "status": request.get("status"),
                "artifact_dir": request.get("artifact_dir"),
                "artifact_paths": request.get("artifacts", []),
                "definition": "In-flight AgentInstance reserved by dispatch/run state.",
            }
        )
    return instances


def build_agent_topology(state: dict[str, Any]) -> dict[str, Any]:
    blueprints = build_agent_blueprints_from_state(state)
    instances = build_agent_instances_from_state(state)
    blueprint_nodes = [
        {
            "id": f"blueprint:{blueprint.get('id')}",
            "type": "AgentBlueprint",
            "agent_type": blueprint.get("agent_type"),
            "stage": blueprint.get("stage"),
            "manifest_status": blueprint.get("manifest_status"),
        }
        for blueprint in blueprints
    ]
    instance_nodes = [
        {
            "id": f"instance:{instance.get('id')}",
            "type": "AgentInstance",
            "blueprint_id": instance.get("blueprint_id"),
            "status": instance.get("status"),
            "runtime": instance.get("runtime"),
        }
        for instance in instances
    ]
    return {
        "version": "stella-factory-agent-topology-v1",
        "command_owner": STELLA_COMMAND_OWNER,
        "execution_controller": RELEASE_EXECUTION_CONTROLLER,
        "source_of_truth": "SOT/service-factory-state.json",
        "kanban_role": "projection_only",
        "agent_creation_rule": "AgentBlueprint designs specialists; AgentInstance proves a spawned/run unit; AgentManifest is only reusable after a manifest exists.",
        "not_agent_creation": [
            "prompt file only",
            "worktree path only",
            "result file only without a blueprint/instance link",
            "kanban card only",
        ],
        "layers": [
            {
                "id": "command",
                "owner": STELLA_COMMAND_OWNER,
                "responsibility": "goal normalization, AgentTopology, final readiness decision",
            },
            {
                "id": "runtime",
                "owner": RELEASE_EXECUTION_CONTROLLER,
                "responsibility": "state ledger, dispatch, collect, gates, handoff, recovery",
            },
            {
                "id": "specialists",
                "owner": "AgentBlueprint/AgentInstance",
                "responsibility": "bounded research, implementation, review, Probe, security, release audit",
            },
        ],
        "blueprint_count": len(blueprints),
        "instance_count": len(instances),
        "manifest_candidates": [
            blueprint
            for blueprint in blueprints
            if blueprint.get("manifest_status") in {"missing_manifest", "proposed_manifest"}
        ],
        "nodes": [
            {"id": "stella", "type": "CommandOwner", "owner": STELLA_COMMAND_OWNER},
            {"id": "release", "type": "ExecutionController", "owner": RELEASE_EXECUTION_CONTROLLER},
            *blueprint_nodes,
            *instance_nodes,
        ],
        "edges": [
            {"from": "stella", "to": "release", "relationship": "commands_runtime_adapter"},
            *[
                {
                    "from": "stella",
                    "to": f"blueprint:{blueprint.get('id')}",
                    "relationship": "authorizes_specialist_blueprint",
                }
                for blueprint in blueprints
            ],
            *[
                {
                    "from": "release",
                    "to": f"instance:{instance.get('id')}",
                    "relationship": "dispatches_or_collects_instance",
                }
                for instance in instances
            ],
        ],
    }


def ensure_stella_control_plane(state: dict[str, Any]) -> bool:
    changed = False

    def set_if_changed(container: dict[str, Any], key: str, value: Any) -> None:
        nonlocal changed
        if container.get(key) != value:
            container[key] = value
            changed = True

    set_if_changed(state, "command_owner", STELLA_COMMAND_OWNER)
    set_if_changed(
        state,
        "control_plane",
        {
            "command_owner": STELLA_COMMAND_OWNER,
            "execution_controller": RELEASE_EXECUTION_CONTROLLER,
            "state_role": "StateLedger + Release runtime adapter",
            "board_role": "KanbanProjection only",
            "source_of_truth": "SOT/service-factory-state.json",
        },
    )
    set_if_changed(
        state,
        "kanban_projection",
        {
            "role": "projection_only",
            "source": "SOT/service-factory-state.json",
            "truth_rule": "Kanban cards may visualize queues, but cannot replace Stella command_owner or AgentTopology evidence.",
        },
    )

    run_log = state.get("run_log")
    if not isinstance(run_log, dict):
        run_log = {}
        state["run_log"] = run_log
        changed = True
    set_if_changed(run_log, "command_owner", STELLA_COMMAND_OWNER)
    set_if_changed(run_log, "current_owner", STELLA_COMMAND_OWNER)
    set_if_changed(run_log, "execution_controller", RELEASE_EXECUTION_CONTROLLER)

    blueprints = build_agent_blueprints_from_state(state)
    if state.get("agent_blueprints") != blueprints:
        state["agent_blueprints"] = blueprints
        changed = True
    instances = build_agent_instances_from_state(state)
    if state.get("agent_instances") != instances:
        state["agent_instances"] = instances
        changed = True
    topology = build_agent_topology(state)
    if state.get("agent_topology") != topology:
        state["agent_topology"] = topology
        changed = True
    return changed


def merge_agent_requests(existing: list[Any], fresh: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_by_id = {
        str(request.get("id")): request
        for request in existing
        if isinstance(request, dict) and request.get("id")
    }
    preserved_fields = {
        "status",
        "last_run_id",
        "started_at",
        "finished_at",
        "worktree_path",
        "dispatch_path",
        "dispatch_json",
        "artifact_dir",
        "artifacts",
        "modified_files",
        "commands_run",
        "failure_class",
        "next_step",
        "validation_resolved_at",
        "validation_evidence",
        "validation_note",
    }
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for request in fresh:
        request_id = str(request.get("id"))
        previous = existing_by_id.get(request_id, {})
        combined = {**request}
        for field in preserved_fields:
            if field in previous:
                combined[field] = previous[field]
        merged.append(combined)
        seen.add(request_id)
    return merged


def proposed_manifest(name: str, purpose: str) -> str:
    return "\n".join(
        [
            f'name = "{name}"',
            f'description = "Use when a task needs {purpose.lower()}"',
            'model = "gpt-5.4"',
            'model_reasoning_effort = "high"',
            'sandbox_mode = "workspace-write"',
            'developer_instructions = """',
            purpose,
            "",
            "Working mode:",
            "1. Map the exact boundary and owned files for the requested capability.",
            "2. Implement or review only the scoped capability.",
            "3. Return changed files, commands run, evidence, residual risks, and handoff notes.",
            "",
            "Do not perform DB/data deletion, production deploys, paid API expansion, external communication, or offensive testing unless the parent agent provides explicit approval and scope.",
            '"""',
        ]
    )


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_operating_contract(state)
    ensure_stella_control_plane(state)
    state["updated_at"] = now_iso()
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.{datetime.now().strftime('%Y%m%d%H%M%S%f')}.tmp")
    tmp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def project_sot_dir(state: dict[str, Any]) -> Path:
    return Path(state["project"]["path"]) / "SOT" / "service-factory"


def bridge_dir(state: dict[str, Any]) -> Path:
    return project_sot_dir(state) / "bridge"


def prompt_for_request(state: dict[str, Any], request: dict[str, Any]) -> str:
    constraints = state.get("constraints", {})
    return f"""# Service Factory Agent Request

factory_id: {state.get("factory_id")}
stage: {request.get("stage")}
role: {request.get("kind")}
agent_type: {request.get("agent_type")}
status: {request.get("status")}
command_owner: {state.get("command_owner", STELLA_COMMAND_OWNER)}
execution_controller: {state.get("run_log", {}).get("execution_controller", RELEASE_EXECUTION_CONTROLLER)}

## Goal
{state.get("goal")}

## Mandatory Working Method
Every development request must follow this order:

1. Current state discovery: inspect the actual repo, runtime, SOT, dirty paths,
   installed/build state, capabilities, constraints, and verification baseline.
2. Research intelligence: use K-Dense/research agents to gather evidence,
   map sources, generate hypotheses/counter-hypotheses, and record research QC.
3. Goal-to-plan strategy: explain the gap from current state and research evidence
   to the target, then define task packets with owner, owned paths, done_when,
   verification, and rollback/retry criteria.
4. Execution and verification loop: implement only the scoped task packet,
   integrate, verify, and loop back to the plan when evidence fails.

Do not begin broad implementation before current-state, research, and development-plan
evidence exists. If the task is narrow enough to execute directly, state that
it is a narrow one-shot and still record the baseline and verification evidence.

Stella is the command owner. Release is the runtime adapter/state ledger for
dispatch, collect, gates, handoff, and recovery. Treat this request as an
AgentBlueprint until an actual run/result creates an AgentInstance.

## Owned Paths
{json.dumps(request.get("owned_paths", []), ensure_ascii=False, indent=2)}

## Success Criteria
{json.dumps(request.get("success_criteria", []), ensure_ascii=False, indent=2)}

## Forbidden Without Explicit User Approval
- DB/data deletion
- destructive migrations or volume deletion
- production deploy or production data writes
- paid API budget expansion
- external communication as the user/company
- offensive security testing or broad scanning

## Approval Gates
{json.dumps(constraints, ensure_ascii=False, indent=2)}

## Required Return Shape
Return JSON-compatible handoff fields:
- status: done|blocked|validation_required
- modified_files
- commands_run with exit codes
- artifacts
- findings or risks
- next_step

Do not mark the work done from self-check only. If independent verification is missing, use validation_required.
"""


def write_agent_prompts(state_path: Path, state: dict[str, Any]) -> list[str]:
    base = state_path.parent / "service-factory" / "agent-prompts"
    base.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for request in state.get("agent_requests", []):
        prompt_rel = str(request.get("prompt_path", ""))
        prompt_path = safe_project_relative_path(Path(state["project"]["path"]), prompt_rel)
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_for_request(state, request), encoding="utf-8")
        written.append(str(prompt_path))
    return written


def append_progress(state: dict[str, Any], event: dict[str, Any]) -> Path:
    out_dir = project_sot_dir(state)
    out_dir.mkdir(parents=True, exist_ok=True)
    progress_path = out_dir / "progress.jsonl"
    payload = {"timestamp": now_iso(), "factory_id": state.get("factory_id"), **event}
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return progress_path


def write_handoff_files(state: dict[str, Any], state_path: Path) -> tuple[Path, Path]:
    out_dir = project_sot_dir(state)
    out_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = out_dir / "handoff-latest.md"
    handoff_path.write_text(render_handoff(state, state_path), encoding="utf-8")
    progress_path = out_dir / "progress.jsonl"
    progress = {
        "timestamp": now_iso(),
        "factory_id": state.get("factory_id"),
        "status": state.get("status"),
        "handoff": str(handoff_path),
        "blocked_reason": state.get("run_log", {}).get("blocked_reason"),
        "next_step": state.get("run_log", {}).get("next_step"),
    }
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(progress, ensure_ascii=False) + "\n")
    state["artifacts"] = sorted(set(state.get("artifacts", []) + [str(handoff_path), str(progress_path)]))
    return handoff_path, progress_path


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": now_iso(), **event}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def command_gate_block(command: str) -> tuple[str | None, str | None]:
    for gate, pattern in SENSITIVE_COMMAND_RULES:
        if pattern.search(command):
            if gate == "destructive_filesystem":
                return gate, "destructive filesystem command blocked"
            return gate, f"command requires approval gate: {gate}"
    return None, None


def gate_approved(state: dict[str, Any], gate_id: str) -> bool:
    for gate in state.get("gates", []):
        if isinstance(gate, dict) and gate.get("id") == gate_id:
            return gate.get("status") == "approved" and bool(gate.get("evidence"))
    return False


def command_allowed(state: dict[str, Any], command: str) -> tuple[bool, str | None, str | None]:
    gate_id, reason = command_gate_block(command)
    if not gate_id:
        return True, None, None
    if gate_id == "destructive_filesystem":
        return False, "unsafe_request", reason
    if gate_id == "db_data_deletion":
        return False, "unsafe_request", reason
    if gate_approved(state, gate_id):
        return True, None, None
    return False, "permission_blocked", reason


def executable_allowed(argv: list[str]) -> tuple[bool, str | None, str | None]:
    if not argv:
        return False, "unsafe_request", "empty command argv is not allowed"
    executable = Path(argv[0]).name
    if executable == "codex":
        return True, None, None
    if executable in {"git", "rg", "sed", "ls", "tail", "head", "wc"}:
        return True, None, None
    if executable in INTERPRETER_EXECUTABLES:
        if len(argv) < 2:
            return False, "unsafe_request", f"{executable} requires an approved script path"
        if argv[1].startswith("-"):
            return False, "unsafe_request", f"{executable} inline or option-based execution is not allowed"
        script_path = Path(argv[1]).expanduser()
        try:
            script_path = script_path.resolve()
        except OSError:
            return False, "unsafe_request", f"{executable} script path cannot be resolved"
        if executable.startswith("python") and script_path in {path.resolve() for path in ALLOWED_PYTHON_SCRIPTS}:
            return True, None, None
        return False, "unsafe_request", f"{executable} may only run approved Service Factory scripts"
    return False, "unsafe_request", f"executable is not allowlisted: {executable}"


def is_git_worktree(project: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--is-inside-work-tree"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def prepare_request_workspace(project: Path, request: dict[str, Any], *, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"mode": "project", "path": str(project), "created": False, "note": "worktree preparation disabled"}
    if not is_git_worktree(project):
        return {"mode": "project_no_git", "path": str(project), "created": False, "note": "project is not a git worktree"}

    worktree_root = project / ".service-factory" / "worktrees"
    worktree_path = worktree_root / slug(str(request.get("id", "request")))
    if worktree_path.exists():
        return {"mode": "existing_worktree", "path": str(worktree_path), "created": False, "note": "worktree path already exists"}

    worktree_root.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "-C", str(project), "worktree", "add", "--detach", str(worktree_path), "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        return {
            "mode": "git_worktree",
            "path": str(worktree_path),
            "created": True,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    return {
        "mode": "project_worktree_failed",
        "path": str(project),
        "created": False,
        "note": "git worktree add failed; using project path",
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def render_agent_launcher(state: dict[str, Any], request: dict[str, Any], workspace: dict[str, Any], artifact_dir: Path) -> str:
    prompt_path = Path(state["project"]["path"]) / str(request.get("prompt_path", ""))
    return f"""# Agent Launch Instructions

factory_id: {state.get("factory_id")}
request_id: {request.get("id")}
agent_type: {request.get("agent_type")}
backend: manual
workspace: {workspace.get("path")}
prompt_file: {prompt_path}
artifact_dir: {artifact_dir}

## Action
Spawn the requested agent with the prompt file above. The agent must write its result as JSON-compatible handoff fields and preserve stdout/stderr/tool evidence under this artifact directory.

## Required Result Fields
- status: done|blocked|validation_required
- modified_files
- commands_run with exit codes
- artifacts
- findings_or_risks
- next_step

## Guardrails
Do not perform DB/data deletion, destructive filesystem deletion, production deployment, paid API budget expansion, external communication, or offensive security testing unless the state file has an explicit approved gate with evidence.
"""


def render_bridge_dispatch(state_path: Path, state: dict[str, Any], request: dict[str, Any], workspace: dict[str, Any], artifact_dir: Path) -> str:
    prompt_path = Path(state["project"]["path"]) / str(request.get("prompt_path", ""))
    result_path = artifact_dir / "result.json"
    return f"""# Service Factory Codex Bridge Dispatch

factory_id: {state.get("factory_id")}
request_id: {request.get("id")}
agent_type: {request.get("agent_type")}
stage: {request.get("stage")}
state_file: {state_path}
workspace: {workspace.get("path")}
prompt_file: {prompt_path}
artifact_dir: {artifact_dir}
result_file: {result_path}

## Mission
Complete only this Service Factory request. You are not alone in the codebase. Do not revert unrelated changes, and keep your work inside the assigned workspace and owned paths.

## Source Prompt
Read the prompt file above first. It contains the goal, owned paths, success criteria, forbidden actions, and required return shape.

## Required Output
Write `{result_path}` with JSON:

```json
{{
  "status": "done|blocked|validation_required|failed",
  "modified_files": [],
  "commands_run": [],
  "artifacts": [],
  "findings_or_risks": [],
  "failure_category": null,
  "next_step": ""
}}
```

## Guardrails
- Do not perform DB/data deletion.
- Do not run destructive filesystem commands.
- Do not deploy to production.
- Do not expand paid API budget.
- Do not communicate externally as the user/company.
- Do not run offensive security testing or broad scanning.
- If independent verification is missing, set `status` to `validation_required`.
"""


def safe_env() -> dict[str, str]:
    keep = {"PATH", "HOME", "LANG", "LC_ALL", "TERM", "TMPDIR"}
    deny_fragments = (
        "TOKEN",
        "SECRET",
        "PASSWORD",
        "PASSWD",
        "API_KEY",
        "PRIVATE_KEY",
        "ACCESS_KEY",
        "SESSION",
        "COOKIE",
        "CREDENTIAL",
        "AUTH",
        "SSH_",
        "AWS_",
        "GCP_",
        "GOOGLE_",
        "CLOUD",
        "OPENAI_",
        "ANTHROPIC_",
        "GITHUB_",
        "GH_",
        "STRIPE_",
    )
    env: dict[str, str] = {}
    for key, value in os.environ.items():
        upper = key.upper()
        if key in keep and not any(fragment in upper for fragment in deny_fragments):
            env[key] = value
    env["CI"] = "1"
    env["SERVICE_FACTORY_RUN"] = "1"
    env.pop("SSH_AUTH_SOCK", None)
    return env


def has_shell_operators(argv: list[str]) -> bool:
    operators = {";", "&", "|", ">", "<", "&&", "||", "$(", "`"}
    return any(token in operators or "$(" in token or "`" in token for token in argv)


def command_text(argv: list[str]) -> str:
    return shlex.join(argv)


def format_agent_argv(template: str, state_path: Path, state: dict[str, Any], request: dict[str, Any], workspace: dict[str, Any], artifact_dir: Path, run_id_value: str) -> list[str]:
    project = Path(state["project"]["path"])
    prompt_file = project / str(request.get("prompt_path", ""))
    values = {
        "prompt_file": shlex.quote(str(prompt_file)),
        "artifact_dir": shlex.quote(str(artifact_dir)),
        "request_id": shlex.quote(str(request.get("id", ""))),
        "agent_type": shlex.quote(str(request.get("agent_type", ""))),
        "worktree": shlex.quote(str(workspace.get("path", project))),
        "state_file": shlex.quote(str(state_path)),
        "project": shlex.quote(str(project)),
        "run_id": shlex.quote(run_id_value),
    }
    return shlex.split(template.format(**values))


def execute_argv(argv: list[str], cwd: Path, stdout_path: Path, stderr_path: Path, timeout_seconds: int, input_text: str | None = None) -> dict[str, Any]:
    started_at = now_iso()
    try:
        result = subprocess.run(
            argv,
            cwd=str(cwd),
            shell=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=safe_env(),
            input=input_text,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text(exc.stderr or f"Timed out after {timeout_seconds}s", encoding="utf-8")
        return {
            "status": "failed",
            "failure_category": "command_timeout",
            "exit_code": None,
            "started_at": started_at,
            "ended_at": now_iso(),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }

    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    return {
        "status": "completed" if result.returncode == 0 else "failed",
        "failure_category": None if result.returncode == 0 else "command_failed",
        "exit_code": result.returncode,
        "started_at": started_at,
        "ended_at": now_iso(),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }


def load_child_result(artifact_dir: Path) -> dict[str, Any] | None:
    result_path = artifact_dir / "result.json"
    if not result_path.exists():
        return None
    with result_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{result_path} root must be an object")
    payload["_result_path"] = str(result_path)
    return payload


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def resolve_project_path(raw_path: str, project: Path) -> Path:
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else project / path


def safe_project_relative_path(project: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        raise ValueError(f"path must be relative to project: {raw_path}")
    resolved = (project / path).resolve()
    project_root = project.resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {raw_path}") from exc
    return resolved


def artifact_paths_from_child(child_result: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for artifact in child_result.get("artifacts", []):
        if isinstance(artifact, str):
            paths.append(artifact)
        elif isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
            paths.append(str(artifact["path"]))
    return paths


def findings_from_child(child_result: dict[str, Any]) -> list[str]:
    findings = child_result.get("findings_or_risks", child_result.get("findings", []))
    if isinstance(findings, list):
        return [str(item) for item in findings]
    if findings:
        return [str(findings)]
    return []


def validate_child_result_trust(
    project: Path,
    request: dict[str, Any],
    artifact_dir: Path,
    child_result: dict[str, Any],
    expected_run_id: str | None = None,
) -> list[str]:
    issues: list[str] = []
    expected_request_id = str(request.get("id", ""))
    child_request_id = child_result.get("request_id")
    if child_request_id != expected_request_id:
        issues.append("child result request_id does not match request")
    if expected_run_id and child_result.get("run_id") != expected_run_id:
        issues.append("child result run_id does not match run")
    child_artifact_dir = child_result.get("artifact_dir")
    if child_artifact_dir:
        child_artifact_path = Path(str(child_artifact_dir)).expanduser()
        try:
            if child_artifact_path.resolve() != artifact_dir.resolve():
                issues.append("child result artifact_dir does not match expected artifact directory")
        except OSError:
            issues.append("child result artifact_dir cannot be resolved")
    else:
        issues.append("child result artifact_dir is missing")
    if not child_result_has_collectable_evidence(child_result):
        issues.append("child result has no collectable evidence")

    owned_roots: list[Path] = []
    for raw_path in request.get("owned_paths", []):
        if isinstance(raw_path, str):
            owned_roots.append(resolve_project_path(raw_path, project))

    modified_files = child_result.get("modified_files", [])
    if modified_files is not None and not isinstance(modified_files, list):
        issues.append("modified_files must be a list")
    elif isinstance(modified_files, list):
        for raw_path in modified_files:
            if not isinstance(raw_path, str):
                issues.append("modified_files entries must be strings")
                continue
            path = resolve_project_path(raw_path, project)
            if path.name == "result.json" and path_is_within(path, artifact_dir):
                continue
            if path_is_within(path, artifact_dir):
                continue
            if owned_roots and not any(path_is_within(path, root) or path.resolve() == root.resolve() for root in owned_roots):
                issues.append(f"modified file outside owned paths: {raw_path}")

    artifacts = child_result.get("artifacts", [])
    if artifacts is not None and not isinstance(artifacts, list):
        issues.append("artifacts must be a list")
    else:
        for raw_path in artifact_paths_from_child(child_result):
            path = resolve_project_path(raw_path, project)
            if not (path_is_within(path, project) or path_is_within(path, artifact_dir)):
                issues.append(f"artifact outside project/artifact directory: {raw_path}")
            if not path.exists():
                issues.append(f"artifact does not exist: {raw_path}")

    commands_run = child_result.get("commands_run", [])
    if commands_run is not None and not isinstance(commands_run, list):
        issues.append("commands_run must be a list")
    elif isinstance(commands_run, list):
        for index, command in enumerate(commands_run):
            if not isinstance(command, dict):
                issues.append(f"commands_run[{index}] must be an object")
                continue
            if not isinstance(command.get("argv"), list):
                issues.append(f"commands_run[{index}] missing argv list")
            if command.get("returncode") is None and command.get("exit_code") is None:
                issues.append(f"commands_run[{index}] missing returncode or exit_code")
    return issues


def normalize_child_status(status: Any, exit_status: str) -> tuple[str, str]:
    normalized = str(status or "").strip().lower()
    if exit_status != "completed" and normalized != "blocked":
        return "failed", "failed"
    if normalized in {"done", "completed", "pass", "passed"}:
        return "completed", "completed"
    if normalized in {"blocked"}:
        return "blocked", "blocked"
    if normalized in {"validation_required", "needs_validation", "review_required"}:
        return "validation_required", "validation_required"
    if normalized in {"failed", "failure", "error"}:
        return "failed", "failed"
    if exit_status == "completed":
        return "validation_required", "validation_required"
    return "failed", "failed"


def child_result_has_collectable_evidence(result: dict[str, Any]) -> bool:
    status = str(result.get("status", "")).strip().lower()
    if status in {"done", "completed", "pass", "passed"}:
        modified_files = result.get("modified_files")
        commands_run = result.get("commands_run")
        artifacts = result.get("artifacts")
        findings = result.get("findings_or_risks")
        if (isinstance(modified_files, list) and modified_files):
            return True
        if isinstance(commands_run, list) and commands_run:
            return True
        if isinstance(artifacts, list) and artifacts:
            return True
        if isinstance(findings, list) and findings:
            return True
    return False


def request_dependencies_done(state: dict[str, Any], request: dict[str, Any]) -> bool:
    stage_id = request.get("stage")
    stages = {stage.get("id"): stage for stage in state.get("stages", []) if isinstance(stage, dict)}
    stage = stages.get(stage_id)
    if not stage:
        return True
    for dependency in stage.get("depends_on", []):
        dependency_stage = stages.get(dependency)
        if dependency_stage and dependency_stage.get("state") != "done":
            return False
    return True


def advance_intake_stage(state: dict[str, Any]) -> None:
    for stage in state.get("stages", []):
        if isinstance(stage, dict) and stage.get("id") == "intake" and stage.get("state") == "in_progress":
            stage["state"] = "done"
            stage["artifacts"] = sorted(set(stage.get("artifacts", []) + ["service-factory:intake-state"]))
            return


def update_stage_states_from_requests(state: dict[str, Any]) -> None:
    requests_by_stage: dict[str, list[dict[str, Any]]] = {}
    for request in state.get("agent_requests", []):
        if isinstance(request, dict):
            requests_by_stage.setdefault(str(request.get("stage")), []).append(request)

    result_artifacts = [
        artifact
        for result in state.get("agent_results", [])
        if isinstance(result, dict)
        for artifact in result.get("artifact_paths", [])
    ]
    for stage in state.get("stages", []):
        if not isinstance(stage, dict):
            continue
        stage_id = str(stage.get("id"))
        stage_requests = requests_by_stage.get(stage_id, [])
        if not stage_requests:
            continue
        statuses = {str(request.get("status")) for request in stage_requests}
        if "blocked" in statuses:
            stage["state"] = "blocked"
        elif "validation_required" in statuses:
            stage["state"] = "validation_required"
        elif "failed" in statuses:
            stage["state"] = "validation_required"
        elif statuses and statuses <= {"completed"}:
            stage["state"] = "done"
            stage["artifacts"] = sorted(set(stage.get("artifacts", []) + result_artifacts))
        elif "running" in statuses:
            stage["state"] = "in_progress"
        elif "queued" in statuses:
            stage["state"] = "queued"


def select_requests_to_run(state: dict[str, Any], request_id: str | None, max_requests: int | None, include_unavailable: bool) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for request in state.get("agent_requests", []):
        if not isinstance(request, dict):
            continue
        if request_id and request.get("id") != request_id:
            continue
        if request.get("status") not in {"queued", "failed", "validation_required"}:
            continue
        if not include_unavailable and not request.get("available"):
            continue
        if not request_dependencies_done(state, request):
            continue
        selected.append(request)
        if max_requests is not None and len(selected) >= max_requests:
            break
    return selected


def run_agent_request(
    state_path: Path,
    state: dict[str, Any],
    request: dict[str, Any],
    *,
    backend: str,
    command_template: str | None,
    run_id_value: str,
    timeout_seconds: int,
    prepare_worktrees: bool,
    allow_paid_agent_call: bool = False,
) -> dict[str, Any]:
    project = Path(state["project"]["path"])
    artifact_dir = canonical_artifact_dir(project, request, run_id_value)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    events_path = artifact_dir / "events.jsonl"
    workspace = prepare_request_workspace(project, request, enabled=prepare_worktrees)
    launcher_path = artifact_dir / "agent-launch.md"
    launcher_path.write_text(render_agent_launcher(state, request, workspace, artifact_dir), encoding="utf-8")
    request["status"] = "running"
    request["last_run_id"] = run_id_value
    request["worktree_path"] = workspace.get("path")
    append_event(events_path, {"event": "request_started", "request_id": request.get("id"), "backend": backend, "workspace": workspace})

    result: dict[str, Any] = {
        "run_id": run_id_value,
        "request_id": request.get("id"),
        "agent_type": request.get("agent_type"),
        "backend": backend,
        "status": "validation_required",
        "failure_category": "spawn_backend_missing",
        "started_at": now_iso(),
        "ended_at": None,
        "worktree": workspace,
        "prompt_path": str(project / str(request.get("prompt_path", ""))),
        "artifact_dir": str(artifact_dir),
        "artifact_paths": [str(launcher_path), str(events_path)],
        "command": None,
        "exit_code": None,
    }

    if backend == "manual":
        result["ended_at"] = now_iso()
        result["note"] = "manual backend wrote launch instructions but did not spawn an agent"
        request["status"] = "blocked"
        append_event(events_path, {"event": "request_blocked", "reason": result["failure_category"]})
        return result

    if backend == "command":
        if not command_template:
            result["status"] = "blocked"
            result["ended_at"] = now_iso()
            result["failure_category"] = "spawn_backend_missing"
            result["note"] = "--agent-command-template is required for command backend"
            request["status"] = "blocked"
            append_event(events_path, {"event": "request_blocked", "reason": result["note"]})
            return result
        argv = format_agent_argv(command_template, state_path, state, request, workspace, artifact_dir, run_id_value)
        command = command_text(argv)
        allowed, failure_category, reason = command_allowed(state, command)
        if has_shell_operators(argv):
            allowed, failure_category, reason = False, "unsafe_request", "shell operators are not allowed in agent command templates"
        executable_ok, executable_failure, executable_reason = executable_allowed(argv)
        if allowed and not executable_ok:
            allowed, failure_category, reason = False, executable_failure, executable_reason
        result["command"] = command
        result["argv"] = argv
        if not allowed:
            result["status"] = "blocked"
            result["ended_at"] = now_iso()
            result["failure_category"] = failure_category or "permission_blocked"
            result["note"] = reason
            request["status"] = "blocked"
            append_event(events_path, {"event": "request_blocked", "reason": reason, "command": command})
            return result
        stdout_path = artifact_dir / "stdout.txt"
        stderr_path = artifact_dir / "stderr.txt"
        append_event(events_path, {"event": "command_started", "command": command})
        command_result = execute_argv(argv, Path(str(workspace.get("path", project))), stdout_path, stderr_path, timeout_seconds)
        result.update(command_result)
        result["artifact_paths"].extend([str(stdout_path), str(stderr_path)])
        child_result = load_child_result(artifact_dir)
        if child_result:
            result["child_result"] = child_result
            result["artifact_paths"].append(str(child_result["_result_path"]))
            result_status, request_status = normalize_child_status(child_result.get("status"), command_result["status"])
            trust_issues = validate_child_result_trust(project, request, artifact_dir, child_result, run_id_value) if result_status == "completed" else []
            if trust_issues:
                result_status = "validation_required"
                request_status = "validation_required"
            result["status"] = result_status
            result["failure_category"] = "child_result_trust_boundary" if trust_issues else child_result.get("failure_category") or result.get("failure_category")
            result["modified_files"] = child_result.get("modified_files", [])
            result["commands_run"] = child_result.get("commands_run", [])
            result["findings_or_risks"] = findings_from_child(child_result) + trust_issues
            result["next_step"] = child_result.get("next_step")
            for artifact in artifact_paths_from_child(child_result):
                result["artifact_paths"].append(artifact)
        elif command_result["status"] == "completed":
            result["status"] = "validation_required"
            result["failure_category"] = None
            result["note"] = "command exited 0 but did not write artifact_dir/result.json"
            request_status = "validation_required"
        else:
            request_status = "failed"
        request["status"] = request_status
        request["finished_at"] = result.get("ended_at")
        request["artifacts"] = sorted(set(request.get("artifacts", []) + result["artifact_paths"]))
        request["commands_run"] = [{"argv": argv, "exit_code": result.get("exit_code"), "stdout_path": str(stdout_path), "stderr_path": str(stderr_path)}]
        request["failure_class"] = result.get("failure_category")
        request["next_step"] = result.get("next_step")
        append_event(events_path, {"event": "command_finished", "status": result["status"], "request_status": request["status"], "exit_code": result["exit_code"]})
        return result

    if backend == "codex-exec":
        if not allow_paid_agent_call:
            result["status"] = "blocked"
            result["ended_at"] = now_iso()
            result["failure_category"] = "permission_blocked"
            result["note"] = "codex-exec backend requires --allow-paid-agent-call"
            request["status"] = "blocked"
            append_event(events_path, {"event": "request_blocked", "reason": result["note"]})
            return result
        dispatch_text = render_bridge_dispatch(state_path, state, request, workspace, artifact_dir)
        dispatch_path = artifact_dir / "codex-exec-dispatch.md"
        dispatch_path.write_text(dispatch_text, encoding="utf-8")
        stdout_path = artifact_dir / "stdout.txt"
        stderr_path = artifact_dir / "stderr.txt"
        last_message_path = artifact_dir / "last-message.md"
        argv = [
            "codex",
            "exec",
            "--cd",
            str(workspace.get("path", project)),
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--ask-for-approval",
            "never",
            "--output-last-message",
            str(last_message_path),
            "-",
        ]
        command = command_text(argv)
        allowed, failure_category, reason = command_allowed(state, command)
        executable_ok, executable_failure, executable_reason = executable_allowed(argv)
        if allowed and not executable_ok:
            allowed, failure_category, reason = False, executable_failure, executable_reason
        result["command"] = command
        result["argv"] = argv
        result["artifact_paths"].extend([str(dispatch_path), str(last_message_path)])
        if not allowed:
            result["status"] = "blocked"
            result["ended_at"] = now_iso()
            result["failure_category"] = failure_category or "permission_blocked"
            result["note"] = reason
            request["status"] = "blocked"
            append_event(events_path, {"event": "request_blocked", "reason": reason, "command": command})
            return result
        append_event(events_path, {"event": "codex_exec_started", "command": command})
        command_result = execute_argv(argv, Path(str(workspace.get("path", project))), stdout_path, stderr_path, timeout_seconds, input_text=dispatch_text)
        result.update(command_result)
        result["artifact_paths"].extend([str(stdout_path), str(stderr_path)])
        child_result = load_child_result(artifact_dir)
        if child_result:
            result["child_result"] = child_result
            result["artifact_paths"].append(str(child_result["_result_path"]))
            result_status, request_status = normalize_child_status(child_result.get("status"), command_result["status"])
            trust_issues = validate_child_result_trust(project, request, artifact_dir, child_result, run_id_value) if result_status == "completed" else []
            if trust_issues:
                result_status = "validation_required"
                request_status = "validation_required"
            result["status"] = result_status
            result["failure_category"] = "child_result_trust_boundary" if trust_issues else child_result.get("failure_category") or result.get("failure_category")
            result["modified_files"] = child_result.get("modified_files", [])
            result["commands_run"] = child_result.get("commands_run", [])
            result["findings_or_risks"] = findings_from_child(child_result) + trust_issues
            result["next_step"] = child_result.get("next_step")
            for artifact in artifact_paths_from_child(child_result):
                result["artifact_paths"].append(artifact)
        elif command_result["status"] == "completed":
            result["status"] = "validation_required"
            result["failure_category"] = None
            result["note"] = "codex exec exited 0 but did not write artifact_dir/result.json"
            request_status = "validation_required"
        else:
            request_status = "failed"
        request["status"] = request_status
        request["finished_at"] = result.get("ended_at")
        request["artifacts"] = sorted(set(request.get("artifacts", []) + result["artifact_paths"]))
        request["commands_run"] = [{"argv": argv, "exit_code": result.get("exit_code"), "stdout_path": str(stdout_path), "stderr_path": str(stderr_path)}]
        request["failure_class"] = result.get("failure_category")
        request["next_step"] = result.get("next_step")
        append_event(events_path, {"event": "codex_exec_finished", "status": result["status"], "request_status": request["status"], "exit_code": result["exit_code"]})
        return result

    result["status"] = "blocked"
    result["ended_at"] = now_iso()
    result["failure_category"] = "spawn_backend_missing"
    result["note"] = f"unknown backend: {backend}"
    request["status"] = "blocked"
    append_event(events_path, {"event": "request_blocked", "reason": result["note"]})
    return result


def dispatch_agent_request(state_path: Path, state: dict[str, Any], request: dict[str, Any], run_id_value: str, *, prepare_worktrees: bool) -> dict[str, Any]:
    project = Path(state["project"]["path"])
    safe_id = slug(str(request.get("id", "request")))
    artifact_dir = canonical_artifact_dir(project, request, run_id_value)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    events_path = artifact_dir / "events.jsonl"
    workspace = prepare_request_workspace(project, request, enabled=prepare_worktrees)
    dispatch_root = bridge_dir(state) / run_id_value / safe_id
    dispatch_root.mkdir(parents=True, exist_ok=True)
    dispatch_md_path = dispatch_root / "dispatch.md"
    dispatch_json_path = dispatch_root / "dispatch.json"
    dispatch_md_path.write_text(render_bridge_dispatch(state_path, state, request, workspace, artifact_dir), encoding="utf-8")
    dispatch_payload = {
        "factory_id": state.get("factory_id"),
        "run_id": run_id_value,
        "request_id": request.get("id"),
        "agent_type": request.get("agent_type"),
        "stage": request.get("stage"),
        "state_file": str(state_path),
        "workspace": workspace,
        "prompt_file": str(project / str(request.get("prompt_path", ""))),
        "artifact_dir": str(artifact_dir),
        "result_file": str(artifact_dir / "result.json"),
        "dispatch_markdown": str(dispatch_md_path),
    }
    dispatch_json_path.write_text(json.dumps(dispatch_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    request["status"] = "running"
    request["last_run_id"] = run_id_value
    request["worktree_path"] = workspace.get("path")
    request["dispatch_path"] = str(dispatch_md_path)
    request["artifact_dir"] = str(artifact_dir)
    append_event(events_path, {"event": "request_dispatched", "request_id": request.get("id"), "backend": "codex_bridge", "dispatch": str(dispatch_md_path), "workspace": workspace})
    return {
        "run_id": run_id_value,
        "request_id": request.get("id"),
        "agent_type": request.get("agent_type"),
        "backend": "codex_bridge",
        "status": "dispatched",
        "worktree": workspace,
        "artifact_dir": str(artifact_dir),
        "dispatch_path": str(dispatch_md_path),
        "dispatch_json": str(dispatch_json_path),
        "result_file": str(artifact_dir / "result.json"),
        "events_path": str(events_path),
    }


def collect_agent_request_result(state: dict[str, Any], request: dict[str, Any], run_id_value: str | None = None) -> dict[str, Any] | None:
    project = Path(state["project"]["path"])
    effective_run_id = run_id_value or str(request.get("last_run_id", ""))
    if not effective_run_id:
        return None
    artifact_dir = canonical_artifact_dir(project, request, effective_run_id)
    child_result = load_child_result(artifact_dir)
    if not child_result:
        return None
    result_status, request_status = normalize_child_status(child_result.get("status"), "completed")
    child_failure_category = child_result.get("failure_category")
    if result_status == "completed" and not child_result_has_collectable_evidence(child_result):
        result_status = "validation_required"
        request_status = "validation_required"
        child_failure_category = "insufficient_evidence"
    trust_issues = validate_child_result_trust(project, request, artifact_dir, child_result, effective_run_id) if result_status == "completed" else []
    if trust_issues:
        result_status = "validation_required"
        request_status = "validation_required"
        child_failure_category = "child_result_trust_boundary"
    events_path = artifact_dir / "events.jsonl"
    result = {
        "run_id": effective_run_id,
        "request_id": request.get("id"),
        "agent_type": request.get("agent_type"),
        "backend": "codex_bridge",
        "status": result_status,
        "failure_category": child_failure_category,
        "started_at": request.get("started_at"),
        "ended_at": now_iso(),
        "worktree": {"path": request.get("worktree_path")},
        "prompt_path": str(project / str(request.get("prompt_path", ""))),
        "artifact_dir": str(artifact_dir),
        "artifact_paths": [str(child_result["_result_path"]), str(events_path)],
        "child_result": child_result,
        "modified_files": child_result.get("modified_files", []),
        "commands_run": child_result.get("commands_run", []),
        "findings_or_risks": findings_from_child(child_result) + trust_issues,
        "next_step": child_result.get("next_step"),
    }
    for artifact in artifact_paths_from_child(child_result):
        result["artifact_paths"].append(artifact)
    request["status"] = request_status
    request["finished_at"] = result["ended_at"]
    request["artifacts"] = sorted(set(request.get("artifacts", []) + result["artifact_paths"]))
    request["modified_files"] = result["modified_files"]
    request["commands_run"] = result["commands_run"]
    request["failure_class"] = result.get("failure_category")
    request["next_step"] = result.get("next_step")
    append_event(events_path, {"event": "request_collected", "request_id": request.get("id"), "status": result_status, "request_status": request_status})
    return result


def run_gate_command(state: dict[str, Any], gate: dict[str, Any], run_id_value: str, timeout_seconds: int) -> dict[str, Any]:
    project = Path(state["project"]["path"])
    gate_id = str(gate.get("id", "gate"))
    argv = [str(item) for item in gate.get("argv", [])] if isinstance(gate.get("argv"), list) else shlex.split(str(gate.get("cmd", "")))
    command = command_text(argv)
    artifact_dir = project / "SOT" / "service-factory" / "runs" / run_id_value / "gates" / slug(gate_id)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = artifact_dir / "stdout.txt"
    stderr_path = artifact_dir / "stderr.txt"
    allowed, failure_category, reason = command_allowed(state, command)
    if has_shell_operators(argv):
        allowed, failure_category, reason = False, "unsafe_request", "shell operators are not allowed in gate argv"
    executable_ok, executable_failure, executable_reason = executable_allowed(argv)
    if allowed and not executable_ok:
        allowed, failure_category, reason = False, executable_failure, executable_reason
    result = {
        "run_id": run_id_value,
        "gate_id": gate_id,
        "stage": gate.get("stage"),
        "command": command,
        "argv": argv,
        "optional": bool(gate.get("optional")),
        "trusted": bool(gate.get("trusted")),
        "network_policy": gate.get("network_policy", "disabled_by_policy"),
        "env_policy": "minimal_allowlist",
        "status": "blocked",
        "failure_category": failure_category,
        "reason": reason,
        "exit_code": None,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "artifact_dir": str(artifact_dir),
        "started_at": now_iso(),
        "ended_at": None,
    }
    if not allowed:
        stderr_path.write_text(reason or "blocked by permission policy", encoding="utf-8")
        result["ended_at"] = now_iso()
        return result

    command_result = execute_argv(argv, project, stdout_path, stderr_path, timeout_seconds)
    result["status"] = "passed" if command_result["status"] == "completed" else ("timeout" if command_result["failure_category"] == "command_timeout" else "failed")
    result["failure_category"] = command_result["failure_category"]
    result["exit_code"] = command_result["exit_code"]
    result["started_at"] = command_result["started_at"]
    result["ended_at"] = command_result["ended_at"]
    return result


def build_execution_plan(state: dict[str, Any], requests: list[dict[str, Any]], missing: list[dict[str, Any]]) -> dict[str, Any]:
    parallel_groups = [
        {"id": "state_research_strategy", "stages": ["current_state", "research_intelligence", "development_plan"], "max_parallel": 1},
        {"id": "planning", "stages": ["product_brief", "repo_map"], "max_parallel": 2},
        {"id": "implementation", "stages": ["parallel_implementation"], "max_parallel": state.get("limits", {}).get("max_parallel_agents", 3)},
        {"id": "review", "stages": ["verification", "security_review"], "max_parallel": 3},
    ]
    return {
        "runner_version": "0.2",
        "mode": "plan_only_until_parent_spawns_agents",
        "operating_contract": state.get("operating_contract", {
            "version": "state-plan-execute-v1",
            "required_order": ["current_state", "research_intelligence", "development_plan", "execution_verification"],
            "phases": OPERATING_PHASES,
        }),
        "worktree_isolation": {
            "enabled": True,
            "root": ".service-factory/worktrees",
            "policy": "one_writer_per_owned_path",
        },
        "parallel_groups": parallel_groups,
        "watchdog": {
            "enabled": True,
            "stale_after_minutes": 15,
            "progress_files": ["SOT/service-factory/progress.jsonl", "SOT/service-factory/handoff-latest.md"],
            "action": "mark_blocked_or_respawn_from_handoff",
        },
        "handoff": {
            "enabled": True,
            "required_fields": [
                "factory_id",
                "request_id",
                "run_id",
                "stage",
                "command_owner",
                "current_owner",
                "execution_controller",
                "successor_role",
                "status",
                "backend",
                "last_command",
                "last_artifact",
                "failure_category",
                "blocked_reason",
                "next_step",
                "owned_paths",
                "pending_artifacts",
                "approval_gate_snapshot",
                "agent_topology_snapshot",
                "mandatory_requests_remaining",
                "retry_count",
                "respawn_eligible",
                "lease_owner",
                "lease_expires_at",
                "resume_command",
            ],
        },
        "automatic_gates": detect_gate_commands(Path(state["project"]["path"])),
        "ready_to_spawn": [request["id"] for request in requests if request.get("available")],
        "foundry_required": [item["agent_type"] for item in missing],
    }


def detect_gate_commands(project: Path) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    if (project / "package.json").exists():
        commands.extend(
            [
                {"id": "node-test", "cmd": "npm test", "argv": ["npm", "test"], "stage": "verification", "optional": True, "trusted": False, "network_policy": "disabled_by_policy", "env_policy": "minimal_allowlist"},
                {"id": "node-build", "cmd": "npm run build", "argv": ["npm", "run", "build"], "stage": "verification", "optional": True, "trusted": False, "network_policy": "disabled_by_policy", "env_policy": "minimal_allowlist"},
                {"id": "node-typecheck", "cmd": "npm run typecheck", "argv": ["npm", "run", "typecheck"], "stage": "verification", "optional": True, "trusted": False, "network_policy": "disabled_by_policy", "env_policy": "minimal_allowlist"},
            ]
        )
    if (project / "pyproject.toml").exists() or (project / "pytest.ini").exists() or (project / "setup.py").exists():
        commands.append({"id": "pytest", "cmd": "python3 -m pytest", "argv": ["python3", "-m", "pytest"], "stage": "verification", "optional": True, "trusted": False, "network_policy": "disabled_by_policy", "env_policy": "minimal_allowlist"})
        commands.append({"id": "py-compile", "cmd": "python3 -m compileall .", "argv": ["python3", "-m", "compileall", "."], "stage": "verification", "optional": True, "trusted": True, "network_policy": "disabled_by_policy", "env_policy": "minimal_allowlist"})
    if (project / "Cargo.toml").exists():
        commands.append({"id": "cargo-test", "cmd": "cargo test", "argv": ["cargo", "test"], "stage": "verification", "optional": True, "trusted": False, "network_policy": "disabled_by_policy", "env_policy": "minimal_allowlist"})
        commands.append({"id": "cargo-check", "cmd": "cargo check", "argv": ["cargo", "check"], "stage": "verification", "optional": True, "trusted": False, "network_policy": "disabled_by_policy", "env_policy": "minimal_allowlist"})
    commands.append(
        {
            "id": "service-factory-validate",
            "cmd": f"{sys.executable} {SCRIPT_DIR / 'service_factory.py'} validate --project .",
            "argv": [sys.executable, str(SCRIPT_DIR / "service_factory.py"), "validate", "--project", "."],
            "stage": "final_audit",
            "optional": False,
            "trusted": True,
            "network_policy": "disabled_by_policy",
            "env_policy": "minimal_allowlist",
        }
    )
    return commands


def build_state(
    project: Path,
    goal: str,
    mode: str,
    forbidden: str | None = None,
    definition_of_done: str | None = None,
    approval_delegation: str | None = None,
) -> dict[str, Any]:
    resolved = project.resolve()
    timestamp = now_iso()
    roles = detect_roles(goal)
    stages = []
    for index, (stage_id, stage_roles, depends_on, done_requires) in enumerate(STAGES):
        stages.append(make_stage(stage_id, stage_roles, depends_on, done_requires, index=index))

    return {
        "schema_version": "1.0",
        "factory_id": factory_id(),
        "created_at": timestamp,
        "updated_at": timestamp,
        "project": {"path": str(resolved), "name": project_name(resolved)},
        "goal": goal,
        "mode": mode,
        "status": "draft",
        "intake_contract": _ic_build_contract(
            goal=goal,
            forbidden=forbidden,
            definition_of_done=definition_of_done,
            approval_delegation=approval_delegation,
        ),
        "constraints": {
            "db_data_deletion": "forbidden_without_explicit_user_approval",
            "production_deploy": "requires_explicit_user_approval",
            "paid_api_budget": "requires_explicit_user_approval",
            "external_communication": "requires_explicit_user_approval",
            "offensive_security": "requires_explicit_user_approval_and_scope",
        },
        "operating_contract": {
            "version": "state-plan-execute-v1",
            "required_order": ["current_state", "research_intelligence", "development_plan", "execution_verification"],
            "rule": "Always inspect current state first, then run research intelligence and hypothesis QC, then write a goal-to-plan strategy, then execute and verify. Do not start implementation before current-state, research, and development-plan artifacts exist unless the user explicitly requests a trivial one-shot task.",
            "phases": OPERATING_PHASES,
        },
        "gates": [
            {"id": gate, "status": "pending", "requires_human_approval": True, "evidence": []}
            for gate in APPROVAL_GATES
        ],
        "roles": roles,
        "stages": stages,
        "artifacts": [],
        "known_issues": [],
        "limits": {"max_child_agents": 12, "max_parallel_agents": 3, "max_retries_per_stage": 3, "max_wall_clock_minutes": None},
        "budget": {"agent_call_limit": None, "paid_api_limit": "requires_explicit_user_approval", "notes": []},
        "green_policy": {
            "required_evidence": ["command", "exit_code", "artifact_path", "independent_verification"],
            "self_check_only_state": "validation_required",
            "mock_only_state": "validation_required",
        },
        "file_leases": [],
        "agent_requests": [],
        "agent_results": [],
        "gate_results": [],
        "missing_capabilities": [],
        "foundry": {"mode": "request_manifest_when_missing", "proposed_manifests": []},
        "execution_plan": {},
        "runtime": {"backend": None, "last_run_id": None, "last_run_at": None, "status": "not_started"},
        "run_log": {
            "command_owner": STELLA_COMMAND_OWNER,
            "current_owner": STELLA_COMMAND_OWNER,
            "execution_controller": RELEASE_EXECUTION_CONTROLLER,
            "last_command": None,
            "last_artifact": None,
            "blocked_reason": None,
            "next_step": "product_brief",
        },
        "resume": {"count": 0, "last_completed_stage": None, "notes": []},
    }


def load_state(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("state root must be an object")
    return data


def write_new_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_operating_contract(state)
    ensure_stella_control_plane(state)
    payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)


def validate_state(state: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    project_info = state.get("project") if isinstance(state.get("project"), dict) else {}
    project_path = Path(str(project_info.get("path", "."))).expanduser()

    for key in ["schema_version", "factory_id", "created_at", "updated_at", "project", "goal", "status", "roles", "stages", "gates"]:
        if key not in state:
            errors.append(f"missing required field: {key}")

    if state.get("command_owner") != STELLA_COMMAND_OWNER:
        warnings.append("command_owner should be Stella for Service Factory runs")
    run_log = state.get("run_log") if isinstance(state.get("run_log"), dict) else {}
    if run_log.get("current_owner") != STELLA_COMMAND_OWNER or run_log.get("execution_controller") != RELEASE_EXECUTION_CONTROLLER:
        warnings.append("run_log should preserve Stella current_owner and Release execution_controller")
    topology = state.get("agent_topology")
    if not isinstance(topology, dict):
        warnings.append("agent_topology is missing; run plan to materialize AgentBlueprint/AgentInstance distinctions")
    elif topology.get("command_owner") != STELLA_COMMAND_OWNER:
        warnings.append("agent_topology.command_owner should be Stella")

    if state.get("status") not in FACTORY_STATES:
        errors.append(f"invalid status: {state.get('status')!r}")

    contract = state.get("operating_contract")
    if not isinstance(contract, dict):
        warnings.append("operating_contract is missing; run plan to apply the state-plan-execute contract")
    else:
        required_order = contract.get("required_order")
        if required_order != ["current_state", "research_intelligence", "development_plan", "execution_verification"]:
            errors.append("operating_contract.required_order must be current_state -> research_intelligence -> development_plan -> execution_verification")

    roles = state.get("roles", [])
    if not isinstance(roles, list):
        errors.append("roles must be a list")
        roles = []
    role_ids = [role.get("id") for role in roles if isinstance(role, dict)]
    if len(role_ids) != len(set(role_ids)):
        errors.append("role ids must be unique")
    known_roles = set(role_ids)

    stages = state.get("stages", [])
    if not isinstance(stages, list):
        errors.append("stages must be a list")
        stages = []
    stage_ids = [stage.get("id") for stage in stages if isinstance(stage, dict)]
    if len(stage_ids) != len(set(stage_ids)):
        errors.append("stage ids must be unique")
    known_stages = set(stage_ids)

    for stage in stages:
        if not isinstance(stage, dict):
            errors.append("stage entry must be an object")
            continue
        stage_id = stage.get("id", "<unknown>")
        if stage.get("state") not in QUEUE_STATES:
            errors.append(f"{stage_id}: invalid state {stage.get('state')!r}")
        for dependency in stage.get("depends_on", []):
            if dependency not in known_stages:
                errors.append(f"{stage_id}: unknown dependency {dependency!r}")
        for role_id in stage.get("roles", []):
            if role_id not in known_roles:
                errors.append(f"{stage_id}: unknown role {role_id!r}")
        if stage.get("state") == "done" and stage.get("done_requires") and not stage.get("artifacts"):
            warnings.append(f"{stage_id}: done but artifacts list is empty")

    gates = state.get("gates", [])
    if not isinstance(gates, list):
        errors.append("gates must be a list")
        gates = []
    gate_ids = [gate.get("id") for gate in gates if isinstance(gate, dict)]
    for required_gate in APPROVAL_GATES:
        if required_gate not in gate_ids:
            errors.append(f"missing approval gate: {required_gate}")
    for gate in gates:
        if not isinstance(gate, dict):
            errors.append("gate entry must be an object")
            continue
        gate_id = gate.get("id", "<unknown>")
        if gate.get("status") not in GATE_STATUSES:
            errors.append(f"{gate_id}: invalid gate status {gate.get('status')!r}")
        if gate.get("requires_human_approval") and gate.get("status") == "approved" and not gate.get("evidence"):
            errors.append(f"{gate_id}: approved gate requires evidence")

    if state.get("status") == "done":
        unfinished = [
            stage.get("id")
            for stage in stages
            if isinstance(stage, dict) and stage.get("state") in {"queued", "in_progress", "blocked", "validation_required"}
        ]
        if unfinished:
            errors.append("factory status done but unfinished stages remain: " + ", ".join(str(item) for item in unfinished))
        pending_gates = [
            gate.get("id")
            for gate in gates
            if isinstance(gate, dict) and gate.get("requires_human_approval") and gate.get("status") == "pending"
        ]
        if pending_gates:
            errors.append("factory status done but approval gates are still pending: " + ", ".join(str(item) for item in pending_gates))

    limits = state.get("limits", {})
    if limits and not isinstance(limits, dict):
        errors.append("limits must be an object")
    elif isinstance(limits, dict):
        max_parallel = limits.get("max_parallel_agents")
        if isinstance(max_parallel, int) and max_parallel > 3:
            warnings.append("max_parallel_agents above 3 requires extra cost/coordination review")

    leases = state.get("file_leases", [])
    if leases and not isinstance(leases, list):
        errors.append("file_leases must be a list")
    elif isinstance(leases, list):
        write_paths: dict[str, str] = {}
        for lease in leases:
            if not isinstance(lease, dict):
                errors.append("file lease entry must be an object")
                continue
            path = lease.get("path")
            owner = lease.get("owner")
            mode = lease.get("mode")
            if not path or not owner:
                errors.append("file lease requires path and owner")
            if mode not in LEASE_MODES:
                errors.append(f"{path or '<unknown>'}: invalid lease mode {mode!r}")
            if isinstance(path, str) and path.startswith(".."):
                errors.append(f"{path}: file lease cannot escape project root")
            if mode == "write" and isinstance(path, str):
                previous_owner = write_paths.get(path)
                if previous_owner and previous_owner != owner:
                    errors.append(f"{path}: multiple write owners ({previous_owner}, {owner})")
                write_paths[path] = str(owner)

    requests = state.get("agent_requests", [])
    if requests and not isinstance(requests, list):
        errors.append("agent_requests must be a list")
    elif isinstance(requests, list):
        request_ids: set[str] = set()
        for request in requests:
            if not isinstance(request, dict):
                errors.append("agent request entry must be an object")
                continue
            request_id = str(request.get("id", ""))
            if not request_id:
                errors.append("agent request requires id")
            if request_id in request_ids:
                errors.append(f"duplicate agent request id: {request_id}")
            request_ids.add(request_id)
            if request.get("status") not in REQUEST_STATUSES:
                errors.append(f"{request_id}: invalid request status {request.get('status')!r}")
            stage = request.get("stage")
            if stage and stage not in known_stages:
                errors.append(f"{request_id}: unknown request stage {stage!r}")
            prompt_path = request.get("prompt_path")
            if isinstance(prompt_path, str):
                try:
                    safe_project_relative_path(project_path, prompt_path)
                except ValueError as exc:
                    errors.append(f"{request_id}: invalid prompt path: {exc}")
            artifact_dir = request.get("artifact_dir")
            if isinstance(artifact_dir, str):
                artifact_path = Path(artifact_dir).expanduser()
                if not artifact_path.is_absolute():
                    artifact_path = project_path / artifact_path
                runs_root = project_path / "SOT" / "service-factory" / "runs"
                if not path_is_within(artifact_path, runs_root):
                    errors.append(f"{request_id}: artifact_dir must stay under SOT/service-factory/runs")
                expected_run_id = str(request.get("last_run_id") or "")
                if expected_run_id:
                    expected_artifact_dir = canonical_artifact_dir(project_path, request, expected_run_id)
                    try:
                        if request.get("status") != "completed" and artifact_path.resolve() != expected_artifact_dir.resolve():
                            errors.append(f"{request_id}: artifact_dir does not match canonical run directory")
                    except OSError:
                        errors.append(f"{request_id}: artifact_dir cannot be resolved")

    agent_results = state.get("agent_results", [])
    if agent_results and not isinstance(agent_results, list):
        errors.append("agent_results must be a list")
    elif isinstance(agent_results, list):
        for result in agent_results:
            if not isinstance(result, dict):
                errors.append("agent result entry must be an object")
                continue
            result_id = result.get("request_id", "<unknown>")
            if result.get("status") not in RESULT_STATUSES:
                errors.append(f"{result_id}: invalid agent result status {result.get('status')!r}")
            failure_category = result.get("failure_category")
            if failure_category and failure_category not in RUN_FAILURE_CATEGORIES:
                warnings.append(f"{result_id}: unknown failure category {failure_category!r}")

    gate_results = state.get("gate_results", [])
    if gate_results and not isinstance(gate_results, list):
        errors.append("gate_results must be a list")
    elif isinstance(gate_results, list):
        for result in gate_results:
            if not isinstance(result, dict):
                errors.append("gate result entry must be an object")
                continue
            gate_id = result.get("gate_id", "<unknown>")
            if result.get("status") not in GATE_RESULT_STATUSES:
                errors.append(f"{gate_id}: invalid gate result status {result.get('status')!r}")

    missing = state.get("missing_capabilities", [])
    if missing and not isinstance(missing, list):
        errors.append("missing_capabilities must be a list")
    elif isinstance(missing, list):
        for item in missing:
            if not isinstance(item, dict):
                errors.append("missing capability entry must be an object")
                continue
            if not item.get("agent_type"):
                errors.append("missing capability requires agent_type")
            if item.get("suggested_action") == "create_agent_manifest" and not item.get("proposed_manifest"):
                warnings.append(f"{item.get('agent_type', '<unknown>')}: missing proposed_manifest")

    execution_plan = state.get("execution_plan", {})
    if execution_plan and not isinstance(execution_plan, dict):
        errors.append("execution_plan must be an object")
    elif isinstance(execution_plan, dict):
        automatic_gates = execution_plan.get("automatic_gates", [])
        if automatic_gates and not isinstance(automatic_gates, list):
            errors.append("execution_plan.automatic_gates must be a list")
        elif isinstance(automatic_gates, list):
            allowed_gate_fields = {"id", "cmd", "argv", "stage", "optional", "trusted", "network_policy", "env_policy"}
            for gate in automatic_gates:
                if not isinstance(gate, dict):
                    errors.append("automatic gate entry must be an object")
                    continue
                gate_id = gate.get("id", "<unknown>")
                unknown_fields = set(gate) - allowed_gate_fields
                if unknown_fields:
                    errors.append(f"{gate_id}: unknown automatic gate field(s): {', '.join(sorted(unknown_fields))}")
                if not gate.get("id"):
                    errors.append("automatic gate requires id")
                if gate.get("stage") not in known_stages:
                    errors.append(f"{gate_id}: unknown automatic gate stage {gate.get('stage')!r}")
                argv = gate.get("argv")
                if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
                    errors.append(f"{gate_id}: automatic gate requires non-empty argv[]")
                elif has_shell_operators(argv):
                    errors.append(f"{gate_id}: automatic gate argv contains shell operators")
                if gate.get("network_policy") != "disabled_by_policy":
                    errors.append(f"{gate_id}: automatic gate network_policy must be disabled_by_policy")
                if gate.get("env_policy") != "minimal_allowlist":
                    errors.append(f"{gate_id}: automatic gate env_policy must be minimal_allowlist")

    return errors, warnings


def resolve_state_path(args: argparse.Namespace) -> Path:
    if getattr(args, "state", None):
        return Path(args.state).expanduser()
    if getattr(args, "project", None):
        return default_state_path(Path(args.project).expanduser())
    raise SystemExit("--state or --project is required")


def ensure_intake_contract(state: dict[str, Any]) -> dict[str, Any]:
    """오래된 state 에 intake_contract 가 없으면 goal 로 생성, 있으면 status 재평가.

    state['goal'] 을 contract.fields.goal 로 미러링해 단일 진실을 유지한다.
    """
    existing = state.get("intake_contract") if isinstance(state.get("intake_contract"), dict) else None
    goal = str(state.get("goal", "")).strip() or None
    if existing is None:
        state["intake_contract"] = _ic_build_contract(goal=goal)
    else:
        fields = dict(existing.get("fields", {})) if isinstance(existing.get("fields"), dict) else {}
        if goal and not fields.get("goal"):
            fields["goal"] = goal
        state["intake_contract"] = _ic_build_contract(existing={"fields": fields})
    return state


def intake_gate_block(state: dict[str, Any], state_path: Path, allow_incomplete: bool, pretty: bool) -> int | None:
    """plan/run 진입 게이트. 4항목 미충족이면 되물을 질문을 출력하고 차단(exit 3).

    완결이거나 --allow-incomplete-intake 면 None(통과).
    """
    gate = _ic_intake_gate(state)
    if gate["intake_complete"] or allow_incomplete:
        return None
    run_log = state.get("run_log") if isinstance(state.get("run_log"), dict) else {}
    run_log["blocked_reason"] = "intake_clarification_required"
    run_log["next_step"] = "fill missing intake fields, then re-run"
    state["run_log"] = run_log
    block = {
        "state": str(state_path),
        "intake_clarification_required": True,
        "missing_fields": gate["missing_fields"],
        "clarification_questions": gate["clarification_questions"],
        "next_step": (
            "사용자에게 각 clarification_question 을 물어본 뒤 채우세요: "
            "service_factory.py intake --project <project> --set <field> --value \"<답변>\""
        ),
    }
    print(json.dumps(block, ensure_ascii=False, indent=2 if pretty else None))
    return 3


def command_init(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser()
    state_path = Path(args.state).expanduser() if args.state else default_state_path(project)
    state = build_state(
        project,
        args.goal,
        args.mode,
        forbidden=getattr(args, "forbidden", None),
        definition_of_done=getattr(args, "dod", None),
        approval_delegation=getattr(args, "approval_delegation", None),
    )
    write_new_state(state_path, state)
    gate = _ic_intake_gate(state)
    out = {
        "created": str(state_path),
        "factory_id": state["factory_id"],
        "status": state["status"],
        "intake_complete": gate["intake_complete"],
        "missing_fields": gate["missing_fields"],
        "clarification_questions": gate["clarification_questions"],
    }
    if not gate["intake_complete"]:
        out["next_step"] = (
            "사용자에게 각 clarification_question 을 물어본 뒤 채우세요: "
            "service_factory.py intake --project <project> --set <field> --value \"<답변>\""
        )
    print(json.dumps(out, ensure_ascii=False, indent=2 if getattr(args, "pretty", False) else None))
    return 0


def command_intake(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    ensure_intake_contract(state)
    if getattr(args, "set_field", None):
        if args.value is None:
            print(json.dumps({"error": "--value is required with --set"}, ensure_ascii=False))
            return 2
        state["intake_contract"] = _ic_set_field(state["intake_contract"], args.set_field, args.value)
        write_state(state_path, state)
    else:
        write_state(state_path, state)
    gate = _ic_intake_gate(state)
    out = {
        "state": str(state_path),
        "intake_complete": gate["intake_complete"],
        "missing_fields": gate["missing_fields"],
        "fields": state.get("intake_contract", {}).get("fields", {}),
        "clarification_questions": gate["clarification_questions"],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2 if getattr(args, "pretty", False) else None))
    return 0


def command_status(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    ensure_operating_contract(state)
    ensure_stella_control_plane(state)
    stages = state.get("stages", [])
    counts = {name: 0 for name in sorted(QUEUE_STATES)}
    for stage in stages:
        if isinstance(stage, dict) and stage.get("state") in counts:
            counts[stage["state"]] += 1
    summary = {
        "state": str(state_path),
        "factory_id": state.get("factory_id"),
        "status": state.get("status"),
        "goal": state.get("goal"),
        "command_owner": state.get("command_owner"),
        "execution_controller": state.get("run_log", {}).get("execution_controller"),
        "agent_topology": {
            "blueprints": state.get("agent_topology", {}).get("blueprint_count"),
            "instances": state.get("agent_topology", {}).get("instance_count"),
            "kanban_role": state.get("agent_topology", {}).get("kanban_role"),
        },
        "stage_counts": counts,
        "next": [stage.get("id") for stage in stages if isinstance(stage, dict) and stage.get("state") in {"queued", "in_progress", "validation_required"}][:3],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    ensure_operating_contract(state)
    ensure_stella_control_plane(state)
    errors, warnings = validate_state(state)
    result = {"state": str(state_path), "valid": not errors, "errors": errors, "warnings": warnings}
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 1 if errors else 0


def command_suggest(args: argparse.Namespace) -> int:
    roles = detect_roles(args.goal)
    result = {
        "goal": args.goal,
        "roles": [{"id": role["id"], "owner": role["owner"], "kind": role["kind"], "spawn_policy": role["spawn_policy"]} for role in roles],
        "foundry_candidates": foundry_roles(args.goal),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def command_plan(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    ensure_operating_contract(state)
    ensure_intake_contract(state)
    gate_code = intake_gate_block(state, state_path, getattr(args, "allow_incomplete_intake", False), getattr(args, "pretty", False))
    if gate_code is not None:
        write_state(state_path, state)
        return gate_code
    state["roles"] = detect_roles(str(state.get("goal", "")))
    fresh_requests, missing = build_agent_requests(state)
    requests = merge_agent_requests(state.get("agent_requests", []), fresh_requests)
    state["agent_requests"] = requests
    state["missing_capabilities"] = missing
    state["foundry"] = {
        "mode": "request_manifest_when_missing",
        "proposed_manifests": [
            {"agent_type": item["agent_type"], "manifest": item.get("proposed_manifest", "")}
            for item in missing
            if item.get("proposed_manifest")
        ],
    }
    state["execution_plan"] = build_execution_plan(state, requests, missing)
    update_stage_states_from_requests(state)
    # 260603 — file_leases ledger 자동 흡수 (Release 가 stage 시작 전에 lease 남긴다는 약속 정합).
    # owned_paths 데이터는 이미 build_agent_requests 가 박았으므로 한 줄로 ledger 채움.
    state["file_leases"] = _fl_seed_file_leases_from_requests(state)
    written = write_agent_prompts(state_path, state)
    state["artifacts"] = sorted(set(state.get("artifacts", []) + [path for path in written]))
    state["run_log"] = {
        "current_owner": "Release",
        "last_command": "service_factory.py plan",
        "last_artifact": str(state_path),
        "blocked_reason": "missing_capabilities" if missing else None,
        "next_step": "create missing agent manifests" if missing else "spawn queued agent requests",
    }
    write_state(state_path, state)
    result = {
        "state": str(state_path),
        "agent_requests": len(requests),
        "missing_capabilities": len(missing),
        "file_leases": len(state.get("file_leases", [])),
        "file_lease_conflicts": len(_fl_detect_write_conflicts(state.get("file_leases", []))),
        "prompt_files": written,
        "next_step": state["run_log"]["next_step"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 1 if missing and args.fail_on_missing else 0


def command_run(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    ensure_operating_contract(state)
    errors, warnings = validate_state(state)
    if errors:
        print(json.dumps({"state": str(state_path), "valid": False, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2 if args.pretty else None))
        return 2

    ensure_intake_contract(state)
    gate_code = intake_gate_block(state, state_path, getattr(args, "allow_incomplete_intake", False), getattr(args, "pretty", False))
    if gate_code is not None:
        write_state(state_path, state)
        return gate_code

    if not state.get("agent_requests") and args.auto_plan:
        state["roles"] = detect_roles(str(state.get("goal", "")))
        requests, missing = build_agent_requests(state)
        state["agent_requests"] = requests
        state["missing_capabilities"] = missing
        state["foundry"] = {
            "mode": "request_manifest_when_missing",
            "proposed_manifests": [
                {"agent_type": item["agent_type"], "manifest": item.get("proposed_manifest", "")}
                for item in missing
                if item.get("proposed_manifest")
            ],
        }
        state["execution_plan"] = build_execution_plan(state, requests, missing)
        written = write_agent_prompts(state_path, state)
        state["artifacts"] = sorted(set(state.get("artifacts", []) + written))

    advance_intake_stage(state)
    run_id_value = run_id()
    max_requests = args.max_requests
    selected = select_requests_to_run(state, args.request, max_requests, args.include_unavailable)
    state["status"] = "running"
    state.setdefault("agent_results", [])
    state.setdefault("gate_results", [])
    state["runtime"] = {
        "backend": args.backend,
        "last_run_id": run_id_value,
        "last_run_at": now_iso(),
        "status": "running",
        "command_policy": "argv_only_no_shell",
        "env_policy": "minimal_allowlist",
        "repo_gates_included": bool(args.include_repo_gates),
    }
    progress_path = append_progress(
        state,
        {
            "event": "run_started",
            "run_id": run_id_value,
            "backend": args.backend,
            "selected_requests": [request.get("id") for request in selected],
        },
    )

    results: list[dict[str, Any]] = []
    for request in selected:
        result = run_agent_request(
            state_path,
            state,
            request,
            backend=args.backend,
            command_template=args.agent_command_template,
            run_id_value=run_id_value,
            timeout_seconds=args.timeout_seconds,
            prepare_worktrees=not args.no_worktrees,
            allow_paid_agent_call=args.allow_paid_agent_call,
        )
        results.append(result)
        state["agent_results"].append(result)
        append_progress(state, {"event": "agent_request_finished", "run_id": run_id_value, "request_id": result.get("request_id"), "status": result.get("status"), "failure_category": result.get("failure_category")})

    gate_results: list[dict[str, Any]] = []
    if not args.skip_gates:
        for gate in state.get("execution_plan", {}).get("automatic_gates", []):
            if not isinstance(gate, dict):
                continue
            if not gate.get("trusted") and not args.include_repo_gates:
                skipped = {
                    "run_id": run_id_value,
                    "gate_id": gate.get("id"),
                    "stage": gate.get("stage"),
                    "command": gate.get("cmd"),
                    "argv": gate.get("argv", []),
                    "optional": bool(gate.get("optional")),
                    "trusted": bool(gate.get("trusted")),
                    "status": "skipped",
                    "failure_category": None,
                    "reason": "repo-controlled gate skipped; pass --include-repo-gates to run it",
                    "started_at": now_iso(),
                    "ended_at": now_iso(),
                }
                gate_results.append(skipped)
                state["gate_results"].append(skipped)
                continue
            gate_result = run_gate_command(state, gate, run_id_value, args.timeout_seconds)
            gate_results.append(gate_result)
            state["gate_results"].append(gate_result)
            append_progress(state, {"event": "gate_finished", "run_id": run_id_value, "gate_id": gate_result.get("gate_id"), "status": gate_result.get("status"), "failure_category": gate_result.get("failure_category")})

    update_stage_states_from_requests(state)
    execution_plan_update = {"last_run_id": run_id_value}
    if selected and args.backend in AUTONOMOUS_BACKENDS:
        execution_plan_update["mode"] = f"spawn_runtime_{args.backend}"
    elif selected:
        execution_plan_update["last_manual_run_id"] = run_id_value
    state["execution_plan"] = {**state.get("execution_plan", {}), **execution_plan_update}
    result_paths = [
        artifact
        for result in results
        for artifact in result.get("artifact_paths", [])
    ]
    gate_paths = [
        path
        for gate_result in gate_results
        for path in [gate_result.get("stdout_path"), gate_result.get("stderr_path")]
        if path
    ]
    state["artifacts"] = sorted(set(state.get("artifacts", []) + [str(progress_path)] + result_paths + gate_paths))
    blocked = [result for result in results if result.get("status") == "blocked"]
    failed = [result for result in results if result.get("status") == "failed"]
    validation_required = [result for result in results if result.get("status") == "validation_required"]
    failed_gates = [result for result in gate_results if result.get("status") in {"failed", "blocked", "timeout"} and not result.get("optional")]
    if blocked:
        state["status"] = "blocked"
        blocked_reason = blocked[0].get("failure_category") or blocked[0].get("note")
        next_step = "resolve blocked agent request"
    elif failed or failed_gates:
        state["status"] = "validation_required"
        blocked_reason = (failed[0].get("failure_category") if failed else failed_gates[0].get("failure_category")) or "validation_failed"
        next_step = "review failed run artifacts and rerun"
    elif validation_required:
        state["status"] = "validation_required"
        blocked_reason = validation_required[0].get("failure_category") or "insufficient_evidence"
        next_step = "attach independent validation evidence or spawn a specialist agent"
    elif not selected:
        state["status"] = "validation_required"
        blocked_reason = "no_dispatchable_requests"
        next_step = "resolve blocked dependencies or select a queued request"
    else:
        state["status"] = "validation_required" if args.backend == "manual" else "running"
        blocked_reason = None
        next_step = "continue next service_factory.py run cycle or review artifacts"
    state["runtime"]["status"] = state["status"]
    state["run_log"] = {
        "current_owner": "Release",
        "last_command": "service_factory.py run",
        "last_artifact": str(progress_path),
        "blocked_reason": blocked_reason,
        "next_step": next_step,
    }
    if state["status"] in {"blocked", "validation_required"}:
        handoff_path, _ = write_handoff_files(state, state_path)
        state["run_log"]["last_artifact"] = str(handoff_path)
    write_state(state_path, state)
    summary = {
        "state": str(state_path),
        "run_id": run_id_value,
        "status": state["status"],
        "backend": args.backend,
        "selected_requests": [request.get("id") for request in selected],
        "agent_results": [{"request_id": result.get("request_id"), "status": result.get("status"), "failure_category": result.get("failure_category"), "artifact_dir": result.get("artifact_dir")} for result in results],
        "gate_results": [{"gate_id": result.get("gate_id"), "status": result.get("status"), "trusted": result.get("trusted"), "reason": result.get("reason")} for result in gate_results],
        "warnings": warnings,
        "next_step": next_step,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2 if args.pretty else None))
    return 1 if state["status"] in {"blocked", "validation_required"} or failed or failed_gates else 0


def command_dispatch(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    errors, warnings = validate_state(state)
    if errors:
        print(json.dumps({"state": str(state_path), "valid": False, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2 if args.pretty else None))
        return 2

    ensure_intake_contract(state)
    gate_code = intake_gate_block(state, state_path, getattr(args, "allow_incomplete_intake", False), getattr(args, "pretty", False))
    if gate_code is not None:
        write_state(state_path, state)
        return gate_code

    if not state.get("agent_requests") and args.auto_plan:
        state["roles"] = detect_roles(str(state.get("goal", "")))
        requests, missing = build_agent_requests(state)
        state["agent_requests"] = requests
        state["missing_capabilities"] = missing
        state["foundry"] = {
            "mode": "request_manifest_when_missing",
            "proposed_manifests": [
                {"agent_type": item["agent_type"], "manifest": item.get("proposed_manifest", "")}
                for item in missing
                if item.get("proposed_manifest")
            ],
        }
        state["execution_plan"] = build_execution_plan(state, requests, missing)
        written = write_agent_prompts(state_path, state)
        state["artifacts"] = sorted(set(state.get("artifacts", []) + written))

    advance_intake_stage(state)
    run_id_value = run_id()
    selected = select_requests_to_run(state, args.request, args.max_requests, args.include_unavailable)
    state["status"] = "running"
    state.setdefault("agent_results", [])
    state.setdefault("gate_results", [])
    state["runtime"] = {
        "backend": "codex_bridge",
        "last_run_id": run_id_value,
        "last_run_at": now_iso(),
        "status": "dispatched",
        "bridge": "dispatch_collect",
    }
    dispatches = [
        dispatch_agent_request(state_path, state, request, run_id_value, prepare_worktrees=not args.no_worktrees)
        for request in selected
    ]
    progress_path = append_progress(
        state,
        {
            "event": "dispatch_created",
            "run_id": run_id_value,
            "backend": "codex_bridge",
            "selected_requests": [request.get("id") for request in selected],
            "dispatches": [item["dispatch_path"] for item in dispatches],
        },
    )
    state["execution_plan"] = {**state.get("execution_plan", {}), "mode": "spawn_runtime_codex_bridge", "last_run_id": run_id_value}
    state["artifacts"] = sorted(set(state.get("artifacts", []) + [str(progress_path)] + [item["dispatch_path"] for item in dispatches] + [item["dispatch_json"] for item in dispatches]))
    state["run_log"] = {
        "current_owner": "Release",
        "last_command": "service_factory.py dispatch",
        "last_artifact": str(progress_path),
        "blocked_reason": None if dispatches else "no_dispatchable_requests",
        "next_step": "spawn Codex subagents from dispatch files and run service_factory.py collect",
    }
    write_state(state_path, state)
    summary = {
        "state": str(state_path),
        "run_id": run_id_value,
        "status": state["status"],
        "dispatches": dispatches,
        "warnings": warnings,
        "next_step": state["run_log"]["next_step"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if dispatches else 1


def command_dispatch_workflow(args: argparse.Namespace) -> int:
    """dispatch-workflow — stage-level fan-out via Claude Code Workflow tool.

    Thin facade. 실제 script/instructions 조립과 dispatch 파일 작성은
    service_factory_dynamic_workflow_backend 모듈이 담당한다 (Architecture-First).

    흐름:
      1. state 로드 + validate (errors 면 즉시 종료)
      2. agent_requests 가 비어 있고 auto_plan 이면 plan 자동 생성
      3. queued/in_progress 인 request 들을 골라낸다 (--stage 로 필터)
      4. --max-requests 로 cap
      5. 각 request 에 canonical artifact_dir 보장
      6. 한 번에 묶어 dispatch.workflow.js + dispatch.instructions.md + dispatch.json 산출
      7. state 갱신 (request.status='running', backend='dynamic_workflow', last_run_id 기록)
      8. summary JSON print
    """
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    errors, warnings = validate_state(state)
    if errors:
        print(
            json.dumps(
                {"state": str(state_path), "valid": False, "errors": errors, "warnings": warnings},
                ensure_ascii=False,
                indent=2 if args.pretty else None,
            )
        )
        return 2

    ensure_intake_contract(state)
    gate_code = intake_gate_block(state, state_path, getattr(args, "allow_incomplete_intake", False), getattr(args, "pretty", False))
    if gate_code is not None:
        write_state(state_path, state)
        return gate_code

    if not state.get("agent_requests") and args.auto_plan:
        state["roles"] = detect_roles(str(state.get("goal", "")))
        requests, missing = build_agent_requests(state)
        state["agent_requests"] = requests
        state["missing_capabilities"] = missing
        state["foundry"] = {
            "mode": "request_manifest_when_missing",
            "proposed_manifests": [
                {"agent_type": item["agent_type"], "manifest": item.get("proposed_manifest", "")}
                for item in missing
                if item.get("proposed_manifest")
            ],
        }
        state["execution_plan"] = build_execution_plan(state, requests, missing)
        written = write_agent_prompts(state_path, state)
        state["artifacts"] = sorted(set(state.get("artifacts", []) + written))

    advance_intake_stage(state)
    run_id_value = run_id()
    selected = _dw_collect_dispatch_requests(state, stage=getattr(args, "stage", None))
    if args.request:
        selected = [r for r in selected if r.get("id") == args.request]
    if args.max_requests and args.max_requests > 0:
        selected = selected[: args.max_requests]

    if not selected:
        summary = {
            "state": str(state_path),
            "run_id": run_id_value,
            "status": state.get("status"),
            "backend": "dynamic_workflow",
            "dispatched": 0,
            "warnings": warnings + ["no_dispatchable_requests"],
            "next_step": "service_factory.py plan 또는 새 stage queue 후 재시도",
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2 if args.pretty else None))
        return 1

    # 각 request 에 artifact_dir 보장 + request status='running' + backend 기록
    project = Path(state["project"]["path"])
    for r in selected:
        ad = canonical_artifact_dir(project, r, run_id_value)
        ad.mkdir(parents=True, exist_ok=True)
        r["artifact_dir"] = str(ad)
        r["last_run_id"] = run_id_value
        r["status"] = "running"
        r["backend"] = "dynamic_workflow"

    summary = _dw_write_dispatch(
        state=state,
        state_path=state_path,
        bridge_dir=bridge_dir(state),
        run_id=run_id_value,
        requests=selected,
        max_parallel=getattr(args, "max_parallel", None),
    )

    state["status"] = "running"
    state["execution_plan"] = {
        **state.get("execution_plan", {}),
        "mode": "spawn_runtime_dynamic_workflow",
        "last_run_id": run_id_value,
    }
    state["artifacts"] = sorted(
        set(state.get("artifacts", []) + [summary["workflow_script"], summary["instructions"]])
    )
    state["run_log"] = {
        "current_owner": "Release",
        "last_command": "service_factory.py dispatch-workflow",
        "last_artifact": summary["instructions"],
        "blocked_reason": None,
        "next_step": (
            "parent agent 가 Workflow 도구로 dispatch.workflow.js 를 실행 → "
            "결과를 각 artifact_dir/result.json 으로 직렬화 → service_factory.py collect"
        ),
    }
    write_state(state_path, state)

    out = {
        "state": str(state_path),
        "run_id": run_id_value,
        "status": state["status"],
        "backend": "dynamic_workflow",
        "dispatched": len(selected),
        "request_ids": [r.get("id") for r in selected],
        "workflow_script": summary["workflow_script"],
        "instructions": summary["instructions"],
        "dispatch_json": str(Path(summary["workflow_script"]).parent / "dispatch.json"),
        "max_parallel": summary["max_parallel"],
        "warnings": warnings,
        "next_step": state["run_log"]["next_step"],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def command_collect(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    errors, warnings = validate_state(state)
    if errors:
        print(json.dumps({"state": str(state_path), "valid": False, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2 if args.pretty else None))
        return 2

    run_id_value = args.run_id or state.get("runtime", {}).get("last_run_id") or run_id()
    state.setdefault("agent_results", [])
    state.setdefault("gate_results", [])
    collected: list[dict[str, Any]] = []
    missing_results: list[str] = []
    for request in state.get("agent_requests", []):
        if not isinstance(request, dict):
            continue
        if args.request and request.get("id") != args.request:
            continue
        if request.get("status") not in {"running", "validation_required", "failed", "blocked"}:
            continue
        result = collect_agent_request_result(state, request, args.run_id)
        if result:
            collected.append(result)
            state["agent_results"].append(result)
            append_progress(state, {"event": "agent_request_collected", "run_id": run_id_value, "request_id": result.get("request_id"), "status": result.get("status"), "failure_category": result.get("failure_category")})
        else:
            missing_results.append(str(request.get("id")))

    gate_results: list[dict[str, Any]] = []
    if collected and not args.skip_gates:
        for gate in state.get("execution_plan", {}).get("automatic_gates", []):
            if not isinstance(gate, dict):
                continue
            if not gate.get("trusted") and not args.include_repo_gates:
                skipped = {
                    "run_id": run_id_value,
                    "gate_id": gate.get("id"),
                    "stage": gate.get("stage"),
                    "command": gate.get("cmd"),
                    "argv": gate.get("argv", []),
                    "optional": bool(gate.get("optional")),
                    "trusted": bool(gate.get("trusted")),
                    "status": "skipped",
                    "failure_category": None,
                    "reason": "repo-controlled gate skipped; pass --include-repo-gates to run it",
                    "started_at": now_iso(),
                    "ended_at": now_iso(),
                }
                gate_results.append(skipped)
                state["gate_results"].append(skipped)
                continue
            gate_result = run_gate_command(state, gate, str(run_id_value), args.timeout_seconds)
            gate_results.append(gate_result)
            state["gate_results"].append(gate_result)
            append_progress(state, {"event": "gate_finished", "run_id": run_id_value, "gate_id": gate_result.get("gate_id"), "status": gate_result.get("status"), "failure_category": gate_result.get("failure_category")})

    update_stage_states_from_requests(state)
    result_paths = [
        artifact
        for result in collected
        for artifact in result.get("artifact_paths", [])
    ]
    gate_paths = [
        path
        for gate_result in gate_results
        for path in [gate_result.get("stdout_path"), gate_result.get("stderr_path")]
        if path
    ]
    state["artifacts"] = sorted(set(state.get("artifacts", []) + result_paths + gate_paths))
    blocked = [result for result in collected if result.get("status") == "blocked"]
    failed = [result for result in collected if result.get("status") == "failed"]
    validation_required = [result for result in collected if result.get("status") == "validation_required"]
    failed_gates = [result for result in gate_results if result.get("status") in {"failed", "blocked", "timeout"} and not result.get("optional")]
    if blocked:
        state["status"] = "blocked"
        blocked_reason = blocked[0].get("failure_category") or "agent_blocked"
        next_step = "resolve blocked collected result"
    elif failed or failed_gates:
        state["status"] = "validation_required"
        blocked_reason = (failed[0].get("failure_category") if failed else failed_gates[0].get("failure_category")) or "validation_failed"
        next_step = "review failed collected artifacts"
    elif validation_required or missing_results:
        state["status"] = "validation_required"
        blocked_reason = "missing_or_unverified_results" if missing_results else None
        next_step = "collect remaining results or run independent verification"
    else:
        state["status"] = "running"
        blocked_reason = None
        next_step = "continue dispatching next queued requests"
    state["runtime"] = {
        **state.get("runtime", {}),
        "backend": "codex_bridge",
        "last_run_id": run_id_value,
        "last_run_at": now_iso(),
        "status": state["status"],
        "bridge": "dispatch_collect",
    }
    state["run_log"] = {
        "current_owner": "Release",
        "last_command": "service_factory.py collect",
        "last_artifact": collected[-1]["artifact_dir"] if collected else None,
        "blocked_reason": blocked_reason,
        "next_step": next_step,
    }
    if state["status"] in {"blocked", "validation_required"}:
        handoff_path, _ = write_handoff_files(state, state_path)
        state["run_log"]["last_artifact"] = str(handoff_path)
    write_state(state_path, state)
    summary = {
        "state": str(state_path),
        "run_id": run_id_value,
        "status": state["status"],
        "collected": [{"request_id": result.get("request_id"), "status": result.get("status"), "artifact_dir": result.get("artifact_dir")} for result in collected],
        "missing_results": missing_results,
        "gate_results": [{"gate_id": result.get("gate_id"), "status": result.get("status"), "trusted": result.get("trusted"), "reason": result.get("reason")} for result in gate_results],
        "warnings": warnings,
        "next_step": next_step,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2 if args.pretty else None))
    return 1 if state["status"] in {"blocked", "validation_required"} else 0


def command_resolve_validation(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    errors, warnings = validate_state(state)
    if errors:
        print(json.dumps({"state": str(state_path), "valid": False, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2 if args.pretty else None))
        return 2

    project = Path(state["project"]["path"])
    request = next(
        (
            item
            for item in state.get("agent_requests", [])
            if isinstance(item, dict) and item.get("id") == args.request
        ),
        None,
    )
    if not request:
        print(json.dumps({"state": str(state_path), "resolved": False, "error": f"request not found: {args.request}"}, ensure_ascii=False, indent=2 if args.pretty else None))
        return 2
    if request.get("status") != "validation_required" and not args.force:
        print(
            json.dumps(
                {
                    "state": str(state_path),
                    "resolved": False,
                    "request_id": args.request,
                    "status": request.get("status"),
                    "error": "request is not validation_required; pass --force to attach evidence anyway",
                },
                ensure_ascii=False,
                indent=2 if args.pretty else None,
            )
        )
        return 1

    evidence_paths: list[str] = []
    missing_evidence: list[str] = []
    for raw_path in args.evidence or []:
        evidence_path = Path(raw_path).expanduser()
        if not evidence_path.is_absolute():
            evidence_path = project / evidence_path
        if evidence_path.exists():
            evidence_paths.append(str(evidence_path))
        else:
            missing_evidence.append(str(evidence_path))
    if missing_evidence:
        print(
            json.dumps(
                {"state": str(state_path), "resolved": False, "request_id": args.request, "missing_evidence": missing_evidence},
                ensure_ascii=False,
                indent=2 if args.pretty else None,
            )
        )
        return 2

    previous_status = request.get("status")
    resolved_at = now_iso()
    request["status"] = "completed"
    request["validation_resolved_at"] = resolved_at
    request["validation_evidence"] = sorted(set(request.get("validation_evidence", []) + evidence_paths))
    if args.note:
        request["validation_note"] = args.note
    request["artifacts"] = sorted(set(request.get("artifacts", []) + evidence_paths))

    state.setdefault("agent_results", []).append(
        {
            "run_id": request.get("last_run_id") or state.get("runtime", {}).get("last_run_id"),
            "request_id": args.request,
            "agent_type": request.get("agent_type"),
            "backend": "validation_resolution",
            "status": "completed",
            "previous_status": previous_status,
            "ended_at": resolved_at,
            "artifact_paths": evidence_paths,
            "findings_or_risks": [],
            "next_step": args.note or "validation resolved with independent evidence",
        }
    )
    state["artifacts"] = sorted(set(state.get("artifacts", []) + evidence_paths))
    update_stage_states_from_requests(state)
    state["status"] = "running"
    progress_path = append_progress(
        state,
        {
            "event": "validation_resolved",
            "request_id": args.request,
            "previous_status": previous_status,
            "evidence": evidence_paths,
            "note": args.note,
        },
    )
    state["run_log"] = {
        "current_owner": "Release",
        "last_command": "service_factory.py resolve-validation",
        "last_artifact": str(progress_path),
        "blocked_reason": None,
        "next_step": "dispatch next queued agent requests",
    }
    state["updated_at"] = now_iso()
    write_state(state_path, state)
    result = {
        "state": str(state_path),
        "resolved": True,
        "request_id": args.request,
        "previous_status": previous_status,
        "status": "completed",
        "evidence": evidence_paths,
        "next_step": state["run_log"]["next_step"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def command_handoff(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    out_dir = project_sot_dir(state)
    out_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = out_dir / "handoff-latest.md"
    handoff = render_handoff(state, state_path)
    handoff_path.write_text(handoff, encoding="utf-8")
    progress_path = out_dir / "progress.jsonl"
    progress = {"timestamp": now_iso(), "factory_id": state.get("factory_id"), "status": state.get("status"), "handoff": str(handoff_path)}
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(progress, ensure_ascii=False) + "\n")
    state["run_log"] = {
        "current_owner": "Release",
        "last_command": "service_factory.py handoff",
        "last_artifact": str(handoff_path),
        "blocked_reason": state.get("run_log", {}).get("blocked_reason"),
        "next_step": state.get("run_log", {}).get("next_step") or "resume from first queued agent request",
        "completion_claim_guard": completion_claim_guard(state),
    }
    state["artifacts"] = sorted(set(state.get("artifacts", []) + [str(handoff_path), str(progress_path)]))
    write_state(state_path, state)
    print(json.dumps({"handoff": str(handoff_path), "progress": str(progress_path)}, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def command_review_report(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    out_dir = project_sot_dir(state)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "artifact-review.md"
    report_path.write_text(render_review_report(state, state_path), encoding="utf-8")
    state["artifacts"] = sorted(set(state.get("artifacts", []) + [str(report_path)]))
    state["run_log"] = {
        "current_owner": "Release",
        "last_command": "service_factory.py review-report",
        "last_artifact": str(report_path),
        "blocked_reason": state.get("run_log", {}).get("blocked_reason"),
        "next_step": state.get("run_log", {}).get("next_step") or "review generated artifacts",
        "completion_claim_guard": completion_claim_guard(state),
    }
    write_state(state_path, state)
    print(json.dumps({"report": str(report_path)}, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def command_recovery_report(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    out_dir = project_sot_dir(state)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "recovery-proof.md"
    report_path.write_text(render_recovery_report(state, state_path), encoding="utf-8")
    progress_path = append_progress(
        state,
        {
            "event": "recovery_report",
            "report": str(report_path),
            "recovered_requests": len(find_recovery_pairs(state)),
        },
    )
    state["artifacts"] = sorted(set(state.get("artifacts", []) + [str(report_path), str(progress_path)]))
    state["run_log"] = {
        "current_owner": "Release",
        "last_command": "service_factory.py recovery-report",
        "last_artifact": str(report_path),
        "blocked_reason": None,
        "next_step": "rerun readiness assessment",
    }
    write_state(state_path, state)
    print(json.dumps({"report": str(report_path), "progress": str(progress_path)}, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def command_assess(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    state = load_state(state_path)
    ensure_operating_contract(state)
    ensure_stella_control_plane(state)
    assessment = assess_antigravity_readiness(state)
    if args.write_report:
        out_dir = project_sot_dir(state)
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / "antigravity-readiness.md"
        report_path.write_text(render_readiness_report(state, state_path, assessment), encoding="utf-8")
        state["artifacts"] = sorted(set(state.get("artifacts", []) + [str(report_path)]))
        state["readiness"] = assessment["verdict"]
        state["status"] = "validation_required" if assessment.get("primary_blocker") else "running"
        runtime = state.get("runtime") if isinstance(state.get("runtime"), dict) else {}
        runtime["status"] = state["status"]
        state["runtime"] = runtime
        state["run_log"] = {
            "current_owner": "Release",
            "last_command": "service_factory.py assess",
            "last_artifact": str(report_path),
            "blocked_reason": assessment["primary_blocker"],
            "next_step": assessment["next_step"],
            "completion_claim_guard": assessment.get("completion_claim_guard", completion_claim_guard(state, assessment)),
        }
        write_state(state_path, state)
        assessment["report"] = str(report_path)
    print(json.dumps(assessment, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def command_autopilot(args: argparse.Namespace) -> int:
    state_path = resolve_state_path(args)
    if not state_path.exists():
        if not args.project or not args.goal:
            print(
                json.dumps(
                    {
                        "state": str(state_path),
                        "status": "blocked",
                        "error": "autopilot needs --goal when state does not exist",
                    },
                    ensure_ascii=False,
                    indent=2 if args.pretty else None,
                )
            )
            return 2
        state = build_state(
            Path(args.project),
            args.goal,
            args.mode,
            forbidden=getattr(args, "forbidden", None),
            definition_of_done=getattr(args, "dod", None),
            approval_delegation=getattr(args, "approval_delegation", None),
        )
        write_new_state(state_path, state)

    worker = SCRIPT_DIR / "service_factory_local_worker.py"
    command_template = (
        f"{sys.executable} {worker} "
        "--artifact-dir {artifact_dir} "
        "--request-id {request_id} "
        "--agent-type {agent_type} "
        "--state-file {state_file} "
        "--project {project} "
        "--prompt-file {prompt_file} "
        "--worktree {worktree} "
        "--run-id {run_id}"
    )
    steps: list[dict[str, Any]] = []

    def run_step(argv: list[str]) -> dict[str, Any]:
        proc = subprocess.run(argv, text=True, capture_output=True, check=False)
        step: dict[str, Any] = {
            "argv": argv,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
        if proc.stdout.strip():
            try:
                step["json"] = json.loads(proc.stdout)
            except json.JSONDecodeError:
                step["json"] = None
        steps.append(step)
        return step

    plan_step = run_step([sys.executable, str(Path(__file__).resolve()), "plan", "--state", str(state_path), "--pretty"])
    plan_json = plan_step.get("json") if isinstance(plan_step.get("json"), dict) else {}
    if plan_step.get("returncode") == 3 or plan_json.get("intake_clarification_required"):
        # intake 4항목 미충족 — max_cycles 공회전하지 않고 즉시 멈춰 사용자에게 되묻는다.
        print(
            json.dumps(
                {
                    "state": str(state_path),
                    "status": "intake_clarification_required",
                    "missing_fields": plan_json.get("missing_fields", []),
                    "clarification_questions": plan_json.get("clarification_questions", []),
                    "next_step": plan_json.get("next_step")
                    or "fill intake fields: service_factory.py intake --project <p> --set <field> --value \"<answer>\"",
                },
                ensure_ascii=False,
                indent=2 if args.pretty else None,
            )
        )
        return 3
    planned_state = load_state(state_path)
    if downgrade_unverified_mandatory_requests(planned_state):
        planned_state["run_log"] = {
            "current_owner": "Release",
            "last_command": "service_factory.py autopilot",
            "last_artifact": str(state_path),
            "blocked_reason": "mandatory_verification_chain",
            "next_step": "rerun mandatory requests with specialist evidence",
        }
        write_state(state_path, planned_state)
    last_assessment: dict[str, Any] | None = None
    stopped_reason = "max_cycles_reached"

    for _ in range(max(1, args.max_cycles)):
        run_result = run_step(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "run",
                "--state",
                str(state_path),
                "--backend",
                "command",
                "--agent-command-template",
                command_template,
                "--max-requests",
                str(args.max_requests),
                "--timeout-seconds",
                str(args.timeout_seconds),
                "--pretty",
            ]
        )
        run_json = run_result.get("json") or {}
        if isinstance(run_json, dict) and run_json.get("status") == "blocked":
            stopped_reason = "blocked"
            break
        if isinstance(run_json, dict) and not run_json.get("selected_requests"):
            fresh_state = load_state(state_path)
            open_requests = [
                request
                for request in fresh_state.get("agent_requests", [])
                if isinstance(request, dict)
                and request.get("status") in {"queued", "failed", "validation_required"}
            ]
            if open_requests:
                fresh_state["status"] = "blocked"
                fresh_state["run_log"] = {
                    "current_owner": "Release",
                    "last_command": "service_factory.py autopilot",
                    "last_artifact": str(state_path),
                    "blocked_reason": "no_dispatchable_requests",
                    "next_step": "resolve unmet stage dependencies or add a dispatchable implementation request",
                }
                write_state(state_path, fresh_state)
                stopped_reason = "no_dispatchable_requests"
                break

        run_step([sys.executable, str(Path(__file__).resolve()), "review-report", "--state", str(state_path), "--pretty"])
        run_step([sys.executable, str(Path(__file__).resolve()), "handoff", "--state", str(state_path), "--pretty"])
        run_step([sys.executable, str(Path(__file__).resolve()), "recovery-report", "--state", str(state_path), "--pretty"])
        assessment_step = run_step(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "assess",
                "--state",
                str(state_path),
                "--write-report",
                "--pretty",
            ]
        )
        assessment_json = assessment_step.get("json")
        if isinstance(assessment_json, dict):
            last_assessment = assessment_json
            if assessment_json.get("verdict") == "pilot_ready":
                stopped_reason = "pilot_ready"
                break
            if assessment_json.get("primary_blocker") == "missing_capabilities":
                stopped_reason = "missing_capabilities"
                break

        fresh_state = load_state(state_path)
        blocked_requests = [
            request
            for request in fresh_state.get("agent_requests", [])
            if isinstance(request, dict) and request.get("status") == "blocked"
        ]
        if blocked_requests:
            stopped_reason = "blocked"
            break
        queued_or_open = [
            request
            for request in fresh_state.get("agent_requests", [])
            if isinstance(request, dict)
            and request.get("status") in {"queued", "failed", "validation_required"}
        ]
        if not queued_or_open:
            stopped_reason = "no_open_requests"
            break

    if last_assessment is None:
        assessment_step = run_step(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "assess",
                "--state",
                str(state_path),
                "--write-report",
                "--pretty",
            ]
        )
        if isinstance(assessment_step.get("json"), dict):
            last_assessment = assessment_step["json"]
    if last_assessment and last_assessment.get("verdict") == "pilot_ready":
        fresh_state = load_state(state_path)
        fresh_state["status"] = "running"
        fresh_state["readiness"] = "pilot_ready"
        fresh_state["run_log"] = {
            "current_owner": "Release",
            "last_command": "service_factory.py autopilot",
            "last_artifact": str(project_sot_dir(fresh_state) / "antigravity-readiness.md"),
            "blocked_reason": None,
            "next_step": last_assessment.get("next_step"),
        }
        write_state(state_path, fresh_state)

    validate_step = run_step([sys.executable, str(Path(__file__).resolve()), "validate", "--state", str(state_path), "--pretty"])

    result = {
        "state": str(state_path),
        "status": "completed"
        if last_assessment and last_assessment.get("verdict") == "pilot_ready"
        else "validation_required",
        "stopped_reason": stopped_reason,
        "assessment": last_assessment,
        "valid": (validate_step.get("json") or {}).get("valid"),
        "steps": steps,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if result["status"] == "completed" else 1


def render_handoff(state: dict[str, Any], state_path: Path) -> str:
    counts: dict[str, int] = {name: 0 for name in sorted(QUEUE_STATES)}
    for stage in state.get("stages", []):
        if isinstance(stage, dict) and stage.get("state") in counts:
            counts[stage["state"]] += 1
    requests = [request for request in state.get("agent_requests", []) if isinstance(request, dict)]
    queued = [request.get("id") for request in requests if request.get("status") == "queued"]
    open_requests = [request for request in requests if request.get("status") in {"queued", "running", "blocked", "validation_required", "failed"}]
    current_request = open_requests[0] if open_requests else None
    current_stage = str(current_request.get("stage")) if current_request else None
    matching_stage = next((stage for stage in state.get("stages", []) if isinstance(stage, dict) and stage.get("id") == current_stage), {})
    latest_result = next(
        (
            result
            for result in reversed(state.get("agent_results", []))
            if isinstance(result, dict) and (not current_request or result.get("request_id") == current_request.get("id"))
        ),
        {},
    )
    mandatory_stage_ids = {"verification", "security_review", "deployment_readiness", "final_audit"}
    mandatory_remaining = [
        request.get("id")
        for request in requests
        if request.get("stage") in mandatory_stage_ids and request.get("status") != "completed"
    ]
    retry_count = sum(
        1
        for result in state.get("agent_results", [])
        if isinstance(result, dict) and current_request and result.get("request_id") == current_request.get("id")
    )
    handoff_payload = {
        "factory_id": state.get("factory_id"),
        "request_id": current_request.get("id") if current_request else None,
        "run_id": current_request.get("last_run_id") if current_request else state.get("runtime", {}).get("last_run_id"),
        "stage": current_stage,
        "command_owner": state.get("command_owner"),
        "current_owner": state.get("run_log", {}).get("current_owner"),
        "execution_controller": state.get("run_log", {}).get("execution_controller"),
        "successor_role": current_request.get("agent_type") if current_request else None,
        "status": current_request.get("status") if current_request else state.get("status"),
        "backend": latest_result.get("backend") or state.get("runtime", {}).get("backend"),
        "last_command": state.get("run_log", {}).get("last_command"),
        "last_artifact": state.get("run_log", {}).get("last_artifact"),
        "failure_category": latest_result.get("failure_category") or (current_request or {}).get("failure_class"),
        "blocked_reason": state.get("run_log", {}).get("blocked_reason"),
        "next_step": state.get("run_log", {}).get("next_step"),
        "owned_paths": current_request.get("owned_paths", []) if current_request else [],
        "pending_artifacts": current_request.get("artifacts", []) if current_request else [],
        "approval_gate_snapshot": state.get("gates", []),
        "agent_topology_snapshot": {
            "version": state.get("agent_topology", {}).get("version"),
            "blueprints": state.get("agent_topology", {}).get("blueprint_count"),
            "instances": state.get("agent_topology", {}).get("instance_count"),
            "kanban_role": state.get("agent_topology", {}).get("kanban_role"),
        },
        "mandatory_requests_remaining": mandatory_remaining,
        "retry_count": retry_count,
        "respawn_eligible": bool(current_request and current_request.get("status") in {"blocked", "validation_required", "failed"}),
        "lease_owner": matching_stage.get("owner") if isinstance(matching_stage, dict) else None,
        "lease_expires_at": None,
        "resume_command": f"python3 {Path(__file__).resolve()} run --state {state_path} --request {current_request.get('id')} --backend command" if current_request else f"python3 {Path(__file__).resolve()} status --state {state_path}",
        "completion_claim_guard": completion_claim_guard(state),
    }
    return f"""# Service Factory Handoff

factory_id: {state.get("factory_id")}
status: {state.get("status")}
state_file: {state_path}
updated_at: {now_iso()}

## Goal
{state.get("goal")}

## Current Run Log
```json
{json.dumps(state.get("run_log", {}), ensure_ascii=False, indent=2)}
```

## Handoff Contract
```json
{json.dumps(handoff_payload, ensure_ascii=False, indent=2)}
```

## Stage Counts
```json
{json.dumps(counts, ensure_ascii=False, indent=2)}
```

## Queued Agent Requests
```json
{json.dumps(queued, ensure_ascii=False, indent=2)}
```

## Missing Capabilities
```json
{json.dumps(state.get("missing_capabilities", []), ensure_ascii=False, indent=2)}
```

## Operating Contract
```json
{json.dumps(state.get("operating_contract", {}), ensure_ascii=False, indent=2)}
```

## Resume Rule
Read this handoff, then `SOT/service-factory-state.json`. Do not start new work before checking `run_log.next_step`, queued agent requests, file leases, and approval gates.
"""


def render_review_report(state: dict[str, Any], state_path: Path) -> str:
    errors, warnings = validate_state(state)
    gates = state.get("gates", [])
    requests = state.get("agent_requests", [])
    guard = completion_claim_guard(state)
    return f"""# Service Factory Artifact Review

factory_id: {state.get("factory_id")}
state_file: {state_path}
generated_at: {now_iso()}

## Validation
- valid: {not errors}
- errors: {len(errors)}
- warnings: {len(warnings)}

## Completion Claim Guard
```json
{json.dumps(guard, ensure_ascii=False, indent=2)}
```

## Approval Gates
```json
{json.dumps(gates, ensure_ascii=False, indent=2)}
```

## Agent Requests
```json
{json.dumps(requests, ensure_ascii=False, indent=2)}
```

## Agent Topology
```json
{json.dumps(state.get("agent_topology", {}), ensure_ascii=False, indent=2)}
```

## Execution Plan
```json
{json.dumps(state.get("execution_plan", {}), ensure_ascii=False, indent=2)}
```

## Operating Contract
```json
{json.dumps(state.get("operating_contract", {}), ensure_ascii=False, indent=2)}
```

## Known Issues
```json
{json.dumps(state.get("known_issues", []), ensure_ascii=False, indent=2)}
```
"""


def find_recovery_pairs(state: dict[str, Any]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    by_request: dict[str, list[dict[str, Any]]] = {}
    for result in state.get("agent_results", []):
        if isinstance(result, dict):
            by_request.setdefault(str(result.get("request_id")), []).append(result)
    for request_id, results in by_request.items():
        predecessors = [
            result
            for result in results
            if result.get("status") in {"blocked", "failed", "validation_required"}
        ]
        successors = [
            result
            for result in results
            if result.get("status") == "completed" and result.get("backend") in AUTONOMOUS_BACKENDS
        ]
        if predecessors and successors:
            predecessor = predecessors[-1]
            successor = successors[-1]
            if predecessor.get("run_id") != successor.get("run_id"):
                pairs.append(
                    {
                        "request_id": request_id,
                        "predecessor_run_id": predecessor.get("run_id"),
                        "predecessor_backend": predecessor.get("backend"),
                        "predecessor_status": predecessor.get("status"),
                        "predecessor_failure_category": predecessor.get("failure_category"),
                        "successor_run_id": successor.get("run_id"),
                        "successor_backend": successor.get("backend"),
                        "successor_status": successor.get("status"),
                        "successor_artifact_dir": successor.get("artifact_dir"),
                    }
                )
    return pairs


def render_recovery_report(state: dict[str, Any], state_path: Path) -> str:
    pairs = find_recovery_pairs(state)
    return f"""# Service Factory Recovery Proof

factory_id: {state.get("factory_id")}
state_file: {state_path}
generated_at: {now_iso()}

## Verdict

- recovery_proof: {"ready" if pairs else "missing"}
- recovered_requests: {len(pairs)}

## Recovery Pairs
```json
{json.dumps(pairs, ensure_ascii=False, indent=2)}
```

## Interpretation

This report proves the recovery path when at least one mandatory request has a failed, blocked, or validation-required predecessor run and a later managed backend successor run with completed evidence. It is a local-staging recovery proof, not a production rollback drill.
"""


def latest_completed_result_for_request(state: dict[str, Any], request_id: str) -> dict[str, Any] | None:
    for result in reversed(state.get("agent_results", [])):
        if (
            isinstance(result, dict)
            and result.get("request_id") == request_id
            and result.get("status") == "completed"
        ):
            return result
    return None


def mandatory_request_verified(state: dict[str, Any], request: dict[str, Any]) -> bool:
    result = latest_completed_result_for_request(state, str(request.get("id", "")))
    if not result:
        return False
    child_result = result.get("child_result") if isinstance(result.get("child_result"), dict) else {}
    evidence_class = str(child_result.get("evidence_class") or result.get("evidence_class") or "")
    accepted_classes = {
        "specialist_review",
        "independent_review",
        "runtime_probe",
        "security_review",
        "deployment_readiness",
        "final_audit",
        "product_security_audit",
        "release_audit",
    }
    if evidence_class in accepted_classes:
        return True
    if result.get("backend") == "validation_resolution" and result.get("artifact_paths"):
        return True
    if result.get("backend") == "codex-exec" and result.get("artifact_paths"):
        return True
    return False


def downgrade_unverified_mandatory_requests(state: dict[str, Any]) -> int:
    mandatory_stage_ids = {"verification", "security_review", "deployment_readiness", "final_audit"}
    changed = 0
    for request in state.get("agent_requests", []):
        if not isinstance(request, dict) or request.get("stage") not in mandatory_stage_ids:
            continue
        if request.get("status") == "completed" and not mandatory_request_verified(state, request):
            request["status"] = "validation_required"
            request["failure_class"] = "insufficient_independent_evidence"
            request["next_step"] = "spawn or attach specialist evidence for this mandatory stage"
            changed += 1
    if changed:
        update_stage_states_from_requests(state)
    return changed


def runtime_probe_request(state: dict[str, Any]) -> dict[str, Any] | None:
    for request in state.get("agent_requests", []):
        if isinstance(request, dict) and str(request.get("id")) == "verification::runtime_probe":
            return request
    return None


def runtime_probe_verified(state: dict[str, Any]) -> bool:
    request = runtime_probe_request(state)
    if not request:
        return False
    return mandatory_request_verified(state, request)


def completion_claim_guard(state: dict[str, Any], assessment: dict[str, Any] | None = None) -> dict[str, Any]:
    probe_ok = runtime_probe_verified(state)
    blockers: list[str] = []
    if not probe_ok:
        blockers.append("probe_not_verified")
    if assessment and assessment.get("primary_blocker"):
        blockers.append(str(assessment.get("primary_blocker")))
    if state.get("status") in {"blocked", "validation_required"}:
        blockers.append(f"state_{state.get('status')}")
    # 260603 — file_leases anti false-green: parallel_implementation/integration 진행 중인데
    # ledger 비어 있거나 write 충돌이면 완료 주장 차단 (service-factory.md 파일 Lease 규칙 정합).
    blockers.extend(_fl_file_leases_blockers(state))
    return {
        "probe_required": True,
        "probe_verified": probe_ok,
        "completion_claim_allowed": len(blockers) == 0,
        "blockers": blockers,
    }


def assess_antigravity_readiness(state: dict[str, Any]) -> dict[str, Any]:
    ensure_operating_contract(state)
    ensure_stella_control_plane(state)
    execution_plan = state.get("execution_plan", {})
    execution_mode = execution_plan.get("mode")
    agent_requests = state.get("agent_requests", [])
    agent_results = state.get("agent_results", [])
    gate_results = state.get("gate_results", [])
    missing = state.get("missing_capabilities", [])
    artifacts = [str(item) for item in state.get("artifacts", [])]
    service_dir = project_sot_dir(state)
    contract = state.get("operating_contract") if isinstance(state.get("operating_contract"), dict) else {}
    phase_artifacts_ready = (
        (service_dir / "current-state.md").exists()
        and (service_dir / "research-dossier.md").exists()
        and (service_dir / "evidence-map.md").exists()
        and (service_dir / "research-qc.md").exists()
        and (service_dir / "development-plan.md").exists()
    )
    artifact_review_ready = any(path.endswith("artifact-review.md") for path in artifacts)
    handoff_artifact_ready = any(path.endswith("handoff-latest.md") for path in artifacts)
    handoff_required_fields = execution_plan.get("handoff", {}).get("required_fields", [])
    handoff_contract_ready = handoff_artifact_ready and isinstance(handoff_required_fields, list) and len(handoff_required_fields) >= 20
    recovery_pairs = find_recovery_pairs(state)
    recovery_artifact_ready = any(path.endswith("recovery-proof.md") for path in artifacts)
    recovery_proof_ready = bool(recovery_pairs) and recovery_artifact_ready
    autonomous_results = [
        result
        for result in agent_results
        if isinstance(result, dict)
        and result.get("status") == "completed"
        and result.get("backend") in AUTONOMOUS_BACKENDS
    ]
    latest_autonomous_backend = str(autonomous_results[-1].get("backend")) if autonomous_results else None
    spawn_runtime_mode = f"spawn_runtime_{latest_autonomous_backend}" if latest_autonomous_backend else (execution_mode or "not configured")
    bridge_results = [
        result
        for result in agent_results
        if isinstance(result, dict) and result.get("backend") == "codex_bridge"
    ]
    dispatched_requests = [
        request
        for request in agent_requests
        if isinstance(request, dict) and request.get("status") in {"dispatched", "running"}
    ]
    queued_requests = [
        request
        for request in agent_requests
        if isinstance(request, dict) and request.get("status") == "queued"
    ]
    mandatory_stage_ids = {"verification", "security_review", "deployment_readiness", "final_audit"}
    mandatory_requests = [
        request
        for request in agent_requests
        if isinstance(request, dict) and str(request.get("stage")) in mandatory_stage_ids
    ]
    open_mandatory_requests = [
        request
        for request in mandatory_requests
        if not mandatory_request_verified(state, request)
    ]
    completed_mandatory_requests = [
        request
        for request in mandatory_requests
        if mandatory_request_verified(state, request)
    ]
    probe_verified = runtime_probe_verified(state)
    mandatory_status_counts: dict[str, int] = {}
    for request in mandatory_requests:
        request_status = str(request.get("status") or "unknown")
        mandatory_status_counts[request_status] = mandatory_status_counts.get(request_status, 0) + 1
    topology = state.get("agent_topology") if isinstance(state.get("agent_topology"), dict) else {}
    run_log = state.get("run_log") if isinstance(state.get("run_log"), dict) else {}
    stella_command_ready = (
        state.get("command_owner") == STELLA_COMMAND_OWNER
        and run_log.get("command_owner") == STELLA_COMMAND_OWNER
        and run_log.get("current_owner") == STELLA_COMMAND_OWNER
        and run_log.get("execution_controller") == RELEASE_EXECUTION_CONTROLLER
    )
    topology_ready = (
        topology.get("command_owner") == STELLA_COMMAND_OWNER
        and topology.get("execution_controller") == RELEASE_EXECUTION_CONTROLLER
        and isinstance(topology.get("nodes"), list)
        and bool(topology.get("nodes"))
        and int(topology.get("blueprint_count") or 0) > 0
    )
    capabilities = [
        {
            "id": "stella_command_owner",
            "status": "ready" if stella_command_ready else "missing",
            "evidence": {
                "command_owner": state.get("command_owner"),
                "run_log_command_owner": run_log.get("command_owner"),
                "run_log_current_owner": run_log.get("current_owner"),
                "execution_controller": run_log.get("execution_controller"),
            },
        },
        {
            "id": "agent_topology",
            "status": "ready" if topology_ready else ("partial" if topology else "missing"),
            "evidence": {
                "version": topology.get("version"),
                "command_owner": topology.get("command_owner"),
                "blueprints": topology.get("blueprint_count"),
                "instances": topology.get("instance_count"),
                "kanban_role": topology.get("kanban_role"),
            },
        },
        {
            "id": "service_factory_state",
            "status": "ready" if state.get("stages") and state.get("gates") else "missing",
            "evidence": "state has stages and approval gates",
        },
        {
            "id": "state_plan_execute_contract",
            "status": "ready" if contract.get("version") == "state-plan-execute-v1" and phase_artifacts_ready else ("partial" if contract else "missing"),
            "evidence": {
                "contract_version": contract.get("version"),
                "required_order": contract.get("required_order"),
                "current_state_artifact": str(service_dir / "current-state.md"),
                "research_dossier_artifact": str(service_dir / "research-dossier.md"),
                "evidence_map_artifact": str(service_dir / "evidence-map.md"),
                "research_qc_artifact": str(service_dir / "research-qc.md"),
                "development_plan_artifact": str(service_dir / "development-plan.md"),
                "artifacts_ready": phase_artifacts_ready,
            },
        },
        {
            "id": "agent_runner_plan",
            "status": "ready" if agent_results else ("partial" if agent_requests else "missing"),
            "evidence": f"{len(agent_requests)} agent request(s), {len(agent_results)} result(s)",
        },
        {
            "id": "agent_foundry",
            "status": "ready" if state.get("foundry") is not None and not missing else ("partial" if state.get("foundry") is not None else "missing"),
            "evidence": f"{len(missing)} missing capability request(s)",
        },
        {
            "id": "spawn_runtime",
            "status": "ready" if autonomous_results else ("partial" if execution_mode and execution_mode != "plan_only_until_parent_spawns_agents" else "missing"),
            "evidence": {
                "mode": spawn_runtime_mode,
                "execution_plan_mode": execution_mode or "not configured",
                "agent_results": len(agent_results),
                "autonomous_results": len(autonomous_results),
                "bridge_results": len(bridge_results),
            },
        },
        {
            "id": "worktree_isolation",
            "status": "partial" if execution_plan.get("worktree_isolation", {}).get("enabled") else "missing",
            "evidence": execution_plan.get("worktree_isolation", {}),
        },
        {
            "id": "watchdog",
            "status": "ready" if execution_plan.get("watchdog", {}).get("enabled") and recovery_proof_ready else ("partial" if execution_plan.get("watchdog", {}).get("enabled") else "missing"),
            "evidence": {
                **execution_plan.get("watchdog", {}),
                "recovery_proof": recovery_proof_ready,
                "recovered_requests": len(recovery_pairs),
            },
        },
        {
            "id": "handoff_successor",
            "status": "ready" if handoff_contract_ready else ("partial" if execution_plan.get("handoff", {}).get("enabled") else "missing"),
            "evidence": {
                **execution_plan.get("handoff", {}),
                "handoff_latest": handoff_artifact_ready,
                "required_field_count": len(handoff_required_fields) if isinstance(handoff_required_fields, list) else 0,
            },
        },
        {
            "id": "artifact_review_surface",
            "status": "ready" if artifact_review_ready else "missing",
            "evidence": "artifact-review.md generated with state, gates, requests, execution plan, and known issues" if artifact_review_ready else "no artifact review report",
        },
        {
            "id": "automatic_gates",
            "status": "ready" if any(result.get("status") == "passed" for result in gate_results if isinstance(result, dict)) else ("partial" if execution_plan.get("automatic_gates") else "missing"),
            "evidence": {"configured": execution_plan.get("automatic_gates", []), "results": len(gate_results)},
        },
        {
            "id": "mandatory_verification_chain",
            "status": "ready" if mandatory_requests and not open_mandatory_requests else ("partial" if completed_mandatory_requests else "missing"),
            "evidence": {
                "mandatory_requests": len(mandatory_requests),
                "completed": len(completed_mandatory_requests),
                "open": len(open_mandatory_requests),
                "status_counts": mandatory_status_counts,
            },
        },
        {
            "id": "probe_required_for_completion",
            "status": "ready" if probe_verified else "missing",
            "evidence": {
                "probe_required": True,
                "probe_request_present": bool(runtime_probe_request(state)),
                "probe_verified": probe_verified,
            },
        },
        {
            "id": "recovery_proof",
            "status": "ready" if recovery_proof_ready else ("partial" if recovery_pairs else "missing"),
            "evidence": {
                "artifact": "recovery-proof.md" if recovery_artifact_ready else None,
                "recovered_requests": len(recovery_pairs),
            },
        },
    ]
    score_map = {"ready": 1.0, "partial": 0.5, "missing": 0.0}
    score = sum(score_map[item["status"]] for item in capabilities) / len(capabilities)
    spawn_runtime_status = next(
        (
            str(item.get("status"))
            for item in capabilities
            if isinstance(item, dict) and item.get("id") == "spawn_runtime"
        ),
        "missing",
    )
    primary_blocker = "spawn_runtime" if spawn_runtime_status != "ready" else None
    if not primary_blocker and not stella_command_ready:
        primary_blocker = "stella_command_owner"
    if not primary_blocker and not topology_ready:
        primary_blocker = "agent_topology"
    if not primary_blocker and (contract.get("version") != "state-plan-execute-v1" or not phase_artifacts_ready):
        primary_blocker = "state_plan_execute_contract"
    if not primary_blocker and missing:
        primary_blocker = "missing_capabilities"
    if not primary_blocker and open_mandatory_requests:
        primary_blocker = "mandatory_verification_chain"
    if not primary_blocker and not probe_verified:
        primary_blocker = "probe_required_for_completion"
    if not primary_blocker and not recovery_proof_ready:
        primary_blocker = "recovery_proof"
    pilot_ready = score >= 0.8 and spawn_runtime_status == "ready" and not primary_blocker
    if pilot_ready:
        next_step = "pilot_ready: use the managed Factory cycle for product-specific goals and attach specialist agents for real implementation work"
    elif primary_blocker == "spawn_runtime":
        next_step = "prove a managed spawn backend that executes agent_requests and records results without bridge-only handoff"
    elif primary_blocker == "stella_command_owner":
        next_step = "restore Stella as command_owner and Release as execution_controller before readiness promotion"
    elif primary_blocker == "agent_topology":
        next_step = "materialize AgentTopology with AgentBlueprint/AgentInstance/AgentManifest distinctions"
    elif primary_blocker == "state_plan_execute_contract":
        next_step = "complete current-state.md, research-dossier.md, evidence-map.md, research-qc.md, and development-plan.md before broad implementation or readiness promotion"
    elif primary_blocker == "missing_capabilities":
        next_step = "resolve missing capability manifests before spawning"
    elif primary_blocker == "mandatory_verification_chain":
        next_step = "complete open verification, security, deployment readiness, and final audit requests"
    elif primary_blocker == "probe_required_for_completion":
        next_step = "run Probe and collect a verified runtime_probe result before any completion report"
    elif primary_blocker == "recovery_proof":
        next_step = "write recovery-proof.md from a blocked predecessor and managed successor run"
    elif dispatched_requests:
        next_step = "spawn Codex subagents from dispatch files, then run service_factory.py collect"
    elif queued_requests and not dispatched_requests:
        next_step = "dispatch next queued agent requests"
    elif agent_results and not any(result.get("status") == "passed" for result in gate_results if isinstance(result, dict)):
        next_step = "run trusted gates and review collected artifacts"
    else:
        next_step = "continue dispatch/collect cycles until readiness reaches pilot_ready"
    return {
        "target": "Antigravity-like autonomous product delivery",
        "readiness_score": round(score, 2),
        "verdict": "pilot_ready" if pilot_ready else "foundation_ready_but_not_autonomous",
        "primary_blocker": primary_blocker,
        "next_step": next_step,
        "capabilities": capabilities,
        "completion_claim_guard": completion_claim_guard({**state, "status": "validation_required" if primary_blocker else state.get("status")}, {"primary_blocker": primary_blocker}),
    }


def render_readiness_report(state: dict[str, Any], state_path: Path, assessment: dict[str, Any]) -> str:
    if assessment["verdict"] == "pilot_ready":
        interpretation = "The current Service Factory now has a managed local runtime proof: it can inspect current state, write a goal-to-plan strategy, plan agent requests, execute command-backed worker cycles, collect machine-readable results, write recovery proof, pass factory validation, and close the mandatory verification chain. This is pilot-ready for local autonomous orchestration. It is still not a claim that every future product can be completed without specialist implementation agents; real product goals must attach the needed worker, Probe, security, release, and final-audit evidence."
    else:
        interpretation = "The current Service Factory can plan and document a multi-agent delivery run, propose missing agents, create subagent prompts, record handoff state, and generate review artifacts. It must preserve the current-state -> research-intelligence -> development-plan -> execution/verification order before implementation. It is not yet a fully autonomous Antigravity-class runtime because the local script does not directly spawn and monitor subagents. The next engineering milestone is a spawn adapter that reads `agent_requests`, starts the corresponding agents or worktrees, records results, reruns gates, and triggers watchdog/handoff recovery."
    return f"""# Antigravity-Like Delivery Readiness

factory_id: {state.get("factory_id")}
state_file: {state_path}
generated_at: {now_iso()}

## Verdict

- readiness_score: {assessment["readiness_score"]}
- verdict: {assessment["verdict"]}
- primary_blocker: {assessment["primary_blocker"]}
- next_step: {assessment["next_step"]}

## Capability Matrix

```json
{json.dumps(assessment["capabilities"], ensure_ascii=False, indent=2)}
```

## Interpretation

{interpretation}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Release Service Factory state helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create a new service-factory-state.json")
    init.add_argument("--project", required=True, help="project directory")
    init.add_argument("--goal", required=True, help="목표(Goal): service delivery goal")
    init.add_argument("--forbidden", help="금지선: 절대 하면 안 되는 것/건드리면 안 되는 영역")
    init.add_argument("--dod", dest="dod", help="완료기준(Definition of Done): 무엇이 충족되면 done 인가")
    init.add_argument("--approval-delegation", dest="approval_delegation", help="승인 위임 범위: 사람 확인 없이 자율 진행 허용 경계")
    init.add_argument("--mode", default="local-staging", choices=["repo-only", "local-staging", "production-candidate"])
    init.add_argument("--state", help="optional explicit state output path")
    init.add_argument("--pretty", action="store_true")
    init.set_defaults(func=command_init)

    intake = subparsers.add_parser("intake", help="show or fill the 4 intake-contract fields (goal/forbidden/dod/approval_delegation)")
    intake.add_argument("--project", help="project directory")
    intake.add_argument("--state", help="explicit state path")
    intake.add_argument("--pretty", action="store_true")
    intake.add_argument("--set", dest="set_field", choices=[spec["key"] for spec in _IC_FIELDS], help="채울 항목 key")
    intake.add_argument("--value", help="--set 항목에 채울 값")
    intake.set_defaults(func=command_intake)

    status = subparsers.add_parser("status", help="summarize an existing state file")
    status.add_argument("--project", help="project directory")
    status.add_argument("--state", help="explicit state path")
    status.add_argument("--pretty", action="store_true")
    status.set_defaults(func=command_status)

    validate = subparsers.add_parser("validate", help="validate an existing state file")
    validate.add_argument("--project", help="project directory")
    validate.add_argument("--state", help="explicit state path")
    validate.add_argument("--pretty", action="store_true")
    validate.set_defaults(func=command_validate)

    suggest = subparsers.add_parser("suggest", help="suggest dynamic roles from a goal")
    suggest.add_argument("--goal", required=True)
    suggest.add_argument("--pretty", action="store_true")
    suggest.set_defaults(func=command_suggest)

    plan = subparsers.add_parser("plan", help="create agent requests, prompts, foundry requests, and execution plan")
    plan.add_argument("--project", help="project directory")
    plan.add_argument("--state", help="explicit state path")
    plan.add_argument("--pretty", action="store_true")
    plan.add_argument("--fail-on-missing", action="store_true", help="exit 1 when new agent manifests are required")
    plan.add_argument("--allow-incomplete-intake", action="store_true", help="intake 4항목 미충족이어도 진행 (권장하지 않음)")
    plan.set_defaults(func=command_plan)

    run = subparsers.add_parser("run", help="execute one Service Factory runtime cycle")
    run.add_argument("--project", help="project directory")
    run.add_argument("--state", help="explicit state path")
    run.add_argument("--pretty", action="store_true")
    run.add_argument("--request", help="run a single agent request id")
    run.add_argument("--backend", default="manual", choices=["manual", "command", "codex-exec"], help="manual writes launch instructions; command executes an argv-only command template; codex-exec runs Codex CLI")
    run.add_argument("--agent-command-template", help="command template for command backend; placeholders: {prompt_file} {artifact_dir} {request_id} {agent_type} {worktree} {state_file} {project} {run_id}")
    run.add_argument("--max-requests", type=int, default=1, help="maximum agent requests to execute in this cycle")
    run.add_argument("--timeout-seconds", type=int, default=900)
    run.add_argument("--include-unavailable", action="store_true", help="attempt requests even when the agent manifest is missing")
    run.add_argument("--include-repo-gates", action="store_true", help="run repo-controlled optional gates such as npm test or pytest")
    run.add_argument("--skip-gates", action="store_true", help="skip automatic gates for this cycle")
    run.add_argument("--no-worktrees", action="store_true", help="do not prepare per-request worktrees")
    run.add_argument("--allow-paid-agent-call", action="store_true", help="allow codex-exec backend to make a Codex model call")
    run.add_argument("--no-auto-plan", dest="auto_plan", action="store_false", help="do not generate a plan when agent_requests is empty")
    run.add_argument("--allow-incomplete-intake", action="store_true", help="intake 4항목 미충족이어도 진행 (권장하지 않음)")
    run.set_defaults(func=command_run, auto_plan=True)

    dispatch = subparsers.add_parser("dispatch", help="create Codex bridge dispatch packets for queued agent requests")
    dispatch.add_argument("--project", help="project directory")
    dispatch.add_argument("--state", help="explicit state path")
    dispatch.add_argument("--pretty", action="store_true")
    dispatch.add_argument("--request", help="dispatch a single agent request id")
    dispatch.add_argument("--max-requests", type=int, default=3, help="maximum agent requests to dispatch in this cycle")
    dispatch.add_argument("--include-unavailable", action="store_true", help="dispatch requests even when the agent manifest is missing")
    dispatch.add_argument("--no-worktrees", action="store_true", help="do not prepare per-request worktrees")
    dispatch.add_argument("--no-auto-plan", dest="auto_plan", action="store_false", help="do not generate a plan when agent_requests is empty")
    dispatch.add_argument("--allow-incomplete-intake", action="store_true", help="intake 4항목 미충족이어도 진행 (권장하지 않음)")
    dispatch.set_defaults(func=command_dispatch, auto_plan=True)

    dispatch_workflow = subparsers.add_parser(
        "dispatch-workflow",
        help=(
            "stage-level fan-out via Claude Code Workflow tool (dynamic_workflow spawn_runtime). "
            "writes dispatch.workflow.js + dispatch.instructions.md; parent agent runs Workflow tool."
        ),
    )
    dispatch_workflow.add_argument("--project", help="project directory")
    dispatch_workflow.add_argument("--state", help="explicit state path")
    dispatch_workflow.add_argument("--pretty", action="store_true")
    dispatch_workflow.add_argument("--request", help="restrict to a single agent request id")
    dispatch_workflow.add_argument("--stage", help="restrict to requests of a specific stage id")
    dispatch_workflow.add_argument(
        "--max-requests",
        type=int,
        default=12,
        help="maximum agent requests to bundle into one workflow run (state.limits.max_child_agents 와 정합)",
    )
    dispatch_workflow.add_argument(
        "--max-parallel",
        type=int,
        default=None,
        help=(
            f"workflow parallel batch size; defaults to state.limits.max_parallel_agents "
            f"(or {_DW_DEFAULT_MAX_PARALLEL} if not set)"
        ),
    )
    dispatch_workflow.add_argument(
        "--no-auto-plan",
        dest="auto_plan",
        action="store_false",
        help="do not generate a plan when agent_requests is empty",
    )
    dispatch_workflow.add_argument("--allow-incomplete-intake", action="store_true", help="intake 4항목 미충족이어도 진행 (권장하지 않음)")
    dispatch_workflow.set_defaults(func=command_dispatch_workflow, auto_plan=True)

    collect = subparsers.add_parser("collect", help="collect Codex bridge result.json files into state")
    collect.add_argument("--project", help="project directory")
    collect.add_argument("--state", help="explicit state path")
    collect.add_argument("--pretty", action="store_true")
    collect.add_argument("--request", help="collect a single agent request id")
    collect.add_argument("--run-id", help="run id to collect; defaults to runtime.last_run_id or each request last_run_id")
    collect.add_argument("--timeout-seconds", type=int, default=900)
    collect.add_argument("--include-repo-gates", action="store_true", help="run repo-controlled optional gates such as npm test or pytest")
    collect.add_argument("--skip-gates", action="store_true", help="skip automatic gates for this collection")
    collect.set_defaults(func=command_collect)

    resolve_validation = subparsers.add_parser("resolve-validation", help="promote a validation_required request after independent evidence is attached")
    resolve_validation.add_argument("--project", help="project directory")
    resolve_validation.add_argument("--state", help="explicit state path")
    resolve_validation.add_argument("--pretty", action="store_true")
    resolve_validation.add_argument("--request", required=True, help="agent request id to resolve")
    resolve_validation.add_argument("--evidence", action="append", required=True, help="evidence file path; may be passed more than once")
    resolve_validation.add_argument("--note", help="short resolution note")
    resolve_validation.add_argument("--force", action="store_true", help="attach evidence even if request is not validation_required")
    resolve_validation.set_defaults(func=command_resolve_validation)

    handoff = subparsers.add_parser("handoff", help="write handoff-latest.md and append progress.jsonl")
    handoff.add_argument("--project", help="project directory")
    handoff.add_argument("--state", help="explicit state path")
    handoff.add_argument("--pretty", action="store_true")
    handoff.set_defaults(func=command_handoff)

    review_report = subparsers.add_parser("review-report", help="write an artifact review report for humans and successor agents")
    review_report.add_argument("--project", help="project directory")
    review_report.add_argument("--state", help="explicit state path")
    review_report.add_argument("--pretty", action="store_true")
    review_report.set_defaults(func=command_review_report)

    recovery_report = subparsers.add_parser("recovery-report", help="write recovery-proof.md from blocked/manual predecessors and managed successors")
    recovery_report.add_argument("--project", help="project directory")
    recovery_report.add_argument("--state", help="explicit state path")
    recovery_report.add_argument("--pretty", action="store_true")
    recovery_report.set_defaults(func=command_recovery_report)

    assess = subparsers.add_parser("assess", help="assess readiness for Antigravity-like autonomous delivery")
    assess.add_argument("--project", help="project directory")
    assess.add_argument("--state", help="explicit state path")
    assess.add_argument("--pretty", action="store_true")
    assess.add_argument("--write-report", action="store_true")
    assess.set_defaults(func=command_assess)

    autopilot = subparsers.add_parser("autopilot", help="run managed Service Factory cycles until pilot_ready or a concrete blocker")
    autopilot.add_argument("--project", help="project directory")
    autopilot.add_argument("--state", help="explicit state path")
    autopilot.add_argument("--goal", help="service delivery goal when state does not exist")
    autopilot.add_argument("--forbidden", help="금지선 (intake 4항목)")
    autopilot.add_argument("--dod", dest="dod", help="완료기준 Definition of Done (intake 4항목)")
    autopilot.add_argument("--approval-delegation", dest="approval_delegation", help="승인 위임 범위 (intake 4항목)")
    autopilot.add_argument("--mode", default="local-staging", choices=["repo-only", "local-staging", "production-candidate"])
    autopilot.add_argument("--pretty", action="store_true")
    autopilot.add_argument("--max-cycles", type=int, default=12)
    autopilot.add_argument("--max-requests", type=int, default=1)
    autopilot.add_argument("--timeout-seconds", type=int, default=900)
    autopilot.set_defaults(func=command_autopilot)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileExistsError as exc:
        print(f"error: state already exists: {exc.filename}", file=sys.stderr)
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
