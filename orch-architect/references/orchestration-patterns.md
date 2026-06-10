# Orchestration Patterns Reference

> 외부 프레임워크 + 자체 오케스트레이터에서 추출한 설계 패턴.
> Step 3 (Deep Analysis)에서 참조.

---

## 1. ComposioHQ Agent Orchestrator 패턴

**핵심**: 에이전트를 독립 실행 단위로 관리. 고용/해고/재배치의 자율권.

| 요소 | 패턴 |
|------|------|
| Agent Lifecycle | spawn → execute → evaluate → retain/fire |
| Task Queue | 동적 큐 — 우선순위 기반 배치 |
| Delegation | 프롬프트 템플릿 + 컨텍스트 주입 |
| QC | 스텝별 exit code 기반 기계적 검증 |
| Retry | N회 재시도 → 에이전트 교체 → 폴백 스킬 |

**적용 사례**: release v2.0 (Fleet Management, Phase 4 Execution)

---

## 2. LangGraph 상태 머신 패턴

**핵심**: 각 Phase를 상태(state)로, Phase 간 전환을 엣지(edge)로 모델링.

| 요소 | 패턴 |
|------|------|
| State | 각 Phase = 하나의 상태 (입력/출력 명시) |
| Edge | 조건부 전환 (성공/실패/스킵) |
| Checkpoint | 상태 저장 → 중단/재개 가능 |
| Branching | 조건에 따라 다른 Phase로 분기 |
| Cycle | 자가 성장 = 순환 엣지 (Phase N → Phase 0) |

**적용 가능성**: Resume 프로토콜, 조건부 Phase 스킵

---

## 3. CrewAI 에이전트 협업 패턴

**핵심**: 역할(Role) 기반 에이전트 구성. 각 에이전트에 명확한 역할/목표/백스토리.

| 요소 | 패턴 |
|------|------|
| Role Definition | 역할명 + 목표 + 제약 조건 |
| Task Assignment | Task → Agent 매핑 (1:1 또는 1:N) |
| Process | Sequential / Hierarchical / Consensual |
| Memory | 에이전트 간 공유 메모리 (SOT 파일) |
| Delegation | 에이전트가 다른 에이전트에게 위임 가능 |

**적용 사례**: night-lab (7명 서브에이전트 역할 분담)

---

## 4. 자체 패턴: release v2.1

**핵심**: Zero-Question 자율 실행 + 3-Tier 자가 성장.

### Phase 흐름 패턴
```
Phase 0 (Load) → Phase 1 (Triage) → Phase 2 (Absorption)
→ Phase 3 (Pipeline+Fleet) → Phase 4 (Execute)
→ Phase 5 (QC) → Phase 6 (Self-Improve) → Phase 7 (Report)
```

### 위임 등급 패턴
| 등급 | 기준 | 에이전트 |
|------|------|---------|
| Direct | 단순, 명확 | 없음 (직접 실행) |
| Light | 중간 복잡도 | haiku/sonnet |
| Full | 높은 복잡도 | opus |

### 자가 성장 패턴 (3-Tier)
| Tier | 대상 | 신호 | 필터 | 수정 대상 |
|------|------|------|------|----------|
| 1 Operational | 프로세스 규칙 | 6종 | 3-gate | meta-rules, references |
| 2 Skill Mastery | 스킬 지식 | 4종 | 2-gate | skill-intelligence |
| 3 User Adaptation | 사용자 적응 | 3종 | 1-gate | operational-rules, user-profile |

### SOT 구조 패턴
```
SOT/
├── meta-rules.md          # Tier 1: 누적 규칙
├── performance.md          # 스킬 성과표
├── sessions/              # 세션별 로그
├── operational-rules.md    # Tier 3: 사용자 지시
├── user-profile.md         # Tier 3: 사용자 프로필
├── skill-intelligence.md   # Tier 2: 스킬 심층 지식
├── evolution-signals/      # 스킬 진화 신호
├── project-absorptions/    # 프로젝트 흡수 문서
└── self-improvement-backups/  # 자가 수정 백업
```

---

## 5. 자체 패턴: night-lab v3.5

**핵심**: 루프 기반 목표 지향 연구 + 도메인 권위 축적.

### Phase 흐름 패턴
```
Phase A (설계) → [Loop: Phase B (연구 라운드) → Phase C (기록)
→ Phase D (평가) → Phase E (판정)] → Phase F (루프 종료)
→ Phase G (Retrospective + Self-Growth)
```

### 에이전트 구성 패턴
| 역할 | 동적 고용 조건 |
|------|---------------|
| 탐색원 | 항상 |
| 심층연구원 | 루프 2+ |
| 분석관 | 데이터 종합 필요 시 |
| 검증원 | 주장 검증 필요 시 |
| 비평가 | 품질 임계 미달 시 |
| 전문가 | 도메인 전문성 필요 시 |
| 보고관 | 최종 보고 시 |

### Authority Growth 패턴
```
SOT/research-intelligence/
├── authority/
│   ├── authority-index.md
│   ├── domain-expertise.md
│   ├── cross-domain-network.md
│   ├── frameworks-library.md
│   └── prediction-log.md
├── growth-rules.md
├── methodology-insights.md
└── strategy-matrix.md
```

---

## 6. 설계 원칙 (패턴 횡단)

1. **Phase는 단일 책임**: 하나의 Phase가 하나의 목적만 수행
2. **SOT는 Phase에 종속**: 각 SOT 파일의 갱신 주체(Phase)가 명확해야 함
3. **자가 성장은 분리 Phase**: 실행 Phase와 성장 Phase를 분리 (간섭 방지)
4. **백업은 수정 전 필수**: 자가 수정 전 반드시 원본 백업
5. **Phase 스킵 조건 명시**: 스킵 가능한 Phase는 조건을 SKILL.md에 명문화
6. **입출력 계약**: Phase 간 데이터 전달은 파일/변수로 명시적 계약
