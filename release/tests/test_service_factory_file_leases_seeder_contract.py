"""Focused contract test — Service Factory `file_leases` seeder.

service-factory.md 의 "Release 는 stage 시작 전에 file_leases 를 상태 파일에 남긴다"
약속이 v0.2 에서 미구현이었음 — agent_request 의 owned_paths 는 build_agent_requests
가 박지만 state["file_leases"] ledger 로 흡수하는 단계 누락. 본 모듈이 그 빈 자리를
한 줄로 채운다.

검증 축:
1. 모듈 표면 — KIND_TO_LEASE_MODE / DEFAULT_LEASE_MODE / LEASE_LEDGER_VERSION 노출
2. lease_mode_for_request_kind — explorer/planner/builder/integrator/reviewer/critic/
   auditor 등 핵심 kind 가 정확히 LEASE_MODES (read/write/review/integrate) 로 매핑
3. seed_file_leases_from_requests — agent_requests 의 owned_paths → file_leases ledger
   직렬화 무결성, owned_paths 빈 리스트 skip
4. seed_file_leases_from_requests overwrite=False (기본) — 기존 leases 와 merge
5. seed_file_leases_from_requests overwrite=True — 전체 교체
6. detect_write_conflicts — 같은 path 에 다중 write owner 검출
7. file_leases_blockers — parallel_implementation/integration 진행 중인데 ledger 비어 있으면
   blocker; write_conflict 있으면 blocker
8. service_factory.py facade — _fl_* alias 노출 + command_plan smoke 에서 12 lease 자동 생성
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path("~/.claude/skills/release/scripts").expanduser()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from service_factory_file_leases_seeder import (  # noqa: E402
    DEFAULT_LEASE_MODE,
    KIND_TO_LEASE_MODE,
    LEASE_LEDGER_VERSION,
    detect_write_conflicts,
    file_leases_blockers,
    lease_mode_for_request_kind,
    seed_file_leases_from_requests,
)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
def _req(rid, stage, kind, owned, agent_type="agent", status="queued"):
    return {
        "id": rid,
        "stage": stage,
        "kind": kind,
        "agent_type": agent_type,
        "owned_paths": owned,
        "status": status,
    }


# ---------------------------------------------------------------------------
# 1. 모듈 표면
# ---------------------------------------------------------------------------
def test_module_exposes_required_symbols():
    assert isinstance(KIND_TO_LEASE_MODE, dict) and len(KIND_TO_LEASE_MODE) >= 10
    assert DEFAULT_LEASE_MODE in {"read", "write", "review", "integrate"}
    assert isinstance(LEASE_LEDGER_VERSION, str) and LEASE_LEDGER_VERSION


def test_kind_to_lease_mode_uses_canonical_lease_modes_only():
    """service-factory.md LEASE_MODES = {read/write/review/integrate} 와 정합."""
    canonical = {"read", "write", "review", "integrate"}
    for kind, mode in KIND_TO_LEASE_MODE.items():
        assert mode in canonical, f"{kind}: non-canonical mode {mode!r}"


# ---------------------------------------------------------------------------
# 2. lease_mode_for_request_kind — 핵심 kind 매핑
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "kind,expected",
    [
        ("worker", "write"),
        ("builder", "write"),
        ("explorer", "write"),
        ("planner", "write"),
        ("integrator", "integrate"),
        ("reviewer", "review"),
        ("critic", "review"),
        ("auditor", "review"),
        ("security_auditor", "review"),
        ("runtime_auditor", "review"),
        ("runtime_probe", "review"),
        ("sentinel", "read"),
    ],
)
def test_lease_mode_for_known_kinds(kind, expected):
    assert lease_mode_for_request_kind(kind) == expected


def test_lease_mode_for_unknown_kind_falls_back_to_default():
    assert lease_mode_for_request_kind("nonexistent-kind") == DEFAULT_LEASE_MODE
    assert lease_mode_for_request_kind(None) == DEFAULT_LEASE_MODE
    assert lease_mode_for_request_kind("") == DEFAULT_LEASE_MODE


def test_lease_mode_is_case_insensitive():
    assert lease_mode_for_request_kind("WORKER") == "write"
    assert lease_mode_for_request_kind("Reviewer") == "review"


# ---------------------------------------------------------------------------
# 3. seed_file_leases_from_requests — owned_paths 흡수
# ---------------------------------------------------------------------------
def test_seed_skips_requests_with_empty_owned_paths():
    state = {
        "agent_requests": [
            _req("a", "parallel_implementation", "builder", []),  # skip
            _req("b", "architecture", "planner", ["arch.md"]),
        ]
    }
    leases = seed_file_leases_from_requests(state)
    assert [l["path"] for l in leases] == ["arch.md"]


def test_seed_inlines_required_fields_per_lease():
    state = {
        "agent_requests": [
            _req("p1", "architecture", "planner", ["arch.md"], agent_type="architect-reviewer"),
        ]
    }
    leases = seed_file_leases_from_requests(state)
    assert len(leases) == 1
    l = leases[0]
    for k in ("path", "mode", "owner", "owner_request_id", "owner_agent_type", "stage", "kind"):
        assert k in l, f"lease missing field: {k}"
    assert l["mode"] == "write"
    assert l["owner"] == "p1"
    assert l["owner_request_id"] == "p1"
    assert l["stage"] == "architecture"


def test_seed_multiple_paths_per_request():
    state = {
        "agent_requests": [
            _req("p1", "architecture", "planner", ["a.md", "b.md", "c.md"]),
        ]
    }
    leases = seed_file_leases_from_requests(state)
    assert {l["path"] for l in leases} == {"a.md", "b.md", "c.md"}
    assert all(l["mode"] == "write" for l in leases)


def test_seed_handles_non_dict_requests():
    state = {"agent_requests": [None, "string", _req("ok", "architecture", "planner", ["a.md"])]}
    leases = seed_file_leases_from_requests(state)
    assert len(leases) == 1


# ---------------------------------------------------------------------------
# 4. overwrite=False — merge 동작
# ---------------------------------------------------------------------------
def test_merge_preserves_existing_unique_leases():
    state = {
        "agent_requests": [_req("p1", "architecture", "planner", ["arch.md"])],
        "file_leases": [
            {"path": "legacy.md", "mode": "read", "owner_request_id": "legacy-req"},
        ],
    }
    leases = seed_file_leases_from_requests(state, overwrite=False)
    paths = {l["path"] for l in leases}
    assert "legacy.md" in paths
    assert "arch.md" in paths


def test_merge_dedupes_same_path_same_owner():
    """이미 같은 (path, owner) 가 있으면 중복 추가 안 함."""
    state = {
        "agent_requests": [_req("p1", "architecture", "planner", ["arch.md"])],
        "file_leases": [
            {"path": "arch.md", "mode": "write", "owner_request_id": "p1"},
        ],
    }
    leases = seed_file_leases_from_requests(state, overwrite=False)
    matching = [l for l in leases if l["path"] == "arch.md" and l["owner_request_id"] == "p1"]
    assert len(matching) == 1


def test_overwrite_replaces_existing_leases():
    state = {
        "agent_requests": [_req("p1", "architecture", "planner", ["arch.md"])],
        "file_leases": [
            {"path": "legacy.md", "mode": "read", "owner_request_id": "legacy-req"},
        ],
    }
    leases = seed_file_leases_from_requests(state, overwrite=True)
    paths = {l["path"] for l in leases}
    assert paths == {"arch.md"}


# ---------------------------------------------------------------------------
# 5. detect_write_conflicts
# ---------------------------------------------------------------------------
def test_no_conflict_when_each_write_path_has_single_owner():
    leases = [
        {"path": "a.md", "mode": "write", "owner_request_id": "p1"},
        {"path": "b.md", "mode": "write", "owner_request_id": "p2"},
    ]
    assert detect_write_conflicts(leases) == []


def test_seed_marks_conflict_when_two_writers_for_same_path():
    state = {
        "agent_requests": [
            _req("p1", "architecture", "planner", ["arch.md"]),
            _req("p2", "decomposition", "planner", ["arch.md"]),  # 충돌
        ]
    }
    leases = seed_file_leases_from_requests(state)
    conflicts = detect_write_conflicts(leases)
    assert len(conflicts) == 1
    assert conflicts[0]["path"] == "arch.md"
    assert "conflict_with" in conflicts[0]


def test_seed_allows_write_and_review_on_same_path():
    """write 와 review 가 같은 path 에 동시 존재해도 충돌 아님 — review 는 수정 안 함."""
    state = {
        "agent_requests": [
            _req("p1", "architecture", "planner", ["arch.md"]),
            _req("r1", "verification", "reviewer", ["arch.md"]),
        ]
    }
    leases = seed_file_leases_from_requests(state)
    assert detect_write_conflicts(leases) == []


# ---------------------------------------------------------------------------
# 6. file_leases_blockers — anti false-green
# ---------------------------------------------------------------------------
def test_blocker_when_parallel_implementation_running_with_empty_leases():
    state = {
        "agent_requests": [
            _req("b1", "parallel_implementation", "builder", [], status="running"),
        ],
        "file_leases": [],
    }
    assert "file_leases_empty_during_write_stage" in file_leases_blockers(state)


def test_blocker_when_integration_in_progress_with_empty_leases():
    state = {
        "agent_requests": [
            _req("i1", "integration", "integrator", [], status="in_progress"),
        ],
        "file_leases": [],
    }
    assert "file_leases_empty_during_write_stage" in file_leases_blockers(state)


def test_no_blocker_when_implementation_stage_idle_with_empty_leases():
    state = {
        "agent_requests": [
            _req("b1", "parallel_implementation", "builder", [], status="queued"),
        ],
        "file_leases": [],
    }
    assert file_leases_blockers(state) == []


def test_blocker_when_write_conflict_present():
    state = {
        "agent_requests": [],
        "file_leases": [
            {"path": "a.md", "mode": "write_conflict", "owner_request_id": "p2"},
        ],
    }
    assert "file_leases_write_conflict" in file_leases_blockers(state)


# ---------------------------------------------------------------------------
# 7. facade — service_factory.py 가 본 모듈을 thin facade 로 import
# ---------------------------------------------------------------------------
def test_service_factory_facade_exposes_seeder_symbols():
    import service_factory  # noqa: F401

    assert hasattr(service_factory, "_fl_seed_file_leases_from_requests")
    assert hasattr(service_factory, "_fl_file_leases_blockers")
    assert hasattr(service_factory, "_fl_detect_write_conflicts")


def test_completion_claim_guard_includes_file_lease_blocker():
    """parallel_implementation 진행 중 + ledger 비어 있을 때 guard 가 잡는지."""
    import service_factory as sf

    state = {
        "agent_requests": [
            _req("b1", "parallel_implementation", "builder", [], status="running"),
        ],
        "file_leases": [],
        "status": "running",
    }
    guard = sf.completion_claim_guard(state)
    assert "file_leases_empty_during_write_stage" in guard["blockers"]
    assert guard["completion_claim_allowed"] is False
