"""Service Factory — Intake Contract (4항목 완결성 게이트).

왜 이 모듈이 필요한가
---------------------
스텔라팩토리(Service Factory)의 무인 완주가 멈추는 진짜 원인은 프롬프트가 부실해서가
아니라 설계된 게이트 때문이다. 다만 사용자가 자연어 한 덩어리로 goal 만 던지면,
완료 판정(definition_of_done)·금지선(forbidden)·무인 허용 경계(approval_delegation)가
비어 있어 downstream 게이트(completion_claim_guard, approval gate)에서 막연히 멈춘다.

이 모듈은 **시작 시점(intake)에서 4항목 완결성을 결정적으로 검사**하고, 빠진 항목을
사용자에게 되물을 질문으로 변환한다. 역할 분리:

- 이 스크립트(결정적 게이트): "4항목이 채워졌는가" 만 판단한다. 자연어 의미 해석은 안 한다.
- 오케스트레이터(LLM = Stella/Release): 자연어 goal 을 4항목으로 분해하고, 비어 있는
  항목만 사용자에게 묻고, 답을 `intake --set` 으로 채운다.

이 분리 덕분에 오케스트레이터가 깜빡 묻지 않아도 `plan`/`run` 게이트가 막아 준다.

4항목 (service-factory.md "프롬프트는 복잡함이 아니라 구조" 절과 정합)
------------------------------------------------------------------
1. goal                — 목표
2. forbidden           — 금지선 (절대 하면 안 되는 것/영역)
3. definition_of_done  — 완료기준 (무엇이 충족되면 done 인가)
4. approval_delegation — 승인 위임 범위 (어디까지 사람 확인 없이 자율 허용)

주의: 4번(approval_delegation)은 "무인 허용 경계"를 표현할 뿐, 영구 안전 게이트
(db_data_deletion/production_deploy/paid_api_budget/external_communication/
offensive_security)는 이 값과 무관하게 항상 사람 승인을 요구한다.
"""
from __future__ import annotations

from typing import Any

INTAKE_CONTRACT_VERSION = "intake-contract-v1"

# 4항목 사양 — key, 한국어 라벨, 되물을 질문, 왜 필요한지.
INTAKE_FIELDS: list[dict[str, str]] = [
    {
        "key": "goal",
        "label": "목표",
        "question": "이 프로젝트로 무엇을 만들어야 하나요? 한 줄 핵심 목표를 알려주세요.",
        "why": "전체 작업의 방향. 비면 에이전트가 맥락을 잃고 얕게 끝낸다.",
    },
    {
        "key": "forbidden",
        "label": "금지선",
        "question": "절대 하면 안 되는 것이나 건드리면 안 되는 영역이 있나요? "
        "(특별히 없으면 '기본 안전선만'이라고 답해주세요)",
        "why": "무인 진행 중 위험 행동의 차단 범위. 비면 안전 경계가 모호해진다.",
    },
    {
        "key": "definition_of_done",
        "label": "완료기준(DoD)",
        "question": "무엇이 충족되면 '완료'로 볼까요? 검증 가능한 완료 조건을 알려주세요.",
        "why": "완료 판정 기준. 비면 done 에 도달하지 못하고 멈춘다.",
    },
    {
        "key": "approval_delegation",
        "label": "승인 위임 범위",
        "question": "어디까지 사람 확인 없이 자율로 진행해도 될까요? "
        "(예: 코드·빌드·로컬테스트는 자율, 배포·DB삭제·결제·외부발송은 승인 필요)",
        "why": "무인 허용 경계. 단 db/prod/paid/external/offensive 안전 게이트는 이와 무관하게 항상 승인 필요.",
    },
]

_FIELD_KEYS = [spec["key"] for spec in INTAKE_FIELDS]
_FIELD_SPEC_BY_KEY = {spec["key"]: spec for spec in INTAKE_FIELDS}

# 채워졌다고 보지 않는 placeholder 값들 (대소문자 무시, strip 후 비교).
_PLACEHOLDERS = {
    "",
    "tbd",
    "t.b.d",
    "todo",
    "to-do",
    "n/a",
    "na",
    "none",
    "null",
    "-",
    "?",
    "??",
    "...",
    "미정",
    "추후",
    "나중에",
    "later",
    "pending",
}


def field_keys() -> list[str]:
    """4항목 key 순서 리스트."""
    return list(_FIELD_KEYS)


def field_provided(value: Any) -> bool:
    """한 항목이 채워졌는지 결정적으로 판단 (구조적 완결성만, 의미 품질은 판단 안 함).

    채움 기준: 문자열 + strip 후 비어있지 않음 + placeholder 집합에 없음.
    예) '없음'·'앱'·'기본 안전선만' → 채움(O). ''·'tbd'·'?'·'미정'·'-' → 미충족(X).
    의미 적절성(예: 'x' 가 좋은 답인지)은 오케스트레이터(LLM)가 판단할 몫이다.
    """
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not stripped:
        return False
    return stripped.lower() not in _PLACEHOLDERS


def evaluate_intake(contract: dict[str, Any] | None) -> dict[str, Any]:
    """contract 의 4항목 충족 여부를 평가.

    반환: {complete: bool, missing: [key...], provided: [key...], field_status: {key: provided|missing}}
    """
    fields = {}
    if isinstance(contract, dict) and isinstance(contract.get("fields"), dict):
        fields = contract["fields"]
    missing: list[str] = []
    provided: list[str] = []
    field_status: dict[str, str] = {}
    for key in _FIELD_KEYS:
        if field_provided(fields.get(key)):
            field_status[key] = "provided"
            provided.append(key)
        else:
            field_status[key] = "missing"
            missing.append(key)
    return {
        "complete": not missing,
        "missing": missing,
        "provided": provided,
        "field_status": field_status,
    }


def build_clarification_questions(contract: dict[str, Any] | None) -> list[dict[str, str]]:
    """빠진 항목에 한해 사용자에게 되물을 질문 목록 생성 (채워진 항목은 묻지 않음)."""
    evaluation = evaluate_intake(contract)
    questions: list[dict[str, str]] = []
    for key in evaluation["missing"]:
        spec = _FIELD_SPEC_BY_KEY[key]
        questions.append(
            {
                "field": key,
                "label": spec["label"],
                "question": spec["question"],
                "why": spec["why"],
            }
        )
    return questions


def build_intake_contract(
    goal: str | None = None,
    forbidden: str | None = None,
    definition_of_done: str | None = None,
    approval_delegation: str | None = None,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """4항목 contract 를 생성/갱신. None 인 인자는 기존 값을 보존한다.

    반환 dict: {version, fields:{...}, status: complete|clarification_required,
                missing_fields:[...], field_status:{...}}
    """
    fields: dict[str, Any] = {}
    if isinstance(existing, dict) and isinstance(existing.get("fields"), dict):
        fields = dict(existing["fields"])
    incoming = {
        "goal": goal,
        "forbidden": forbidden,
        "definition_of_done": definition_of_done,
        "approval_delegation": approval_delegation,
    }
    for key, value in incoming.items():
        if value is not None:
            fields[key] = value
    contract = {"version": INTAKE_CONTRACT_VERSION, "fields": fields}
    evaluation = evaluate_intake(contract)
    contract["status"] = "complete" if evaluation["complete"] else "clarification_required"
    contract["missing_fields"] = evaluation["missing"]
    contract["field_status"] = evaluation["field_status"]
    return contract


def set_contract_field(contract: dict[str, Any] | None, field: str, value: str) -> dict[str, Any]:
    """contract 의 한 항목을 채우고 재평가한 새 contract 를 반환."""
    if field not in _FIELD_SPEC_BY_KEY:
        raise ValueError(f"unknown intake field: {field!r} (allowed: {_FIELD_KEYS})")
    fields: dict[str, Any] = {}
    if isinstance(contract, dict) and isinstance(contract.get("fields"), dict):
        fields = dict(contract["fields"])
    fields[field] = value
    return build_intake_contract(existing={"fields": fields})


def intake_status(contract: dict[str, Any] | None) -> str:
    """'complete' 또는 'clarification_required'."""
    return "complete" if evaluate_intake(contract)["complete"] else "clarification_required"


def intake_blockers(state: dict[str, Any] | None) -> list[str]:
    """state 의 intake_contract 미충족 항목을 blocker 리스트로 반환.

    예: ['intake_missing:definition_of_done', 'intake_missing:approval_delegation']
    """
    contract = None
    if isinstance(state, dict):
        contract = state.get("intake_contract")
    evaluation = evaluate_intake(contract if isinstance(contract, dict) else {})
    return [f"intake_missing:{key}" for key in evaluation["missing"]]


def intake_gate(state: dict[str, Any] | None) -> dict[str, Any]:
    """plan/run 게이트가 소비하는 구조화 결과.

    반환: {intake_complete: bool, missing_fields:[...], clarification_questions:[...]}
    """
    contract = state.get("intake_contract") if isinstance(state, dict) else None
    contract = contract if isinstance(contract, dict) else {}
    evaluation = evaluate_intake(contract)
    return {
        "intake_complete": evaluation["complete"],
        "missing_fields": evaluation["missing"],
        "clarification_questions": build_clarification_questions(contract),
    }
