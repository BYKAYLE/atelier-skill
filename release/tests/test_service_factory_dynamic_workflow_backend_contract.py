"""Focused contract test — Service Factory `dynamic_workflow` spawn_runtime backend.

이 테스트는 release/scripts/service_factory_dynamic_workflow_backend.py 의 계약을
1:1 로 검증한다. 큰 통합 테스트에 덧붙이지 않고 신규 파일 — Architecture-First Modular
원칙 + service-factory.md 의 Anti False-Green 규칙(자기검토만으로 done 금지) 정합.

검증 축:
1. 모듈 표면 — 공개 심볼/상수/함수가 존재하고 service_factory.py 의 result.json 계약과 정합
2. render_workflow_script — 빈 입력 거부, JS 산출에 SoT 토큰(meta/RESULT_SCHEMA/ITEMS/MAX_PARALLEL) 모두 포함, schema 가 WORKFLOW_RESULT_SCHEMA 와 byte-equivalent
3. max_parallel 해석 — state.limits.max_parallel_agents > override > DEFAULT, ABSOLUTE cap (16) 강제
4. agent_type 해석 — 알려진 type 만 통과, 그 외 DEFAULT_AGENT_TYPE
5. gate guard — paper-unsafe 키워드(GATE_BLOCK_KEYWORDS) 가 prompt 안에 있으면 violations 반환
6. collect_dispatch_requests — status filter, prompt_path 필수, stage 필터, 형식 견고
7. render_workflow_instructions — Workflow 도구 호출 + result.json 직렬화 + collect 명령 단계가 모두 포함
8. write_dispatch — tmpdir 에 3 산출물(workflow.js / instructions.md / dispatch.json) 생성, summary 무결성
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path("~/.claude/skills/release/scripts").expanduser()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from service_factory_dynamic_workflow_backend import (  # noqa: E402
    ABSOLUTE_MAX_PARALLEL,
    DEFAULT_AGENT_TYPE,
    DEFAULT_MAX_PARALLEL,
    GATE_BLOCK_KEYWORDS,
    WORKFLOW_RESULT_SCHEMA,
    _resolve_agent_type,
    _resolve_max_parallel,
    acceptance_command_is_paper_safe,
    collect_dispatch_requests,
    render_workflow_instructions,
    render_workflow_script,
    write_dispatch,
)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
def _state(limits=None):
    return {
        "factory_id": "fac_test",
        "project": {"path": "/tmp/svc"},
        "limits": limits or {},
        "agent_requests": [],
    }


def _request(rid="req-1", stage="parallel_implementation", agent_type="frontend-developer", prompt_path="SOT/service-factory/agent-prompts/req-1.md", artifact_dir="/tmp/art/req-1", status="queued"):
    return {
        "id": rid,
        "stage": stage,
        "agent_type": agent_type,
        "prompt_path": prompt_path,
        "artifact_dir": artifact_dir,
        "status": status,
    }


# ---------------------------------------------------------------------------
# 1. 모듈 표면
# ---------------------------------------------------------------------------
def test_module_exposes_required_symbols():
    assert isinstance(DEFAULT_MAX_PARALLEL, int) and DEFAULT_MAX_PARALLEL >= 1
    assert isinstance(ABSOLUTE_MAX_PARALLEL, int) and ABSOLUTE_MAX_PARALLEL >= DEFAULT_MAX_PARALLEL
    assert ABSOLUTE_MAX_PARALLEL <= 16  # Workflow 도구 자체 cap 과 정합
    assert isinstance(DEFAULT_AGENT_TYPE, str) and DEFAULT_AGENT_TYPE
    assert isinstance(WORKFLOW_RESULT_SCHEMA, dict)


def test_workflow_result_schema_matches_factory_result_contract():
    """Factory load_child_result() 가 읽는 필드와 1:1."""
    props = WORKFLOW_RESULT_SCHEMA["properties"]
    for key in ("status", "summary", "modified_files", "commands_run", "findings_or_risks", "next_step"):
        assert key in props, f"missing required field {key}"
    enum = props["status"]["enum"]
    for st in ("completed", "validation_required", "blocked", "failed"):
        assert st in enum, f"status enum missing {st}"


# ---------------------------------------------------------------------------
# 2. render_workflow_script
# ---------------------------------------------------------------------------
def test_render_workflow_script_rejects_empty_requests():
    with pytest.raises(ValueError):
        render_workflow_script(_state(), [], "run_x")


def test_render_workflow_script_contains_required_tokens():
    s = render_workflow_script(_state(), [_request()], "run_x")
    required = [
        "export const meta",
        "const RESULT_SCHEMA",
        "const ITEMS",
        "const MAX_PARALLEL",
        "parallel(",
        "agent(",
        "schema: RESULT_SCHEMA",
        "agentType:",
        "phase('Fan-out')",
    ]
    for token in required:
        assert token in s, f"script missing token: {token}"


def test_render_workflow_script_embeds_schema_sot_byte_equivalent():
    s = render_workflow_script(_state(), [_request()], "run_x")
    # WORKFLOW_RESULT_SCHEMA 가 RESULT_SCHEMA = ... 본문에 그대로 들어가는지
    expected = json.dumps(WORKFLOW_RESULT_SCHEMA, ensure_ascii=False, indent=2)
    assert expected in s, "RESULT_SCHEMA inline 이 SoT 와 byte-equivalent 가 아님"


def test_render_workflow_script_respects_state_limits_max_parallel():
    s = render_workflow_script(_state(limits={"max_parallel_agents": 5}), [_request()], "run_x")
    assert "const MAX_PARALLEL = 5;" in s


def test_render_workflow_script_caps_at_absolute_max():
    s = render_workflow_script(_state(limits={"max_parallel_agents": 999}), [_request()], "run_x")
    assert f"const MAX_PARALLEL = {ABSOLUTE_MAX_PARALLEL};" in s


def test_render_workflow_script_inlines_all_requests_as_items():
    reqs = [_request(rid=f"req-{i}") for i in range(3)]
    s = render_workflow_script(_state(), reqs, "run_x")
    for r in reqs:
        assert f'"id": "{r["id"]}"' in s, f"item missing id {r['id']}"


# ---------------------------------------------------------------------------
# 3. max_parallel 해석
# ---------------------------------------------------------------------------
def test_resolve_max_parallel_uses_state_limit():
    assert _resolve_max_parallel(_state(limits={"max_parallel_agents": 7}), None) == 7


def test_resolve_max_parallel_override_wins():
    assert _resolve_max_parallel(_state(limits={"max_parallel_agents": 7}), 2) == 2


def test_resolve_max_parallel_falls_back_to_default_when_invalid():
    assert _resolve_max_parallel(_state(limits={"max_parallel_agents": 0}), None) == DEFAULT_MAX_PARALLEL
    assert _resolve_max_parallel(_state(limits={"max_parallel_agents": "bad"}), None) == DEFAULT_MAX_PARALLEL


def test_resolve_max_parallel_caps_at_absolute():
    assert _resolve_max_parallel(_state(limits={"max_parallel_agents": 100}), None) == ABSOLUTE_MAX_PARALLEL


def test_resolve_max_parallel_rejects_invalid_override():
    with pytest.raises(ValueError):
        _resolve_max_parallel(_state(), 0)
    with pytest.raises(ValueError):
        _resolve_max_parallel(_state(), -1)


# ---------------------------------------------------------------------------
# 4. agent_type 해석
# ---------------------------------------------------------------------------
def test_resolve_agent_type_known_passes_through():
    for known in ("general-purpose", "Explore", "Plan", "code-reviewer"):
        assert _resolve_agent_type({"agent_type": known}) == known


def test_resolve_agent_type_unknown_falls_back():
    assert _resolve_agent_type({"agent_type": "frontend-developer"}) == DEFAULT_AGENT_TYPE
    assert _resolve_agent_type({"agent_type": ""}) == DEFAULT_AGENT_TYPE
    assert _resolve_agent_type({}) == DEFAULT_AGENT_TYPE


# ---------------------------------------------------------------------------
# 5. gate guard
# ---------------------------------------------------------------------------
def test_acceptance_command_is_paper_safe_pass():
    ok, v = acceptance_command_is_paper_safe("read SOT files and produce a report")
    assert ok is True
    assert v == []


def test_acceptance_command_is_paper_safe_detects_gate_keywords():
    for gate, kw in GATE_BLOCK_KEYWORDS:
        text = f"step 1: {kw} something"
        ok, violations = acceptance_command_is_paper_safe(text)
        assert ok is False, f"{kw} should trigger {gate}"
        assert any(gate in v for v in violations)


# ---------------------------------------------------------------------------
# 6. collect_dispatch_requests
# ---------------------------------------------------------------------------
def test_collect_dispatch_requires_prompt_path():
    state = _state()
    state["agent_requests"] = [
        _request(rid="a", prompt_path=""),  # no prompt → excluded
        _request(rid="b"),  # OK
    ]
    out = collect_dispatch_requests(state)
    assert [r["id"] for r in out] == ["b"]


def test_collect_dispatch_filters_by_status():
    state = _state()
    state["agent_requests"] = [
        _request(rid="a", status="queued"),
        _request(rid="b", status="in_progress"),
        _request(rid="c", status="completed"),
        _request(rid="d", status="blocked"),
    ]
    out = collect_dispatch_requests(state)
    assert {r["id"] for r in out} == {"a", "b"}


def test_collect_dispatch_stage_filter():
    state = _state()
    state["agent_requests"] = [
        _request(rid="a", stage="parallel_implementation"),
        _request(rid="b", stage="verification"),
    ]
    out = collect_dispatch_requests(state, stage="verification")
    assert [r["id"] for r in out] == ["b"]


def test_collect_dispatch_handles_non_dict_entries():
    state = _state()
    state["agent_requests"] = [None, "not-a-dict", _request(rid="ok")]
    out = collect_dispatch_requests(state)
    assert [r["id"] for r in out] == ["ok"]


# ---------------------------------------------------------------------------
# 7. render_workflow_instructions
# ---------------------------------------------------------------------------
def test_render_workflow_instructions_contains_required_steps(tmp_path):
    script_path = tmp_path / "dispatch.workflow.js"
    state_path = tmp_path / "state.json"
    md = render_workflow_instructions(_state(), [_request()], "run_x", script_path, state_path=state_path)
    # 필수 단계 (parent agent 가 따라야 할 절차)
    assert "Workflow 도구" in md or "Workflow tool" in md
    assert "result.json" in md
    assert "service_factory.py collect" in md
    assert str(script_path) in md
    assert str(state_path) in md
    # 절대 경계 명시
    assert "LIVE" in md and "DB" in md


# ---------------------------------------------------------------------------
# 8. write_dispatch — 통합
# ---------------------------------------------------------------------------
def test_write_dispatch_produces_three_artifacts(tmp_path):
    state = _state(limits={"max_parallel_agents": 4})
    requests = [_request(rid=f"req-{i}") for i in range(3)]
    state_path = tmp_path / "state.json"
    bridge = tmp_path / "bridge"
    summary = write_dispatch(
        state=state,
        state_path=state_path,
        bridge_dir=bridge,
        run_id="run_xyz",
        requests=requests,
        max_parallel=None,
    )
    out_dir = bridge / "run_xyz" / "dynamic_workflow"
    assert (out_dir / "dispatch.workflow.js").exists()
    assert (out_dir / "dispatch.instructions.md").exists()
    assert (out_dir / "dispatch.json").exists()
    # summary 무결성
    assert summary["backend"] == "dynamic_workflow"
    assert summary["request_count"] == 3
    assert summary["max_parallel"] == 4
    assert summary["request_ids"] == ["req-0", "req-1", "req-2"]
    # dispatch.json 가 disk 와 일치
    saved = json.loads((out_dir / "dispatch.json").read_text())
    assert saved["run_id"] == "run_xyz"
    assert saved["backend"] == "dynamic_workflow"


def test_write_dispatch_rejects_empty_requests(tmp_path):
    with pytest.raises(ValueError):
        write_dispatch(
            state=_state(),
            state_path=tmp_path / "state.json",
            bridge_dir=tmp_path / "bridge",
            run_id="run_x",
            requests=[],
        )


# ---------------------------------------------------------------------------
# 9. service_factory.py facade — import 만 확인 (회귀 방지)
# ---------------------------------------------------------------------------
def test_service_factory_facade_imports_backend_symbols():
    """service_factory.py 가 본 모듈을 thin facade 로 import 하고 노출하는지.

    Architecture-First: service_factory.py 는 dispatch case 추가만 하고 실제 조립은
    본 모듈로 위임한다 — drift 시 즉시 검출.
    """
    import service_factory  # noqa: F401

    # alias 로 노출됐는지
    assert hasattr(service_factory, "_dw_collect_dispatch_requests")
    assert hasattr(service_factory, "_dw_write_dispatch")
    assert hasattr(service_factory, "_DW_DEFAULT_MAX_PARALLEL")
    # 새 sub-command 핸들러
    assert hasattr(service_factory, "command_dispatch_workflow")
    assert callable(service_factory.command_dispatch_workflow)
