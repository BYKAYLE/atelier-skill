# Autonomous QC Protocol — release v2.0

release가 사람 대신 모든 검수와 판단을 수행하는 프로토콜.

## QC 레벨 구조

```
Level 1: Step-Level QC (각 스텝 완료 시)
  └── Tier 1: 기계적 게이트 (빌드/테스트/타입/린트)
  └── Tier 2: 작업별 성공 기준
  └── Tier 2.5: 비개발 구조 검증

Level 2: Project-Level QC (파이프라인 완료 시)
  └── 목표 달성 검증
  └── 교차 정합성 검증
  └── 사용자 기대 모델링
```

## Level 1: Step-Level QC

기존 quality-gates.md의 Tier 1/2/2.5와 동일. 각 스텝 완료 후 즉시 실행.

## Level 2: Project-Level QC (NEW)

파이프라인 전체가 완료된 후, 최종 결과물을 프로젝트 레벨에서 검증.

### 2A. 목표 달성 검증

흡수 문서(`absorption-{timestamp}.md`)의 Quality Criteria를 하나씩 대조:

```
for each criterion in absorption.quality_criteria:
    result = verify(criterion)
    if PASS:
        record("PASS: {criterion}")
    elif PARTIAL:
        assess_severity()
        if acceptable_deviation:
            record("PARTIAL: {criterion} — 허용 가능한 편차: {reason}")
        else:
            trigger_fix(criterion)  # 해당 스텝 재실행
    elif FAIL:
        trigger_fix(criterion)
```

### 2B. 교차 정합성 검증

파이프라인 스텝 간 결과물이 일치하는지:

| 검증 항목 | 방법 |
|----------|------|
| PRD 기능 ↔ 구현 코드 | PRD의 기능 목록 vs 실제 구현된 라우트/컴포넌트 대조 |
| UI 가이드 ↔ 실제 UI | ui-guide.md 색상/레이아웃 vs 코드 내 스타일 대조 |
| 보안 감사 결과 ↔ 수정 | 보안 보고서의 CRITICAL 항목이 모두 수정되었는지 |
| 데이터 모델 ↔ DB 스키마 | PRD 데이터 모델 vs 실제 마이그레이션/스키마 대조 |

### 2C. 사용자 기대 모델링

세션 로그와 user-model.md에서 추출한 사용자 성향 기반 검증:

- **토큰 효율**: 파이프라인 총 토큰이 예상 대비 과다하지 않은지
- **품질 수준**: 과거 세션에서 사용자가 불만을 표시한 패턴이 반복되지 않는지
- **완성도**: "대충 만들어줘" vs "출시 수준까지" — 흡수 문서의 scale에 맞는지

## 판단 권한 범위

release가 자율적으로 결정할 수 있는 범위:

| 판단 | 권한 | 조건 |
|------|------|------|
| **수용** | 자율 | QC 전체 PASS |
| **수용 + 알려진 이슈** | 자율 | minor 이슈만 남음, 기능 영향 없음 |
| **재시도** | 자율 | retry-algorithm 범위 내 (2회까지) |
| **에이전트 해고** | 자율 | 2회 재시도 실패 (fleet-management.md 참조) |
| **폴백 스킬 전환** | 자율 | 해고 후 registry.md Fallback 존재 |
| **best-effort 선언** | 자율 | 3회 재시도 + 폴백 실패, but 블로킹 아님 |
| **디자인 방향 선택** | 자율 | 흡수 문서 + ui-guide + 사용자 히스토리 기반 |
| **기술 스택 결정** | 자율 | 흡수 문서 + 프로젝트 컨텍스트 기반 |

## 에스컬레이션 (사용자에게 올리는 유일한 경우)

아래 조건이 **모두** 충족될 때만:
1. 모든 재시도 소진 (retry 2회 + fallback 2회)
2. 폴백 스킬 없음 또는 폴백도 실패
3. 이슈가 블로킹 (다음 스텝 진행 불가)

에스컬레이션 시 보고 형식:
```markdown
## 에스컬레이션 보고

### 상황
{무엇이 실패했는지}

### 시도한 것
1. {attempt 1}: {result}
2. {attempt 2}: {result}
3. {fallback}: {result}

### 추정 원인
{분석}

### 선택지
A) {대안 접근}
B) {스킵하고 나머지 진행}
C) {구체적 지시 요청}
```

## 디자인 자율 선택 프로토콜

시안 여러 방향 생성 후 release가 자율 선택:

1. 에이전트가 3+ 디자인 방향 생성
2. 각 방향을 평가:
   - ui-guide.md 존재 시: 일치도 가장 높은 방향
   - 사용자 과거 선호도 (세션 로그): 과거 선택 패턴 반영
   - 프로젝트 산업/도메인: 해당 분야 표준 UX 패턴
3. 선택 근거를 pipeline state에 기록
4. 사용자가 최종 결과물에서 디자인 불만 시 → Phase F → user-model.md + 관련 플레이북에 선호도 기록

**예외**: 사용자가 "시안 보여줘" / "디자인 확인할래"라고 명시 → CHECKPOINT 모드 전환
