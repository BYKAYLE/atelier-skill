# Resume Protocol — release v2.0

세션이 컨텍스트 한계로 중단된 후 새 세션에서 이어서 실행하기 위한 프로토콜.
Phase 0에서 자동 감지되며, 흡수/파이프라인 구성을 스킵하고 남은 스텝부터 재개한다.

## 감지 조건

Phase 0(Load Context)에서 아래를 확인:

1. 프로젝트 디렉토리에 `SOT/pipeline-state.json` 존재
2. `status`가 `"interrupted"` 또는 `"running"`
3. `steps[]` 중 `agent_status`가 `"pending"` 또는 `"running"`인 스텝이 1개 이상

세 조건 모두 충족 → **Resume 모드 진입**.

## Resume 경로

```
Phase 0 (Load Context)
  → pipeline-state.json 감지
  → Resume 모드 진입

Phase 0R (Resume Verification)
  → 완료된 스텝의 산출물 존재/유효성 검증
  → 프로젝트 현재 상태 빠른 파악 (빌드, 파일 존재 등)

Phase 4R (Resume Execution)
  → 첫 번째 pending/running 스텝부터 실행
  → 이후 Phase 5~7 정상 진행
```

**스킵되는 단계**: Phase 1(Triage), Phase 2(Absorption), Phase 3(Pipeline Construction)
**이유**: pipeline-state.json이 이미 모든 판단 결과를 담고 있음

## Phase 0R — Resume Verification

### 산출물 검증

완료된 스텝(`agent_status: "completed"`)에 대해:

```
for each completed step:
  1. artifacts[] 파일 존재 확인 (Glob)
  2. 개발 스텝이면: 빌드 가능 여부 확인 (빠른 컴파일 체크)
  3. 배포 스텝이면: 서비스 상태 확인 (health check)
```

**검증 실패 시**:
- 해당 스텝의 `agent_status`를 `"pending"`으로 되돌림
- `resume_context.rollback_steps`에 기록
- 해당 스텝부터 재실행

### 컨텍스트 복원

pipeline-state.json에서 복원하는 정보:
- `goal`: 원래 요청 목표
- `pattern`: 사용된 파이프라인 패턴
- `steps[].artifacts`: 완료된 산출물 경로
- `resume_context.notes`: 중단 시 남긴 메모
- `absorption_ref`: 흡수 문서 경로 (필요 시 참조)

## Phase 4R — Resume Execution

### 재개 지점 결정

```python
# 의사코드
first_pending = min(
    step.step for step in steps
    if step.agent_status in ("pending", "running")
)
resume_from = first_pending
```

### 실행 규칙

1. `running` 상태 스텝: 처음부터 재실행 (부분 완료 신뢰 안함)
2. `pending` 상태 스텝: 정상 실행
3. 이전 스텝의 `artifacts`를 에이전트 프롬프트에 포함
4. 나머지 Phase 5~7은 정상 흐름

### 에이전트 배치

- 원래 pipeline-state.json의 `model`, `tier` 설정을 유지
- 단, 이전 세션에서 `fired_agents`에 기록된 에이전트 구성은 피함
- 재시도 카운터(`retries`)는 세션 간 누적

## pipeline-state.json 확장 필드

기존 스키마에 추가되는 필드:

```json
{
  "status": "running|completed|failed|interrupted",
  "interrupted_at": "2026-03-19T12:00:00Z",
  "resume_count": 0,
  "resume_context": {
    "reason": "context_limit|user_stop|error",
    "notes": "중단 시점 상태 메모",
    "last_completed_step": 2,
    "rollback_steps": []
  },
  "absorption_ref": "SOT/project-absorptions/absorption-{timestamp}.md",
  "steps": [
    {
      "...existing fields...",
      "modified_files": ["path/to/file1", "path/to/file2"],
      "completion_note": "스텝 완료 시 요약 메모"
    }
  ]
}
```

### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `interrupted_at` | string | 중단 시각 (ISO 8601) |
| `resume_count` | number | 재개 횟수 (0부터) |
| `resume_context.reason` | string | 중단 사유 |
| `resume_context.notes` | string | 중단 시점 메모 (다음 세션 힌트) |
| `resume_context.last_completed_step` | number | 마지막 완료 스텝 번호 |
| `resume_context.rollback_steps` | number[] | 검증 실패로 롤백된 스텝 |
| `absorption_ref` | string | 흡수 문서 경로 |
| `steps[].modified_files` | string[] | 해당 스텝에서 변경/생성된 파일 |
| `steps[].completion_note` | string | 스텝 완료 시 요약 |

## 중단 시 기록 (Phase 6 확장)

세션이 끝날 때 (Stop 훅 또는 컨텍스트 한계 감지):

1. pipeline-state.json 갱신:
   - `status` → `"interrupted"`
   - `interrupted_at` → 현재 시각
   - `resume_context.reason` → 사유
   - `resume_context.notes` → 남은 작업 요약
   - `resume_context.last_completed_step` → 마지막 completed 스텝
2. 현재 실행 중인 스텝: `agent_status` → `"running"` 유지 (재개 시 재실행 대상)
3. 세션 로그에 "interrupted — resume required" 기록

## Delivery Report (Resume 모드)

Resume 후 Phase 7에서는 추가 정보를 포함:

```
### 세션 이력
- 총 세션: {N}회 (중단 {M}회, 재개 {M}회)
- 롤백된 스텝: {list 또는 "없음"}
```

## 안전장치

1. **무한 재개 방지**: `resume_count` ≥ 3이면 에스컬레이션 (사용자에게 상황 보고)
2. **산출물 무결성**: 재개 시 반드시 Phase 0R 검증 통과 후 실행
3. **흡수 문서 참조**: pipeline-state.json의 `absorption_ref`로 원래 판단 근거 접근 가능
4. **스텝 롤백**: 검증 실패 스텝은 자동 롤백 후 재실행 (수동 판단 불필요)
