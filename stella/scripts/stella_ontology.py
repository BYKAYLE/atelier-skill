#!/usr/bin/env python3
"""Stella ontology helper.

Usage:
  stella_ontology.py validate
  stella_ontology.py normalize "대표님 지시"
  stella_ontology.py explain kansicrich
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path.home() / ".claude" / "skills" / "stella"
ONTOLOGY = ROOT / "SOT" / "ontology"


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def all_yaml_files() -> list[Path]:
    return sorted(ONTOLOGY.rglob("*.yaml"))


ALLOWED_DELEGATED_TO = {"Release", "NightLab", "self"}
ALLOWED_EXECUTORS = {"Codex", "Claude", "Hermes", "Ouroboros", "Probe", "Edison", "NotebookLM", "Edison + NotebookLM"}


def validate() -> int:
    ok = True
    for path in all_yaml_files():
        try:
            data = load_yaml(path)
            if path.name != "normalized-task.yaml" and "version" not in data:
                print(f"WARN missing version: {path}")
            print(f"OK {path}")
        except Exception as exc:  # pragma: no cover - diagnostic script
            ok = False
            print(f"FAIL {path}: {exc}")

    try:
        intents = load_yaml(ONTOLOGY / "intent.yaml").get("intents", {})
        profiles = load_yaml(ONTOLOGY / "evidence.yaml").get("evidence_profiles", {})
        routing = load_yaml(ONTOLOGY / "routing.yaml")
        template = load_yaml(ONTOLOGY / "templates" / "normalized-task.yaml")
        template_keys = set(template.keys())
        required_template_keys = {
            "next_actor",
            "command_owner",
            "delegated_to",
            "executor",
            "verification",
            "state_role",
            "board_role",
            "agent_topology",
        }
        missing_template_keys = required_template_keys - template_keys
        if missing_template_keys:
            ok = False
            print(f"FAIL normalized-task.yaml missing keys: {sorted(missing_template_keys)}")

        for route in routing.get("routes", []):
            route_id = route.get("id", "<missing-id>")
            intent_id = route.get("intent", "")
            profile_id = route.get("evidence_profile", "")
            if intent_id not in intents:
                ok = False
                print(f"FAIL {route_id}: unknown intent {intent_id!r}")
            if profile_id not in profiles:
                ok = False
                print(f"FAIL {route_id}: unknown evidence_profile {profile_id!r}")
            if route.get("next_actor") != "Stella":
                ok = False
                print(f"FAIL {route_id}: next_actor must be Stella")
            delegated_to = route.get("delegated_to", "")
            if delegated_to and delegated_to not in ALLOWED_DELEGATED_TO:
                ok = False
                print(f"FAIL {route_id}: invalid delegated_to {delegated_to!r}")
            executor = route.get("executor", "")
            if executor and executor not in ALLOWED_EXECUTORS:
                ok = False
                print(f"FAIL {route_id}: invalid executor {executor!r}")
    except Exception as exc:  # pragma: no cover - diagnostic script
        ok = False
        print(f"FAIL ontology cross-reference validation: {exc}")
    return 0 if ok else 1


def contains_any(text: str, values: list[str]) -> bool:
    lower = text.lower()
    return any(v.lower() in lower for v in values)


def compact_lower(text: str) -> str:
    return "".join(text.lower().split())


def is_service_factory_invocation(text: str) -> bool:
    lower = text.lower()
    compact = compact_lower(text)
    return (
        "스텔라팩토리" in compact
        or "stellafactory" in compact
        or "servicefactory" in compact
        or "안티그래비티" in text
        or "antigravity" in lower
        or "서비스개발공장" in compact
        or "자동으로끝까지" in compact
        or "최종제품까지" in compact
    )


def detect_target(text: str) -> tuple[str, str, str]:
    lower = text.lower()
    if "칸식리치" in text or "kansic" in lower or "오토리서치" in text or "autoresearch" in lower:
        return "kansicrich", "Service", "services/kansicrich.yaml"
    if "atelier" in lower or "아틀리에" in text:
        return "atelier", "Service", "services/atelier.yaml"
    if "bk-wiki" in lower or "bkwiki" in lower or "옵시디언" in text or "obsidian" in lower:
        return "bk-wiki", "Service", ""
    if (
        is_service_factory_invocation(text)
        or "service factory" in lower
        or "stella factory" in lower
        or "서비스 개발 공장" in text
        or "최종목표" in text
        or "최종 목표" in text
        or "자동으로 끝까지" in text
    ):
        return "service-factory", "Service", "services/service-factory.yaml"
    if "스텔라" in text or "stella" in lower:
        return "stella", "Agent", "agents.yaml"
    if "헤르메스" in text or "hermes" in lower:
        return "hermes", "Agent", "agents.yaml"
    if "우로보로스" in text or "ouroboros" in lower:
        return "ouroboros", "Agent", "agents.yaml"
    if "깃허브" in text or "github" in lower or "repo" in lower:
        return "external_repository", "Repository", ""
    return "unspecified", "Unknown", ""


def detect_route(text: str) -> dict[str, Any]:
    routing = load_yaml(ONTOLOGY / "routing.yaml")
    for route in routing.get("routes", []):
        words = route.get("match", {}).get("any", [])
        if contains_any(text, words):
            return route
    intents = load_yaml(ONTOLOGY / "intent.yaml").get("intents", {})
    return {
        "id": "ROUTE-DEFAULT-JUDGMENT",
        "intent": "product_judgment",
        "evidence_profile": "agent_routing",
        "next_actor": intents.get("product_judgment", {}).get("default_next_actor", "Stella"),
        "escalation": [],
    }


def detect_intent(text: str, fallback: str) -> tuple[str, float]:
    if fallback == "service_factory":
        return fallback, 0.9
    intents = load_yaml(ONTOLOGY / "intent.yaml").get("intents", {})
    for intent_id, data in intents.items():
        if contains_any(text, data.get("triggers", [])):
            return intent_id, 0.86
    return fallback, 0.55


def service_overlays(target: str, text: str) -> dict[str, Any]:
    if target == "kansicrich":
        svc = load_yaml(ONTOLOGY / "services" / "kansicrich.yaml")
        forbidden = ["DB 삭제", "데이터 삭제", "LIVE 전환", "실거래 주문"]
        concepts = ["TradingSystem", "OperatorDashboard"]
        first_steps: list[str] = []
        team_pattern = "Pipeline"
        if contains_any(text, ["오토리서치", "autoresearch", "전문가 엔진", "손실 복기", "전략 적용", "자동매매 엔진"]):
            concepts.append("AutoResearchDevelopmentEngine")
            first_steps = svc.get("diagnosis_layers", {}).get("autoresearch_development", {}).get("order", [])
            team_pattern = "Supervisor + Producer-Reviewer"
        elif contains_any(text, ["다운", "호스팅", "접속", "530", "1033"]):
            first_steps = svc.get("diagnosis_layers", {}).get("hosting_down", {}).get("order", [])
        elif contains_any(text, ["진입", "포지션", "신호", "수익"]):
            first_steps = svc.get("diagnosis_layers", {}).get("no_entries", {}).get("order", [])
        else:
            first_steps = ["API health", "dashboard surface", "runner state", "paper/profit readiness"]
        return {
            "concepts": concepts,
            "service_profile": "services/kansicrich.yaml",
            "service_harness": "SOT/harnesses/kansicrich/",
            "team_pattern": team_pattern,
            "forbidden": forbidden,
            "first_steps": first_steps,
            "done_when": svc.get("default_done_when", []),
        }
    if target == "atelier":
        svc = load_yaml(ONTOLOGY / "services" / "atelier.yaml")
        return {
            "concepts": ["AgentWorkspace", "TaskSession", "ProviderConnection"],
            "service_profile": "services/atelier.yaml",
            "service_harness": "SOT/harnesses/atelier/",
            "team_pattern": "Pipeline + Producer-Reviewer",
            "forbidden": ["사용자 데이터 삭제", "인증 정보 평문 저장"],
            "first_steps": ["repo surface check", "build/typecheck", "browser or installed app verification"],
            "done_when": svc.get("default_done_when", []),
        }
    if target == "bk-wiki":
        return {
            "concepts": ["OntologyCompiler", "ObsidianMirror", "Provenance"],
            "service_profile": "",
            "service_harness": "SOT/harnesses/bk-wiki/",
            "team_pattern": "Pipeline + Producer-Reviewer",
            "forbidden": ["원본 raw/session/history 삭제", "Obsidian mirror를 source input으로 재흡수"],
            "first_steps": ["identify raw/session/source inputs", "exclude mirror output", "run compiler", "run provenance check", "mirror to Obsidian"],
            "done_when": ["wiki_check 통과", "provenance_check 통과", "Obsidian mirror 확인", "pollution check 통과"],
        }
    if target == "service-factory":
        svc = load_yaml(ONTOLOGY / "services" / "service-factory.yaml")
        return {
            "concepts": [
                "StellaFactory",
                "AutonomousProductDelivery",
                "ServiceFactory",
                "AgentTopology",
                "AgentBlueprint",
                "AgentInstance",
                "StateLedger",
                "KanbanProjection",
                "DispatchCollectBridge",
                "AgentGate",
            ],
            "service_profile": "services/service-factory.yaml",
            "service_harness": "SOT/harnesses/service-factory/",
            "team_pattern": svc.get("default_team_pattern", "Hierarchical Delegation + Supervisor + Producer-Reviewer"),
            "forbidden": svc.get("forbidden", []),
            "command_owner": svc.get("control_plane", {}).get("command_owner", "Stella"),
            "state_role": "StateLedger + Release runtime adapter",
            "board_role": "KanbanProjection only",
            "agent_topology": {
                "required": True,
                "blueprints": [],
                "instances": [],
                "manifests": [],
                "creation_policy": svc.get("agent_ontology", {}).get("creation_policy", []),
            },
            "first_steps": [
                "normalize Stella target/intent/evidence",
                "derive Stella-owned AgentTopology from the goal",
                "bootstrap or load service-factory-state.json",
                "distinguish AgentBlueprint, AgentInstance, AgentManifest, and agent_request",
                "map available specialist agents to required roles",
                "plan roles and agent_requests",
                "dispatch worker/reviewer requests",
                "collect result.json artifacts",
                "assess readiness",
                "if not complete in this turn, create or update heartbeat/recurring automation",
            ],
            "done_when": svc.get("default_done_when", []),
            "automation_policy": svc.get("autonomous_run_policy", {}),
        }
    return {"concepts": [], "service_profile": "", "service_harness": "", "team_pattern": "", "forbidden": [], "first_steps": [], "done_when": []}


def merge_factory_overlay(target_overlay: dict[str, Any], factory_overlay: dict[str, Any]) -> dict[str, Any]:
    combined = dict(factory_overlay)
    combined["concepts"] = list(
        dict.fromkeys(factory_overlay.get("concepts", []) + target_overlay.get("concepts", []))
    )
    combined["service_profile"] = target_overlay.get("service_profile") or factory_overlay.get("service_profile", "")
    combined["factory_profile"] = factory_overlay.get("service_profile", "")
    target_harness = target_overlay.get("service_harness", "")
    factory_harness = factory_overlay.get("service_harness", "")
    combined["service_harness"] = " + ".join([item for item in [target_harness, factory_harness] if item])
    combined["target_team_pattern"] = target_overlay.get("team_pattern", "")
    combined["team_pattern"] = factory_overlay.get("team_pattern", "")
    combined["forbidden"] = list(
        dict.fromkeys(factory_overlay.get("forbidden", []) + target_overlay.get("forbidden", []))
    )
    combined["first_steps"] = list(
        dict.fromkeys(
            factory_overlay.get("first_steps", [])
            + [f"apply target service profile: {target_overlay.get('service_profile', 'unspecified')}"]
            + target_overlay.get("first_steps", [])
        )
    )
    combined["done_when"] = list(
        dict.fromkeys(factory_overlay.get("done_when", []) + target_overlay.get("done_when", []))
    )
    return combined


def supporting_actors(text: str, primary: str) -> list[str]:
    found: list[str] = []
    actor_aliases = {
        "Stella": ["스텔라", "stella"],
        "Hermes": ["헤르메스", "hermes"],
        "Codex": ["코덱스", "codex"],
        "Claude": ["클로드", "claude"],
        "Ouroboros": ["우로보로스", "ouroboros"],
        "Release": ["릴리스", "release"],
    }
    lower = text.lower()
    for actor, aliases in actor_aliases.items():
        if actor == primary:
            continue
        if any(alias.lower() in lower for alias in aliases):
            found.append(actor)
    return found


def normalize(text: str) -> int:
    target_name, target_type, profile = detect_target(text)
    route = detect_route(text)
    intent_id, confidence = detect_intent(text, route.get("intent", "product_judgment"))
    intent_data = load_yaml(ONTOLOGY / "intent.yaml")
    evidence_data = load_yaml(ONTOLOGY / "evidence.yaml")
    overlay = service_overlays(target_name, text)
    if intent_id == "service_factory" and target_name != "service-factory":
        overlay = merge_factory_overlay(overlay, service_overlays("service-factory", text))

    profile_id = route.get("evidence_profile", "")
    evidence_profile = evidence_data.get("evidence_profiles", {}).get(profile_id, {})
    forbidden = []
    forbidden.extend(intent_data.get("constraints", {}).get("forbidden_without_explicit_request", []))
    forbidden.extend(overlay.get("forbidden", []))
    forbidden = list(dict.fromkeys(forbidden))

    intent_record = intent_data.get("intents", {}).get(intent_id, {})
    primary_actor = route.get("next_actor", intent_record.get("default_next_actor", "Stella"))
    command_owner = route.get("command_owner", intent_record.get("command_owner", overlay.get("command_owner", "Stella")))
    delegated_to = route.get("delegated_to", intent_record.get("delegated_to", ""))
    executor = route.get("executor", intent_record.get("executor_hint", ""))
    verification = route.get("verification", "")
    agent_route = intent_id == "agent_routing"
    first_steps = overlay.get("first_steps", [])
    done_when = overlay.get("done_when", [])
    concepts = overlay.get("concepts", [])
    if agent_route:
        concepts = concepts or ["Agent", "Capability", "Workflow", "DecisionBoundary"]
        first_steps = first_steps or ["역할별 owns/does_not_own 확인", "next_actor와 supporting actor 분리", "완료 보고 기준 지정"]
        done_when = done_when or ["Stella/Hermes/Codex/Claude/Ouroboros 역할이 혼합되지 않음", "실행 주체와 검증 주체가 분리됨"]
    if not first_steps and profile_id:
        first_steps = evidence_profile.get("required", [])
    if not done_when:
        done_when = intent_record.get("required_outputs", [])

    result = {
        "schema_version": "3.0",
        "target": {
            "name": target_name,
            "type": target_type,
            "profile": profile or overlay.get("service_profile", ""),
        },
        "intent": {
            "id": intent_id,
            "ko": intent_record.get("ko", ""),
            "confidence": confidence,
        },
        "domain": {
            "concepts": concepts,
            "service_profile": overlay.get("service_profile", profile),
            "service_harness": overlay.get("service_harness", ""),
            "team_pattern": overlay.get("team_pattern", ""),
        },
        "constraints": {
            "always": intent_data.get("constraints", {}).get("always", []),
            "task_specific": [],
        },
        "forbidden": forbidden,
        "risks": {
            "critical": [item for item in forbidden if "삭제" in item or "LIVE" in item or "주문" in item],
            "high": route.get("escalation", []),
        },
        "evidence": {
            "profile": profile_id,
            "required": evidence_profile.get("required", []),
            "recommended": evidence_profile.get("recommended", []),
            "not_enough": evidence_profile.get("not_enough", []),
        },
        "next_actor": primary_actor,
        "command_owner": command_owner,
        "delegated_to": delegated_to,
        "executor": executor,
        "verification": verification,
        "state_role": route.get("state_role", overlay.get("state_role", "")),
        "board_role": route.get("board_role", overlay.get("board_role", "")),
        "agent_topology": overlay.get("agent_topology", {"required": False, "blueprints": [], "instances": [], "manifests": []}),
        "supporting_actors": supporting_actors(text, primary_actor),
        "workflow": {
            "first_steps": first_steps,
            "done_when": done_when,
            "automation_policy": overlay.get("automation_policy", {}),
        },
        "escalation": {
            "ask_representative_only_if": route.get("escalation", []),
        },
        "notes": "자동 정규화 초안. 실행 전 실제 SOT/프로젝트/런타임 증거로 보강한다.",
    }
    print(yaml.dump(result, Dumper=NoAliasDumper, allow_unicode=True, sort_keys=False))
    return 0


def explain(name: str) -> int:
    key = name.lower()
    if key in {"kansicrich", "칸식리치"}:
        data = load_yaml(ONTOLOGY / "services" / "kansicrich.yaml")
    elif key in {"atelier", "아틀리에"}:
        data = load_yaml(ONTOLOGY / "services" / "atelier.yaml")
    elif key in {"service-factory", "service_factory", "antigravity", "안티그래비티"}:
        data = load_yaml(ONTOLOGY / "services" / "service-factory.yaml")
    elif key in {"agents", "agent", "에이전트"}:
        data = load_yaml(ONTOLOGY / "agents.yaml")
    else:
        data = load_yaml(ONTOLOGY / "concepts.yaml")
    print(yaml.dump(data, Dumper=NoAliasDumper, allow_unicode=True, sort_keys=False))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    cmd = argv[1]
    if cmd == "validate":
        return validate()
    if cmd == "normalize":
        if len(argv) < 3:
            print("normalize requires text")
            return 2
        return normalize(" ".join(argv[2:]))
    if cmd == "explain":
        if len(argv) < 3:
            print("explain requires name")
            return 2
        return explain(argv[2])
    print(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
