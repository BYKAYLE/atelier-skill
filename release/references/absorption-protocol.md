# Project Absorption Protocol — release v2.0

프로젝트를 깊게 이해하고, 모든 자율 판단의 근거가 되는 흡수 문서를 생성한다.

## 트리거

- **Pipeline/Standard 등급**: 반드시 실행
- **Express 등급**: 스킵 (직접 실행)

## 흡수 알고리즘

### Step 1: 의도 분해

사용자 요청을 구조화:
- **Goal**: 최종 결과물은 무엇인가? (1문장)
- **Deliverable**: 구체적 산출물 형태 (코드, 문서, 디자인, 서비스 등)
- **Domains**: 어떤 카테고리에 해당하는가? (registry.md 18개 중)
- **Scale**: Express | Standard | Pipeline | Mega (파일 수, 서비스 수, 기간 추정)
- **Implicit Requirements**: 명시되지 않았지만 당연히 필요한 것

### Step 2: 컨텍스트 마이닝

우선순위 순서대로 수집 (높을수록 신뢰):

1. **사용자 요청 텍스트** — 가장 높은 우선순위
2. **프로젝트 SOT** — `L1-project-summary.md`, `planning.md`, `ui-guide.md`, `CLAUDE.md`, `issues.md`
3. **코드베이스 구조** — `package.json`, `Cargo.toml`, 디렉토리 구조, README
4. **MEMORY.md** — 글로벌 사용자 컨텍스트 (회사 정보, 선호도, 과거 프로젝트)
5. **세션 히스토리** — 최근 5개 세션에서 패턴 (사용자 교정, 선호도)
6. **playbooks/** — 도메인별 누적 경험 (절차/이슈/체크리스트)

### Step 3: 모호성 자율 해결

모호한 부분이 있을 때:

```
for each ambiguity:
    resolution = infer_from_context(ambiguity, all_sources)
    if confidence > 0.7:
        resolve(ambiguity, resolution)
        document("HIGH confidence: {resolution} because {evidence}")
    else:
        resolve(ambiguity, best_guess)
        document("LOW confidence: {resolution} — 근거 부족, 최선 추정")
```

**Zero Questions 정책**: 실행 중 사용자에게 질문하지 않는다. 모르면 최선 판단 + 근거 기록 + 진행. 잘못된 판단은 Phase F에서 교정되어 user-model.md + 관련 플레이북에 누적된다.

**예외**: 불가역적 액션 (프로덕션 배포, 데이터 삭제 등)은 에스컬레이션.

### Step 4: 흡수 문서 생성

`SOT/project-absorptions/absorption-{YYYY-MM-DD-HHmmss}.md`에 저장.

## 흡수 문서 템플릿

```markdown
# Project Absorption: {project_name}

## Request
{사용자 원문 요청}

## Goal
{1문장 목표}

## Deliverable
{구체적 산출물 목록}

## Domains
{해당 카테고리 목록 + 근거}

## Scale
{Express|Standard|Pipeline|Mega} — {근거}

## Context Summary
### Project State
{기존 프로젝트면: 현재 상태, 코드 구조, 기술 스택}
{새 프로젝트면: 유사 프로젝트 참고, 기술 스택 제안}

### User Preferences (from history)
{세션 로그에서 추출한 사용자 선호도}

### Constraints
{CLAUDE.md, user-model.md, playbooks 등에서 추출한 제약 조건}

## Skills Needed
{스킬 목록 + 각 스킬을 선택한 이유}

## Risk Areas
{잘못될 수 있는 부분 + 대응 방안}

## Quality Criteria
{완성 판단 기준 — 구체적, 검증 가능}

## Autonomous Decisions
{이 흡수 과정에서 자율적으로 결정한 사항}
- {decision}: {rationale} [confidence: HIGH|LOW]

## Estimated Pipeline
{예상 스텝 수, 예상 토큰, 예상 에이전트 수}
```

## 흡수 깊이 (등급별)

| 등급 | 흡수 깊이 |
|------|----------|
| Express | 없음 (직접 실행) |
| Standard | 경량 흡수: Step 1 + Step 2 (SOT + 코드베이스만) + Step 4 |
| Pipeline | 전체 흡수: Step 1~4 전부 |
| Mega | 전체 흡수 + 시장 리서치 + 경쟁 분석 포함 |

## 프로젝트 연속성

같은 프로젝트에 대한 후속 요청 시:
1. 기존 흡수 문서 읽기 (`SOT/project-absorptions/` 최신)
2. 변경된 부분만 갱신 (전체 재흡수 불필요)
3. 새 흡수 문서 생성 (기존 문서 참조 링크 포함)

## 흡수 실패 시

흡수에 필요한 최소 정보가 없을 때 (예: "만들어줘"만 있고 뭘 만들지 없음):
- **1회만 질문**: "무엇을 만들까요?" (goal만 확인)
- 나머지는 모두 자율 결정
