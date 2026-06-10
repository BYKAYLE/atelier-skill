"""Service Factory — file_leases seeder.

왜 이 모듈이 필요한가
---------------------
service-factory.md 명시(파일 Lease 규칙 절):

    Release는 stage 시작 전에 `file_leases`를 상태 파일에 남긴다.
    같은 파일 또는 디렉터리에는 동시에 `write` owner가 1명만 있어야 한다.
    최종 병합은 단일 Integrator만 수행한다.

그러나 v0.2 의 `command_plan` 은 agent_request 안에 `owned_paths` 를 박지만
이를 state["file_leases"] ledger 로 흡수하지 않는다 — 즉 데이터는 있는데
ledger 가 비어 있어 누가 어느 path 의 write owner 인지 명시 추적이 안 된다.

이 모듈은 그 빈 자리를 채운다.

설계
----
- domain: lease_mode_for_request_kind() — request.kind → LEASE_MODES 매핑 SoT
- application: seed_file_leases_from_requests() — agent_requests 의 owned_paths 를
  읽어 state["file_leases"] 로 직렬화. 같은 path 에 다중 write owner 면 conflict.
- validate: detect_write_conflicts() — 같은 (path, mode=write) 쌍을 두 owner 가 잡으면
  conflict 리스트 반환. service-factory.md 의 "충돌이 감지되면 덮어쓰기 대신 해당
  stage 를 validation_required 로 둔다" 규칙 정합.

핵심 원칙:
- LLM 0 호출 (조합 + dict 변환만)
- 빈 owned_paths 는 skip — decomposer 가 채울 자리에 placeholder 만들지 않음
- backward-compatible: 이미 state["file_leases"] 에 항목 있으면 덮어쓰지 않고 merge
- Architecture-First Modular: 신규 파일, service_factory.py 는 thin wiring 만
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Domain — request.kind → lease_mode SoT
# service-factory.md 의 LEASE_MODES = {read/write/review/integrate} 와 1:1.
# ---------------------------------------------------------------------------
KIND_TO_LEASE_MODE: dict[str, str] = {
    # write — 산출물 직접 작성 (SoT 문서 또는 코드)
    "worker": "write",
    "builder": "write",
    "explorer": "write",  # current_state / repo_map 등 SoT 문서 owner
    "planner": "write",  # development_plan / product_brief / architecture / decomposition owner
    "orchestrator": "write",
    "architect": "write",
    "product_manager": "write",
    "state_mapper": "write",
    "strategy_planner": "write",
    "repo_mapper": "write",
    "decomposer": "write",
    "deployment_readiness": "write",
    "final_audit": "write",
    # integrate — 다중 Worker 산출물 병합 단일 owner
    "integrator": "integrate",
    # review — 수정하지 않고 findings 만 작성
    "reviewer": "review",
    "critic": "review",
    "auditor": "review",
    "security_auditor": "review",
    "runtime_auditor": "review",
    "runtime_probe": "review",
    "orchestration_reviewer": "review",
    # read — 읽기만 (sentinel 등)
    "sentinel": "read",
}

DEFAULT_LEASE_MODE = "read"
LEASE_LEDGER_VERSION = "stella-factory-file-leases-v1"


def lease_mode_for_request_kind(kind: str | None) -> str:
    """request.kind (또는 agent_type 의 lowercased fallback) → LEASE_MODES."""
    if not kind:
        return DEFAULT_LEASE_MODE
    return KIND_TO_LEASE_MODE.get(str(kind).lower(), DEFAULT_LEASE_MODE)


# ---------------------------------------------------------------------------
# Application — seeder
# ---------------------------------------------------------------------------
def seed_file_leases_from_requests(
    state: dict[str, Any],
    *,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    """state["agent_requests"] 의 owned_paths 를 state["file_leases"] 로 흡수.

    각 path 마다 lease 1건 생성:
        { "path", "mode", "owner", "owner_request_id", "owner_agent_type", "stage", "kind" }

    빈 owned_paths 는 skip (decomposer 가 채울 자리). 같은 path 에 다중 write owner
    감지 시 conflict 항목으로 표시(`mode=write_conflict`) — 실행은 plan 이 멈추지
    않지만 detect_write_conflicts() 로 후행 게이트가 잡는다.

    overwrite=False (기본): 기존 state["file_leases"] 항목과 merge (path 기준 dedupe).
    overwrite=True: 기존을 전부 덮어쓴다.
    """
    requests = state.get("agent_requests") or []
    seeded: list[dict[str, Any]] = []
    by_path: dict[str, list[dict[str, Any]]] = {}

    for r in requests:
        if not isinstance(r, dict):
            continue
        paths = r.get("owned_paths") or []
        if not paths:
            continue
        kind = r.get("kind") or r.get("agent_type")
        mode = lease_mode_for_request_kind(kind)
        for p in paths:
            if not isinstance(p, str) or not p:
                continue
            lease = {
                "path": p,
                "mode": mode,
                "owner": r.get("id"),
                "owner_request_id": r.get("id"),
                "owner_agent_type": r.get("agent_type"),
                "stage": r.get("stage"),
                "kind": kind,
            }
            by_path.setdefault(p, []).append(lease)

    # write 충돌 감지 — 같은 path 에 write owner 2명 이상
    for p, leases in by_path.items():
        write_owners = [l for l in leases if l["mode"] == "write"]
        if len(write_owners) >= 2:
            # 첫 owner 유지, 나머지는 write_conflict 표지 (Release 가 후처리)
            for l in write_owners[1:]:
                l["mode"] = "write_conflict"
                l["conflict_with"] = write_owners[0].get("owner_request_id")

    for p, leases in by_path.items():
        seeded.extend(leases)

    if overwrite:
        merged = seeded
    else:
        existing = state.get("file_leases") or []
        for l in existing:
            if isinstance(l, dict) and not l.get("owner") and l.get("owner_request_id"):
                l["owner"] = l.get("owner_request_id")
        existing_keys = {(l.get("path"), l.get("owner_request_id")) for l in existing if isinstance(l, dict)}
        merged = list(existing)
        for l in seeded:
            key = (l.get("path"), l.get("owner_request_id"))
            if key not in existing_keys:
                merged.append(l)
                existing_keys.add(key)

    return merged


def detect_write_conflicts(file_leases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """write_conflict 표지된 lease 항목 반환. 빈 리스트면 충돌 없음."""
    return [l for l in (file_leases or []) if isinstance(l, dict) and l.get("mode") == "write_conflict"]


# ---------------------------------------------------------------------------
# completion_claim_guard 보강용 — false-green 방지
# ---------------------------------------------------------------------------
def file_leases_blockers(state: dict[str, Any]) -> list[str]:
    """parallel_implementation/integration in_progress 인데 file_leases 가 비어 있거나
    write_conflict 가 있으면 blocker 반환.

    service-factory.md 의 Anti False-Green 규칙 + 파일 Lease 규칙 정합.
    """
    leases = state.get("file_leases") or []
    blockers: list[str] = []
    in_progress_stages = {
        str(r.get("stage"))
        for r in (state.get("agent_requests") or [])
        if isinstance(r, dict) and r.get("status") in ("running", "in_progress")
    }
    risky_stages = {"parallel_implementation", "integration"}
    if (in_progress_stages & risky_stages) and not leases:
        blockers.append("file_leases_empty_during_write_stage")
    if detect_write_conflicts(leases):
        blockers.append("file_leases_write_conflict")
    return blockers
