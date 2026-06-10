# Agent Fleet Management — release v2.0

에이전트의 고용, 배치, 모니터링, 퇴역/해고를 관리한다.

## 에이전트 생명주기

```
조립 (Phase 3) → 배치 (Phase 4) → 모니터링 → 퇴역 or 해고
```

### 1. 조립 (Agent Fleet Assembly)

파이프라인 구성에서 필요한 에이전트 목록을 만든다.

**Fleet Roster 생성**:
```
Fleet for pipeline auto-{timestamp}:
- Agent A: {role} ({model}, Step {N}, Skill: {skill_name})
- Agent B: {role} ({model}, Step {M}, Skill: {skill_name})
- ...
```

**역할 유형**:

| 역할 | 모델 | 용도 |
|------|------|------|
| Researcher | sonnet | 시장 리서치, 자료 수집 |
| Planner | opus | PRD, 기획, 아키텍처 설계 |
| Designer | opus | UI/UX 디자인 시안 |
| Builder | opus/sonnet | 코드 구현 |
| QC Inspector | sonnet | 품질 검증 (비용 효율적) |
| Security Auditor | opus | 보안 감사 |
| Hardener | opus | 서비스 보강 (sisyphus_claude) |
| Deployer | opus | 배포 |

**에이전트당 부여**:
- 고유 역할명 (로깅용)
- 담당 스킬
- 담당 스텝 번호
- 모델 (opus/sonnet/haiku)
- 성공 기준 (absorption-protocol에서 도출)
- 토큰 예산 추정 (performance.md에서 해당 스킬 평균)

### 2. 배치 (Deployment)

스텝이 시작될 때 해당 에이전트를 Agent 도구로 스폰.

```
Agent(
    subagent_type="general-purpose",
    model="{roster.model}",
    prompt="{delegation-patterns에서 생성한 프롬프트}"
)
```

- **순차 스텝**: 이전 스텝 완료 후 다음 에이전트 스폰
- **병렬 스텝**: 같은 parallel_group의 에이전트를 동시 스폰
- 에이전트는 작업 완료 후 자동 종료 (일회용)

### 3. 모니터링

에이전트 완료 후 검수:

```
1. 완료 상태 확인: 에이전트가 정상 종료했는가?
2. 산출물 확인: 예상 파일이 존재하는가?
3. 성공 기준 확인: absorption의 criteria 충족하는가?
4. Level 1 QC: quality-gates.md 실행
5. 성능 기록: 토큰 사용량, 소요 시간, 재시도 횟수
```

### 4. 퇴역 (정상 종료)

- 에이전트의 산출물을 pipeline state에 기록
- 에이전트의 보고서를 다음 스텝의 컨텍스트로 전달
- performance.md에 성과 기록

### 5. 해고 (비정상 종료)

**해고 조건**: retry-algorithm에 따라 2회 재시도 후에도 실패

**해고 절차**:
1. 현재 에이전트 작업 중단
2. 실패 원인 분석 + 에러 컨텍스트 수집
3. 새 에이전트 스폰:
   - 동일 스킬 + 에러 컨텍스트 포함
   - "이전 접근이 {error}로 실패했다. 다른 방법을 시도하라."
4. 새 에이전트도 2회 실패 시 → 폴백 스킬로 전환

**해고 기록**:
```json
{
  "step": 2,
  "fired_agents": [
    {
      "attempt": 1,
      "model": "opus",
      "skill": "autonomous-dev",
      "error": "build failed: missing dependency",
      "tokens_used": 45000
    }
  ],
  "replacement": {
    "model": "opus",
    "skill": "autonomous-dev",
    "approach": "different strategy with explicit dependency check",
    "result": "PASS"
  }
}
```

## 에이전트 간 격리

- 각 에이전트는 독립적 (상태 공유 없음)
- 스텝 간 정보 전달은 **파일**을 통해서만
- 에이전트 N의 산출물 경로를 에이전트 N+1의 프롬프트에 포함
- 에이전트가 다른 에이전트를 직접 호출하지 않음

## 병렬 에이전트 관리

같은 parallel_group의 에이전트:
- 동시 스폰 가능 (Agent 도구 병렬 호출)
- 서로 파일을 수정하지 않아야 함 (충돌 방지)
- 모든 병렬 에이전트 완료 후 교차 정합성 검증 (autonomous-qc.md §2B)

## Pipeline State 에이전트 추적

`{project}/SOT/pipeline-state.json`에 per-step 에이전트 상태:

```json
{
  "pipeline_id": "auto-{timestamp}",
  "steps": [
    {
      "step": 0,
      "skill": "notebooklm",
      "agent_status": "completed",
      "agent_model": "sonnet",
      "retries": 0,
      "tokens_used": 25000,
      "artifacts": ["SOT/market-research-notebooklm.md"],
      "fired_agents": []
    }
  ]
}
```

## 동적 에이전트 생성

파이프라인 실행 중 예상치 못한 작업이 필요한 경우:
- release가 추가 에이전트를 동적으로 스폰 가능
- Fleet Roster에 추가 기록
- 예: 보안 감사 중 CRITICAL 발견 → 즉시 수정 에이전트 스폰

## 비용 최적화

- 단순 작업: haiku (비용 최소)
- 중간 작업: sonnet (성능/비용 균형)
- 복잡 작업: opus (품질 최대)
- performance.md의 스킬별 평균 토큰으로 예산 추정
- 예산 초과 경고: 예상의 2배 도달 시 세션 로그에 기록
