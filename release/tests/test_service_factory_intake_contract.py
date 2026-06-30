"""Focused contract test — Service Factory intake-contract 4항목 게이트.

사용자 지시(260603): "사용자가 스텔라팩토리를 자연어로 작성했을 때 4항목
(목표/금지선/완료기준/승인위임범위) 중 빠지거나 부족하면 추가로 물어보고 채워서 진행."

검증 축:
1. 모듈 표면 — INTAKE_FIELDS 4항목 + 각 spec 필수 키
2. field_provided — 빈값/placeholder 거부, 실제값/'없음'/단문('앱') 허용
   (의미 품질 판단은 안 함 — 짧아도 비어있지 않으면 통과, 품질은 오케스트레이터 LLM 몫)
3. evaluate_intake — goal 만 있으면 missing 3, 4항목 다 있으면 complete
4. build_clarification_questions — 빠진 항목만, question/why 포함
5. build_intake_contract — status/missing_fields 정합, None 인자는 기존 보존
6. set_contract_field — 채움+재평가, unknown field 거부
7. intake_blockers / intake_gate — state 소비 표면
8. facade — build_state 가 intake_contract 박음, ensure_intake_contract 보강,
   intake_gate_block 이 미충족이면 exit 3 + clarification 출력, 완결이면 통과
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path("~/.claude/skills/release/scripts").expanduser()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from service_factory_intake_contract import (  # noqa: E402
    INTAKE_FIELDS,
    INTAKE_CONTRACT_VERSION,
    build_clarification_questions,
    build_intake_contract,
    evaluate_intake,
    field_keys,
    field_provided,
    intake_blockers,
    intake_gate,
    intake_status,
    set_contract_field,
)


# ---------------------------------------------------------------------------
# 1. 모듈 표면
# ---------------------------------------------------------------------------
def test_intake_fields_are_the_four_canonical_items():
    keys = [spec["key"] for spec in INTAKE_FIELDS]
    assert keys == ["goal", "forbidden", "definition_of_done", "approval_delegation"]
    assert field_keys() == keys


def test_each_field_spec_has_label_question_why():
    for spec in INTAKE_FIELDS:
        for key in ("key", "label", "question", "why"):
            assert spec.get(key), f"{spec.get('key')}: missing {key}"


# ---------------------------------------------------------------------------
# 2. field_provided
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("value", ["", "  ", "tbd", "TODO", "?", "...", "미정", "n/a", "-", None, 123])
def test_field_provided_rejects_empty_and_placeholder(value):
    assert field_provided(value) is False


@pytest.mark.parametrize("value", ["없음", "앱", "기본 안전선만", "로그인 가능한 대시보드", "코드/빌드는 자율, 배포는 승인"])
def test_field_provided_accepts_real_answers(value):
    assert field_provided(value) is True


# ---------------------------------------------------------------------------
# 3. evaluate_intake
# ---------------------------------------------------------------------------
def test_evaluate_with_only_goal_misses_three():
    contract = {"fields": {"goal": "할 일 관리 앱"}}
    ev = evaluate_intake(contract)
    assert ev["complete"] is False
    assert ev["missing"] == ["forbidden", "definition_of_done", "approval_delegation"]
    assert ev["provided"] == ["goal"]


def test_evaluate_with_all_four_is_complete():
    contract = {
        "fields": {
            "goal": "할 일 관리 앱",
            "forbidden": "기존 DB 스키마 변경 금지",
            "definition_of_done": "E2E 테스트 통과 + 로컬 빌드 성공",
            "approval_delegation": "코드/빌드/로컬테스트 자율, 배포는 승인",
        }
    }
    ev = evaluate_intake(contract)
    assert ev["complete"] is True
    assert ev["missing"] == []


def test_evaluate_handles_none_and_non_dict():
    assert evaluate_intake(None)["missing"] == field_keys()
    assert evaluate_intake({})["complete"] is False
    assert evaluate_intake({"fields": "nope"})["missing"] == field_keys()


# ---------------------------------------------------------------------------
# 4. build_clarification_questions
# ---------------------------------------------------------------------------
def test_clarification_questions_only_for_missing_fields():
    contract = {"fields": {"goal": "앱", "forbidden": "없음"}}
    questions = build_clarification_questions(contract)
    asked = [q["field"] for q in questions]
    assert asked == ["definition_of_done", "approval_delegation"]
    for q in questions:
        assert q["question"] and q["why"] and q["label"]


def test_no_questions_when_complete():
    contract = build_intake_contract("g", "f", "d", "a")
    assert build_clarification_questions(contract) == []


# ---------------------------------------------------------------------------
# 5. build_intake_contract
# ---------------------------------------------------------------------------
def test_build_contract_marks_clarification_required_when_incomplete():
    contract = build_intake_contract(goal="앱만 있음")
    assert contract["version"] == INTAKE_CONTRACT_VERSION
    assert contract["status"] == "clarification_required"
    assert "definition_of_done" in contract["missing_fields"]
    assert intake_status(contract) == "clarification_required"


def test_build_contract_complete_when_all_present():
    contract = build_intake_contract("g", "f", "d", "a")
    assert contract["status"] == "complete"
    assert contract["missing_fields"] == []
    assert intake_status(contract) == "complete"


def test_build_contract_none_args_preserve_existing():
    base = build_intake_contract(goal="g", forbidden="f")
    merged = build_intake_contract(definition_of_done="d", existing=base)
    assert merged["fields"]["goal"] == "g"
    assert merged["fields"]["forbidden"] == "f"
    assert merged["fields"]["definition_of_done"] == "d"


# ---------------------------------------------------------------------------
# 6. set_contract_field
# ---------------------------------------------------------------------------
def test_set_contract_field_fills_and_reevaluates():
    contract = build_intake_contract(goal="g")
    contract = set_contract_field(contract, "forbidden", "프로덕션 DB 직접 수정 금지")
    assert contract["fields"]["forbidden"] == "프로덕션 DB 직접 수정 금지"
    assert "forbidden" not in contract["missing_fields"]


def test_set_contract_field_rejects_unknown_field():
    with pytest.raises(ValueError):
        set_contract_field({"fields": {}}, "nonexistent", "x")


# ---------------------------------------------------------------------------
# 7. intake_blockers / intake_gate (state 소비)
# ---------------------------------------------------------------------------
def test_intake_blockers_lists_missing_keys():
    state = {"intake_contract": {"fields": {"goal": "g"}}}
    blockers = intake_blockers(state)
    assert "intake_missing:forbidden" in blockers
    assert "intake_missing:definition_of_done" in blockers
    assert "intake_missing:approval_delegation" in blockers


def test_intake_blockers_empty_when_complete():
    state = {"intake_contract": build_intake_contract("g", "f", "d", "a")}
    assert intake_blockers(state) == []


def test_intake_gate_structure():
    state = {"intake_contract": {"fields": {"goal": "g"}}}
    gate = intake_gate(state)
    assert gate["intake_complete"] is False
    assert set(gate["missing_fields"]) == {"forbidden", "definition_of_done", "approval_delegation"}
    assert len(gate["clarification_questions"]) == 3


# ---------------------------------------------------------------------------
# 8. facade — service_factory.py wiring
# ---------------------------------------------------------------------------
def test_build_state_embeds_intake_contract():
    import service_factory as sf

    state = sf.build_state(Path("/tmp/sf-intake-demo"), "할 일 앱", "local-staging")
    assert "intake_contract" in state
    assert state["intake_contract"]["status"] == "clarification_required"
    assert state["intake_contract"]["fields"]["goal"] == "할 일 앱"


def test_build_state_complete_when_four_args_given():
    import service_factory as sf

    state = sf.build_state(
        Path("/tmp/sf-intake-demo"),
        "할 일 앱",
        "local-staging",
        forbidden="DB 삭제 금지",
        definition_of_done="E2E 통과",
        approval_delegation="배포만 승인",
    )
    assert state["intake_contract"]["status"] == "complete"


def test_ensure_intake_contract_builds_for_legacy_state():
    import service_factory as sf

    legacy = {"goal": "레거시 목표"}  # intake_contract 없음
    sf.ensure_intake_contract(legacy)
    assert legacy["intake_contract"]["fields"]["goal"] == "레거시 목표"
    assert legacy["intake_contract"]["status"] == "clarification_required"


def test_intake_gate_block_blocks_incomplete(tmp_path, capsys):
    import service_factory as sf

    state = sf.build_state(tmp_path, "앱만", "local-staging")
    code = sf.intake_gate_block(state, tmp_path / "state.json", allow_incomplete=False, pretty=False)
    assert code == 3
    out = json.loads(capsys.readouterr().out)
    assert out["intake_clarification_required"] is True
    assert len(out["clarification_questions"]) == 3
    assert state["run_log"]["blocked_reason"] == "intake_clarification_required"
    # run_log 의 기존 식별 필드를 날리지 않고 in-place 보존하는지 (회귀 방지)
    assert state["run_log"].get("current_owner")
    assert state["run_log"].get("execution_controller")


def test_intake_gate_block_passes_when_complete(tmp_path):
    import service_factory as sf

    state = sf.build_state(
        tmp_path, "앱", "local-staging",
        forbidden="없음", definition_of_done="빌드+E2E", approval_delegation="배포 승인",
    )
    assert sf.intake_gate_block(state, tmp_path / "state.json", allow_incomplete=False, pretty=False) is None


def test_intake_gate_block_honors_allow_incomplete(tmp_path):
    import service_factory as sf

    state = sf.build_state(tmp_path, "앱만", "local-staging")
    assert sf.intake_gate_block(state, tmp_path / "state.json", allow_incomplete=True, pretty=False) is None


# ---------------------------------------------------------------------------
# 9. autopilot — intake 미충족 시 공회전하지 않고 즉시 멈춰 되묻는다 (회귀: 리뷰 major)
# ---------------------------------------------------------------------------
def test_autopilot_stops_on_intake_clarification_instead_of_spinning(tmp_path):
    import subprocess
    import sys as _sys

    project = tmp_path / "proj"
    project.mkdir()
    proc = subprocess.run(
        [
            _sys.executable,
            str(SCRIPT_DIR / "service_factory.py"),
            "autopilot",
            "--project",
            str(project),
            "--goal",
            "할 일 관리 앱",  # goal 만 → 3항목 미충족
            "--max-cycles",
            "5",
        ],
        text=True,
        capture_output=True,
        timeout=60,
    )
    # 공회전(max_cycles 소진) 대신 즉시 exit 3 + 되묻기
    assert proc.returncode == 3, proc.stdout + proc.stderr
    out = json.loads(proc.stdout)
    assert out["status"] == "intake_clarification_required"
    assert set(out["missing_fields"]) == {"forbidden", "definition_of_done", "approval_delegation"}
    assert len(out["clarification_questions"]) == 3
