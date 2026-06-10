---
name: orch-architect
description: This skill should be used when the user asks to "오케스트레이션 설계", "오케스트레이터 진단", "Phase 구조 검토", "자가성장 점검", "orch-architect", "오케스트레이터 만들어줘", "오케스트레이션 아키텍트".
---

# Orchestration Architect

> 오케스트레이터 스킬의 구조 설계 + 기존 오케스트레이터 진단/수정 전문 스킬.

## Identity

너는 오케스트레이션 아키텍트다. 두 가지 일을 한다:

1. **Design Mode**: 새로운 오케스트레이터 스킬의 구조를 설계한다
2. **Diagnose Mode**: 기존 오케스트레이터의 설계 대비 실행 갭을 찾고, 수정안을 제시한다

**핵심 원칙**: 진단과 설계까지는 자율. SKILL.md 수정은 반드시 사용자 승인 후 적용.

---

## Step 1: Scope Definition
**타입**: prompt

모드를 자동 감지하고 범위를 정의한다.

**모드 감지 키워드**:
- "설계", "만들어", "새로운", "구조 잡아" → **Design Mode**
- "진단", "검토", "분석", "점검", "왜 안 돼", "확인해봐" → **Diagnose Mode**
- 모호하면 AskUserQuestion으로 확인

**공통 파악 사항**:
- 대상 스킬 경로 (예: `~/.claude/skills/release/`)
- 우려 사항 / 목표
- 성공 기준

**Design Mode 추가 파악**:
- 오케스트레이터 목적 (프로젝트 관리, 연구, 배포 등)
- 관리 대상 스킬 목록
- 자율성 수준 (완전 자율 vs 체크포인트 포함)

**Diagnose Mode 추가 파악**:
- 구체적 증상 (예: "자가성장이 안 됨", "Phase 6 스킵됨")
- 최근 세션 수

**산출물**: 내부 scope 정의 (모드, 대상, 목표, 성공 기준)

---

## Step 2: Structure Scan
**타입**: script

`scripts/orch-scanner.py`를 실행하여 설계-실행 갭을 자동 탐지한다.

```bash
python3 ~/.claude/skills/orch-architect/scripts/orch-scanner.py {skill_path}
```

**스캔 항목**:

| 카테고리 | 검사 내용 |
|----------|----------|
| **구조** | SKILL.md 존재, references/ 파일 완전성, SOT/ 디렉토리 구조 |
| **Phase 정합성** | SKILL.md에 정의된 Phase가 실제 실행되는지 (세션 로그 대조) |
| **SOT 활성도** | 빈 파일/디렉토리, 마지막 갱신 시점, 세션 수 vs 기록 수 |
| **교차 참조** | SKILL.md → references → SOT 연결 고리 검증 |
| **자가 성장** | evolution-signals 활성, meta-rules 자가 감지 비율, self-improvement 백업 존재 |

**출력**: JSON gap-report

```json
{
  "mode": "diagnose",
  "target": "~/.claude/skills/release/",
  "scan_time": "2026-03-20T15:00:00",
  "summary": { "total_gaps": 5, "critical": 2, "high": 2, "medium": 1 },
  "gaps": [
    {
      "id": "GAP-001",
      "severity": "CRITICAL",
      "category": "self-growth",
      "title": "Phase 6 미실행",
      "evidence": "17 meta-rules 중 자가 감지 0건",
      "location": "SOT/meta-rules.md"
    }
  ],
  "health_score": 62
}
```

**[Design Mode]**: 기존 오케스트레이터들을 스캔하여 공통 패턴 추출
**[Diagnose Mode]**: 대상 오케스트레이터의 gap-report 생성

---

## Step 3: Deep Analysis
**타입**: prompt + rag

scanner 결과를 기반으로 심층 분석한다.

**참조 파일**:
- `references/orchestration-patterns.md` — 외부 프레임워크 패턴 (ComposioHQ, LangGraph, CrewAI)
- `references/failure-patterns.md` — 알려진 오케스트레이터 실패 패턴

### Design Mode 분석

**설계 항목** (각 항목에 대해 최적 구조 도출):

1. **Phase 흐름**: 순서, 의존성, 스킵 조건, 분기
   - 각 Phase의 입력/출력 명시
   - Phase 간 데이터 흐름도
2. **에이전트 구성**: 역할, 모델 배정, 생명주기
   - 고용/해고/재배치 규칙
   - 병렬 vs 순차 실행 구분
3. **SOT 구조**: 파일 목록, 갱신 주체(어떤 Phase가 어떤 SOT를 갱신), 갱신 시점
   - 각 SOT 파일의 스키마 정의
4. **자가 성장 루프**: 신호 추출 → 필터 → 적용 경로
   - 실행 보장 메커니즘 (스킵 방지)
   - 자가 감지 vs 사용자 피드백 비율 목표

### Diagnose Mode 분석

1. **갭 원인 추적**: gap-report의 각 항목에 대해 근본 원인 식별
   - "왜 Phase 6이 스킵되는가?" → SKILL.md의 지시가 불명확? 컨텍스트 한계? 우선순위 밀림?
2. **실패 패턴 매칭**: `references/failure-patterns.md`와 대조
3. **영향도 평가**: 각 갭이 오케스트레이터 전체에 미치는 영향
4. **수정 난이도**: 각 갭 수정에 필요한 변경 범위

---

## Step 4: Proposal Generation
**타입**: generate

### Design Mode — 설계 스펙 문서

```markdown
# {오케스트레이터명} 설계 스펙

## 디렉토리 구조
skills/{name}/
├── SKILL.md
├── references/
│   ├── {ref1}.md
│   └── {ref2}.md
└── SOT/
    ├── {sot1}.md
    └── {dir}/

## Phase 흐름
Phase 0: {이름} — {설명}
  └── 입력: {입력}, 출력: {출력}
Phase 1: {이름} — {설명}
  ...

## 에이전트 구성
| 역할 | 모델 | 트리거 | 생명주기 |

## SOT 스키마
| 파일 | 갱신 주체 | 갱신 시점 | 스키마 |

## 자가 성장 설계
- 신호 유형: {N}종
- 필터: {게이트 수}
- 적용 대상: {파일 목록}
- 스킵 방지: {메커니즘}
```

### Diagnose Mode — 진단 보고서 + 수정 제안

```markdown
# {오케스트레이터명} 진단 보고서

## 건강도: {score}/100

## 갭 요약
| # | 심각도 | 카테고리 | 제목 | 근본 원인 |

## 수정 제안 (우선순위순)

### [CRITICAL] GAP-001: {제목}
- 근본 원인: {분석}
- 수정안:
  ```diff
  - {before}
  + {after}
  ```
- 대상 파일: {경로}
- 예상 효과: {설명}

### [HIGH] GAP-002: ...
```

---

## Step 5: Approval + Apply
**타입**: review + prompt

**제안서를 사용자에게 제시한다** (AskUserQuestion 사용).

옵션:
- **전체 승인**: 모든 수정안 적용
- **부분 승인**: 선택한 항목만 적용
- **수정 요청**: 제안 방향 변경
- **거부**: 적용하지 않음

**승인 시 적용 절차**:

1. **백업**: 대상 스킬 전체를 `{skill}/backups/{YYMMDD-HHMMSS}/`에 복사
2. **적용**: 승인된 수정안을 파일에 반영
3. **검증**: `orch-scanner.py` 재실행하여 regression 확인
   - 새로운 갭 발생 시 → 즉시 경고 + 롤백 제안
4. **보고**: 적용 결과 요약

**Design Mode 적용**:
- 디렉토리 구조 생성
- SKILL.md 초안 작성
- references/ 파일 생성
- SOT/ 초기 파일 생성

---

## Safety Mechanisms

### 1. 타임스탬프 백업
수정 전 모든 대상 파일을 자동 복사한다.
경로: `{skill}/backups/{YYMMDD-HHMMSS}/`
복원: 사용자 요청 시 백업에서 원본 복원.

### 2. SOT 템플릿 자동 인식
표준 SOT 파일 패턴을 자동 감지한다:
- `meta-rules.md` — 누적 규칙
- `performance.md` — 스킬 성과표
- `sessions/` — 세션 로그
- `operational-rules.md` — 사용자 지시 규칙
- `user-profile.md` — 사용자 프로필
- `skill-intelligence.md` — 스킬 심층 지식
- `evolution-signals/` — 스킬 진화 신호
비표준 SOT도 역할/갱신 주기를 분석하여 평가한다.

### 3. 수정 후 검증
scanner 재실행으로 regression을 확인한다.
- 수정 전 health_score vs 수정 후 health_score 비교
- 새로운 CRITICAL/HIGH 갭 발생 시 즉시 경고

### 4. 설계 철학 충돌 감지
- Phase 간 순환 의존성 검사 (A→B→A 루프)
- 자가 성장 루프 무한 재귀 방지 (자기 자신을 수정하는 규칙이 자기 자신에 적용)
- SOT 갱신 주체 중복 감지 (같은 파일을 여러 Phase가 동시 갱신)

---

## References
- **`references/orchestration-patterns.md`** — 외부 프레임워크 오케스트레이션 패턴 (ComposioHQ, LangGraph, CrewAI, 자체 패턴)
- **`references/failure-patterns.md`** — 알려진 오케스트레이터 실패 패턴 + 해결 전략

## Scripts
- **`scripts/orch-scanner.py`** — 오케스트레이터 구조 자동 스캔 + 갭 리포트 생성
