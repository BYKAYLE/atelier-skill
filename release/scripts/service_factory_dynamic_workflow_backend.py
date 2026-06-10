"""Service Factory — `dynamic_workflow` spawn_runtime backend.

왜 이 모듈이 필요한가
---------------------
v0.2 Service Factory의 `assess` readiness 판정은 `foundation_ready_but_not_autonomous`다.
service-factory.md 명시:

    spawn_runtime이 붙어 agent_requests를 실제 subagent/worktree 실행으로
    연결해야 `pilot_ready`로 올라갈 수 있다.

기존 4 backend(`manual`/`command`/`codex-exec`/`codex_bridge`)는 모두 per-request
외부 subprocess 호출 모델이라 **stage 단위 결정성 fan-out**을 못 한다 — Workflow
도구의 핵심 가치(`parallel()`/`pipeline()`로 N-way 병렬 + worktree 격리 + schema
강제 + budget 추적)를 직접 활용 못 한다.

이 모듈은 그 빈 자리를 채우는 dispatch-side 어댑터다.

설계
----
parent agent가 사용하는 Claude Code Workflow 도구는 in-process 호출이라 외부
Python 스크립트가 직접 호출할 수 없다. 따라서 이 백엔드는 codex_bridge와 동일한
**dispatch/collect 분리** 패턴을 따른다:

1. dispatch 단계 (이 모듈)
   - stage에서 처리할 request 리스트를 모은다
   - 각 request → Workflow `agent()` 호출이 되도록 `parallel(...)` script를 직조한다
   - `dispatch.workflow.js`(parent가 Workflow tool로 실행) + `dispatch.instructions.md`
     (parent용 한 화면 지침)를 산출한다
   - 각 request의 `artifact_dir/result.json` 경로를 script가 알게 inline한다

2. parent 실행 (이 모듈 밖)
   - parent agent가 `dispatch.workflow.js`를 Workflow 도구로 실행
   - Workflow가 각 agent를 schema 강제로 호출하고 결과 array 반환
   - parent가 결과를 각 `artifact_dir/result.json`에 직렬화

3. collect 단계 (기존 cmd_collect 재사용)
   - 기존 `service_factory.py collect`가 `result.json`을 ingest

핵심 원칙
--------
- LLM 0 (이 모듈 자체는 모델 호출 안 함, script 텍스트 조립만)
- Architecture-First Modular: 신규 파일, service_factory.py에는 thin wiring만
- 매매 룰 / Stella ontology service-factory.yaml 의 절대 경계와 동일 — 새 위험 없음
- 한도 강제: state.limits.max_parallel_agents 를 Workflow의 동시 batch에 lock
- 게이트 차단: command_allowed() 가 거부한 prompt는 workflow script 진입 금지
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Domain — script 조립의 단일 진실원
# ---------------------------------------------------------------------------
DEFAULT_MAX_PARALLEL = 3
ABSOLUTE_MAX_PARALLEL = 16  # Workflow 도구 자체 cap과 정합 (min(16, cpu-2))
DEFAULT_AGENT_TYPE = "general-purpose"

# Workflow agent 결과가 따라야 할 schema — Factory result.json 계약과 정합.
# Factory의 load_child_result()가 읽는 필드와 1:1.
WORKFLOW_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["status", "summary"],
    "additionalProperties": True,
    "properties": {
        "status": {
            "type": "string",
            "enum": ["completed", "validation_required", "blocked", "failed"],
        },
        "summary": {"type": "string", "minLength": 1},
        "modified_files": {"type": "array", "items": {"type": "string"}},
        "commands_run": {"type": "array"},
        "findings_or_risks": {"type": "array"},
        "next_step": {"type": ["string", "null"]},
        "permission_required": {"type": ["boolean", "null"]},
    },
}


# ---------------------------------------------------------------------------
# Domain — 게이트 차단 키워드 (paid/db/prod/offensive/external)
# service-factory.md의 5 영구 게이트와 동일 의도.
# ---------------------------------------------------------------------------
GATE_BLOCK_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("db_data_deletion", "drop table"),
    ("db_data_deletion", "truncate "),
    ("db_data_deletion", "rm -rf /volume"),
    ("production_deploy", "kubectl apply -f prod"),
    ("paid_api_budget", "openai.com/v1"),
    ("external_communication", "smtp"),
    ("offensive_security", "nmap -sS"),
)


def acceptance_command_is_paper_safe(text: str) -> tuple[bool, list[str]]:
    """간단 가드 — workflow script 안 prompt가 위험 명령을 내포하면 식별.

    대소문자 무관 substring 매치. GATE_BLOCK_KEYWORDS 가 mixed-case 로 선언돼도
    동일하게 검출되도록 양변 모두 lowercase 로 비교한다.
    """
    violations: list[str] = []
    low = text.lower()
    for gate, kw in GATE_BLOCK_KEYWORDS:
        if kw.lower() in low:
            violations.append(f"{gate}: matched '{kw}'")
    return (not violations, violations)


# ---------------------------------------------------------------------------
# Application — request 리스트 → Workflow script + instructions
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_max_parallel(state: dict[str, Any], override: int | None) -> int:
    if override is not None:
        if not isinstance(override, int) or override <= 0:
            raise ValueError("max_parallel override must be a positive int")
        return min(override, ABSOLUTE_MAX_PARALLEL)
    limits = state.get("limits") or {}
    val = limits.get("max_parallel_agents") or DEFAULT_MAX_PARALLEL
    if not isinstance(val, int) or val <= 0:
        val = DEFAULT_MAX_PARALLEL
    return min(val, ABSOLUTE_MAX_PARALLEL)


def _resolve_agent_type(request: dict[str, Any]) -> str:
    """request.agent_type 가 Claude Code 내장 subagent와 매칭되면 그걸, 아니면 default."""
    requested = request.get("agent_type") or ""
    # Factory의 agent_type 명명은 도메인 role (frontend-developer 등)이라 Workflow의
    # 내장 subagent 이름과 1:1 매칭이 안 보장된다. 단순화: 도메인 명칭 그대로 넘기되,
    # Workflow가 모르면 general-purpose로 fallback (Workflow tool 자체에 fallback 없음
    # — 그래서 여기선 빈 문자열 or 알려진 prefix만 통과시키고 그 외는 default).
    known = {"general-purpose", "Explore", "Plan", "code-reviewer", "claude"}
    if requested in known:
        return requested
    return DEFAULT_AGENT_TYPE


def _agent_label(request: dict[str, Any]) -> str:
    stage = str(request.get("stage", "stage"))
    rid = str(request.get("id", "req"))
    return f"{stage}::{rid}"


def _build_prompt(request: dict[str, Any], state: dict[str, Any]) -> str:
    """Workflow agent()에 들어갈 prompt 본문.

    service_factory.py 의 prompt_for_request() 가 만든 본 prompt 파일을 참조하게
    하되, 인라인 instruction(완료 정의·result schema·금지)을 명시한다.
    """
    project_path = state.get("project", {}).get("path", "")
    prompt_path = request.get("prompt_path", "")
    artifact_dir = request.get("artifact_dir", "")
    return (
        "너는 kansicrich/Stella Service Factory 의 stage worker 다.\n"
        f"역할/지시: {project_path}/{prompt_path} 파일을 읽고 그 stage prompt 를 그대로 수행하라.\n"
        "절대 경계:\n"
        "- LIVE 전환·실거래 주문·DB 삭제·prod 배포·유료 API 호출 절대 금지\n"
        "- 매매 룰 임계/regime/sizing/leverage/MTF/gate 직접 변경 금지 (필요 시 escalate)\n"
        "- 본 prompt 파일이 명시한 file_lease 의 write owner 범위만 수정\n"
        "- 응답은 반드시 schema 에 맞는 StructuredOutput 으로 끝낼 것\n"
        "산출:\n"
        f"- artifact_dir: {artifact_dir}\n"
        "- 응답이 schema 에 맞으면 parent 가 result.json 으로 직렬화한다\n"
    )


def render_workflow_script(
    state: dict[str, Any],
    requests: list[dict[str, Any]],
    run_id: str,
    *,
    max_parallel: int | None = None,
    workflow_name: str = "service-factory-stage-fanout",
    description: str = "Service Factory dynamic_workflow backend — stage-level fan-out",
) -> str:
    """Workflow 도구가 그대로 실행할 수 있는 JS script.

    parallel(items.map(r => () => agent(prompt, {label, schema, agentType})))
    로 한 stage 의 모든 request 를 fan-out 한다. concurrency 는 Workflow 의 동시
    cap 으로 자연히 max(min(16, cpu-2)) 로 묶이고, 추가로 본 모듈의
    `max_parallel_agents` 한도를 batch 직렬 분할로 적용한다.
    """
    if not requests:
        raise ValueError("requests is empty — nothing to fan out")
    mp = _resolve_max_parallel(state, max_parallel)

    items: list[dict[str, Any]] = []
    for r in requests:
        prompt = _build_prompt(r, state)
        ok, violations = acceptance_command_is_paper_safe(prompt)
        items.append(
            {
                "id": r.get("id"),
                "stage": r.get("stage"),
                "agent_type": _resolve_agent_type(r),
                "label": _agent_label(r),
                "prompt": prompt,
                "artifact_dir": r.get("artifact_dir"),
                "gate_violations": violations,
                "gate_safe": ok,
            }
        )

    # phases meta — Workflow 도구가 progress UI 에 사용
    phases = [{"title": "Fan-out", "detail": f"{len(items)} stage requests in batches of {mp}"}]

    meta_js = "export const meta = " + json.dumps(
        {"name": workflow_name, "description": description, "phases": phases},
        ensure_ascii=False,
        indent=2,
    )

    schema_js = "const RESULT_SCHEMA = " + json.dumps(WORKFLOW_RESULT_SCHEMA, ensure_ascii=False, indent=2) + ";"
    items_js = "const ITEMS = " + json.dumps(items, ensure_ascii=False, indent=2) + ";"
    mp_js = f"const MAX_PARALLEL = {mp};"

    body = """
phase('Fan-out')
log(`Service Factory dynamic_workflow — ${ITEMS.length} requests, max parallel ${MAX_PARALLEL}`)

// gate-violating items 는 호출 자체를 건너뛴다 (paper-safe 보장).
const safeItems = ITEMS.filter(it => it.gate_safe)
const blockedItems = ITEMS.filter(it => !it.gate_safe)
if (blockedItems.length) {
  log(`blocked by gate: ${blockedItems.map(b => b.id).join(', ')}`)
}

// max_parallel 한도 — Workflow 의 동시 cap(min(16, cpu-2)) 위에서 batch 로 분할.
async function inBatches(items, size, work) {
  const out = []
  for (let i = 0; i < items.length; i += size) {
    const batch = items.slice(i, i + size)
    const res = await parallel(batch.map(it => () => work(it)))
    out.push(...res)
  }
  return out
}

const results = await inBatches(safeItems, MAX_PARALLEL, async (it) => {
  const out = await agent(it.prompt, {
    label: it.label,
    phase: 'Fan-out',
    schema: RESULT_SCHEMA,
    agentType: it.agent_type,
  })
  return { id: it.id, stage: it.stage, artifact_dir: it.artifact_dir, result: out }
})

// gate-blocked 도 동등한 결과 포맷으로 emit (parent 가 result.json 으로 직렬화 시 일관)
for (const b of blockedItems) {
  results.push({
    id: b.id,
    stage: b.stage,
    artifact_dir: b.artifact_dir,
    result: {
      status: 'blocked',
      summary: 'workflow gate blocked: ' + b.gate_violations.join('; '),
      modified_files: [],
      commands_run: [],
      findings_or_risks: b.gate_violations,
      next_step: 'escalate to release/Stella for gate approval',
      permission_required: true,
    },
  })
}

return results
"""
    return "\n".join([meta_js, "", schema_js, "", items_js, "", mp_js, body])


def render_workflow_instructions(
    state: dict[str, Any],
    requests: list[dict[str, Any]],
    run_id: str,
    script_path: Path,
    *,
    state_path: Path,
) -> str:
    """parent agent용 한 화면 markdown 지침.

    Workflow 도구로 script_path 실행 후, 결과 array를 각 request의 result.json으로
    직렬화하라는 절차. 기존 codex_bridge dispatch.md와 같은 톤.
    """
    project_path = state.get("project", {}).get("path", "")
    lines: list[str] = []
    lines.append("# Service Factory · dynamic_workflow dispatch")
    lines.append("")
    lines.append(f"- `run_id`: `{run_id}`")
    lines.append(f"- `project`: `{project_path}`")
    lines.append(f"- `requests`: {len(requests)} (stage-level fan-out)")
    lines.append(f"- `workflow_script`: `{script_path}`")
    lines.append(f"- `state_file`: `{state_path}`")
    lines.append("")
    lines.append("## 1. Workflow 도구로 script 실행")
    lines.append("")
    lines.append("Claude Code 의 `Workflow` 도구를 호출하라. `scriptPath` 인자로 위 `workflow_script` 경로를 넘긴다.")
    lines.append("실행이 끝나면 길이 N 의 결과 배열을 반환받는다 — 각 원소는 `{id, stage, artifact_dir, result}` 형태.")
    lines.append("")
    lines.append("## 2. 각 결과를 result.json 으로 직렬화")
    lines.append("")
    lines.append("각 결과 원소 `e` 에 대해:")
    lines.append("")
    lines.append("```")
    lines.append("path = e.artifact_dir + '/result.json'")
    lines.append("write JSON dump of e.result to that path (UTF-8, indent=2)")
    lines.append("```")
    lines.append("")
    lines.append("## 3. collect 명령으로 흡수")
    lines.append("")
    lines.append("```bash")
    lines.append(
        f"python3 ~/.claude/skills/release/scripts/service_factory.py collect --state '{state_path}'"
    )
    lines.append("```")
    lines.append("")
    lines.append("`collect` 가 각 `result.json` 을 읽어 state 의 request status 를 갱신한다.")
    lines.append("- `status=completed` 인데 trust 검증 실패 → `validation_required` 로 자동 격하")
    lines.append("- `status=blocked` → 그대로 blocked (gate 승인 필요)")
    lines.append("")
    lines.append("## 절대 경계 (workflow agent 가 절대 하지 않을 것)")
    lines.append("")
    lines.append("- LIVE 전환·실거래 주문·DB 삭제·prod 배포·유료 API 호출")
    lines.append("- 매매 룰 임계/regime/sizing/leverage/MTF/gate 직접 변경 (escalate 만)")
    lines.append("- file_lease.write 범위 밖 수정")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Adapter — Factory state ↔ filesystem
# ---------------------------------------------------------------------------
def collect_dispatch_requests(state: dict[str, Any], *, stage: str | None = None) -> list[dict[str, Any]]:
    """이번 dispatch 에 묶을 request 들을 state 에서 골라낸다.

    선택 기준: `status` 가 `queued` 또는 `in_progress` 이고 `prompt_path` 가 있는 것.
    `stage` 지정 시 그 stage 만.
    """
    raw = state.get("agent_requests") or []
    out: list[dict[str, Any]] = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        st = r.get("status", "queued")
        if st not in ("queued", "in_progress"):
            continue
        if not r.get("prompt_path"):
            continue
        if stage and r.get("stage") != stage:
            continue
        out.append(r)
    return out


def write_dispatch(
    *,
    state: dict[str, Any],
    state_path: Path,
    bridge_dir: Path,
    run_id: str,
    requests: list[dict[str, Any]],
    max_parallel: int | None = None,
) -> dict[str, Any]:
    """Stage-level fan-out dispatch payload 를 디스크에 떨군다.

    출력:
      <bridge_dir>/<run_id>/dynamic_workflow/dispatch.workflow.js
      <bridge_dir>/<run_id>/dynamic_workflow/dispatch.instructions.md
      <bridge_dir>/<run_id>/dynamic_workflow/dispatch.json   (machine-readable summary)
    """
    if not requests:
        raise ValueError("no requests to dispatch")
    out_dir = bridge_dir / run_id / "dynamic_workflow"
    out_dir.mkdir(parents=True, exist_ok=True)

    script = render_workflow_script(state, requests, run_id, max_parallel=max_parallel)
    script_path = out_dir / "dispatch.workflow.js"
    script_path.write_text(script, encoding="utf-8")

    instr = render_workflow_instructions(state, requests, run_id, script_path, state_path=state_path)
    instr_path = out_dir / "dispatch.instructions.md"
    instr_path.write_text(instr, encoding="utf-8")

    summary = {
        "factory_id": state.get("factory_id"),
        "run_id": run_id,
        "backend": "dynamic_workflow",
        "request_count": len(requests),
        "max_parallel": _resolve_max_parallel(state, max_parallel),
        "workflow_script": str(script_path),
        "instructions": str(instr_path),
        "state_file": str(state_path),
        "request_ids": [r.get("id") for r in requests],
        "generated_at_utc": _now_iso(),
    }
    summary_path = out_dir / "dispatch.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary
