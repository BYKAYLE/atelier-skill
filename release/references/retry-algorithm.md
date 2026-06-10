# Retry Algorithm — release

## 기본 흐름

```
Quality Gate FAIL
  │
  ├─ Retry 1: 같은 스킬 + 에러 컨텍스트
  │    Agent 프롬프트에 추가:
  │      "이전 시도에서 아래 에러 발생: {error}"
  │      "이 에러를 수정하라. 처음부터 다시 시작하지 말 것."
  │    → Quality Gate 재실행
  │
  ├─ Retry 1 FAIL → Retry 2: 같은 스킬 + 진단 우선
  │    Agent 프롬프트에 추가:
  │      "2회 연속 실패. 이전 에러들: {error1}, {error2}"
  │      "근본 원인을 먼저 진단하라. 빌드/테스트 출력을 주의 깊게 읽어라."
  │    → Quality Gate 재실행
  │
  ├─ Retry 2 FAIL → 판단 분기
  │    ├─ A) registry에 대안 스킬 있음
  │    │    → 대안 스킬로 교체 (새 Agent, 실패 컨텍스트 포함)
  │    │    → 대안도 2회 실패 → 사용자 에스컬레이션
  │    │
  │    ├─ B) 대안 없음
  │    │    → 사용자 에스컬레이션
  │    │
  │    └─ C) 환경 문제 (의존성/버전/설정)
  │         → 오케스트레이터가 직접 환경 수정
  │         → 원래 스킬로 재위임
  │
  └─ 에스컬레이션 보고 형식:
       "3번 시도했지만 해결하지 못했습니다."
       - 시도 1: {시도 내용 + 실패 원인}
       - 시도 2: {시도 내용 + 실패 원인}
       - 시도 3: {시도 내용 + 실패 원인}
       - 추정 원인: {분석}
       - 선택지:
         A) 다른 접근 방법으로 재시도
         B) 이 부분은 건너뛰고 나머지 진행
         C) 구체적 지시 제공
```

## 환경 문제 감지

아래 에러 패턴은 스킬 문제가 아니라 환경 문제로 판단한다:
- `MODULE_NOT_FOUND`, `Cannot find module`
- `command not found`
- `EACCES`, `Permission denied`
- `node: --experimental-*`, 버전 불일치 에러
- `pip install`, `npm install` 필요 힌트

환경 문제 시 오케스트레이터가 직접 설치/설정 수정 후 원래 스킬로 재위임.

## 에이전트 해고 절차 (v2.0)

2회 재시도 후에도 실패 시 에이전트를 "해고"하고 대체한다.

```
Retry 2 FAIL
  │
  ├─ 에이전트 해고: 현재 에이전트 작업 중단
  │    실패 원인 분석 + 에러 컨텍스트 수집
  │
  ├─ 대체 에이전트 스폰 (같은 스킬):
  │    "이전 에이전트가 {error}로 실패했다. 다른 접근을 시도하라."
  │    → 2회 재시도 가능
  │
  ├─ 대체도 실패 → 폴백 스킬 전환:
  │    registry.md Fallback 스킬로 새 에이전트 스폰
  │    → 2회 재시도 가능
  │
  └─ 폴백도 실패 → 판단:
       ├─ 블로킹 아님 → best-effort 선언 + 다음 스텝 진행
       └─ 블로킹 → 에스컬레이션 (autonomous-qc.md 참조)
```

해고 기록은 pipeline-state.json의 `fired_agents` 배열에 저장.
상세: `references/fleet-management.md`

## 성과 반영

- 1회 통과: pass++
- 재시도 후 통과: pass++, retries 기록
- 최종 실패: fail++, Last Failure에 에러 유형 기록
- 에이전트 해고: fired_count++ (pipeline-state.json)
- Pass Rate 50% 미만 (10+회 기준): SOT/skill-playbooks.md에 "대안 우선 선택" 경험 기록
