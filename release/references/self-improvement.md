# Self-Improvement Protocol — release v4.0.0

## 정의

자가성장이란: 프로젝트를 진행하면서 발생한 문제와 이슈를 기록하고,
다음에 유사한 상황에서 그 문제가 자연스럽게 발생하지 않게 진행하는 것.

## North Star

**Post-Completion 요청 수 = 0**

| 단계 | 상태 | 현재 |
|------|------|------|
| Lv.1 | 매번 지적 3+건 | ← 여기 |
| Lv.2 | 가끔 보완 1~2건 | |
| Lv.3 | 추가 지시 없이 승인 | |
| Lv.4 | 예상 초과 선제 처리 | |

---

## v3.0 실패 원인

v3.0은 플레이북 시스템 자체는 좋았으나 **기록 실행이 안 됐다.**

| 문제 | 원인 |
|------|------|
| Phase 6 스킵 | Phase 6이 세션 끝에 위치 → 컨텍스트 소진 시 도달 불가 |
| 강제 메커니즘 부재 | guard.py가 QC만 검증, Phase 6 실행 여부 미검증 |
| 기록이 "기억"에 의존 | "세션 끝에 기록하자"를 기억하는 건 v2.0 규칙 시스템과 같은 실패 |
| Express 면제 과다 | Express에서도 교정 발생하는데 등급 면제로 누락 |
| Failure Log 미동기화 | user-model.md 교정 기록 ↔ performance.md Failure Log 분리 |

---

## v4.0 핵심 변경: 매 Phase 기록 (Incremental Recording)

**원칙: 기록은 세션 끝이 아니라 각 Phase 완료 즉시 수행한다.**

Phase 6에서 한번에 회고하는 것이 아니라, 각 Phase가 끝날 때 사실을 바로 기록한다.
이러면 Phase 6에 도달 못해도 사실 기록의 80%+는 이미 저장되어 있다.

### 세션 파일 생명주기

```
Phase 0  → 세션 파일 생성 (CREATE)
Phase 1  → append: 등급, intent
Phase 2  → append: 흡수 요약 (1줄)
Phase 4  → append: 스킬 호출, 에러, 교정 (발생 즉시)
Phase 5  → append: QC 결과
Phase 6  → append: 배운 것 + 플레이북 갱신 목록
Phase 7  → append: Post-Completion 수, 최종 Level
```

### Phase별 기록 상세

#### Phase 0: 세션 파일 생성

세션 시작 시 즉시 `SOT/sessions/session-{YYYY-MM-DD}-{project}.md` 생성:

```markdown
# {YYYY-MM-DD} — {프로젝트명}
- 시작: {시각}
- 등급: (Phase 1에서 기록)
- 스킬: (Phase 4에서 기록)
- 결과: (Phase 7에서 기록)

## 타임라인
```

**이 파일이 존재해야 guard.py Stop hook을 통과한다.** (Express 포함)

#### Phase 1: 등급 · Intent 기록

Phase 1 완료 즉시 세션 파일에 append:
```markdown
- 등급: Standard
- Intent: development-existing
```

#### Phase 2: 흡수 요약

```markdown
- 흡수: {프로젝트명} — {핵심 파악 1줄}
```

#### Phase 4: 실시간 이벤트 기록

Phase 4 실행 중 아래 이벤트 발생 시 즉시 세션 파일 타임라인에 append:

| 이벤트 | 기록 형식 |
|--------|----------|
| 스킬 호출 | `[HH:MM] SKILL: {스킬명} — {요약}` |
| 에러 발생 | `[HH:MM] ERROR: {에러 요약} → {해결}` |
| **교정 발생** | `[HH:MM] CORRECTION: "{사용자 원문}" → {반영 내용}` |
| 플레이북 조회 | `[HH:MM] PLAYBOOK: {플레이북명} 조회` |
| 자율 판단 | `[HH:MM] DECISION: {판단 내용} — 근거: {근거}` |

**교정 발생 시 3중 동시 갱신:**
1. 세션 파일 타임라인에 CORRECTION 기록
2. `SOT/user-model.md` 교정 기록 테이블에 추가
3. `SOT/performance.md` Failure Log에 추가

#### Phase 5: QC 결과

```markdown
## QC
- 빌드: PASS/FAIL
- 테스트: PASS/FAIL/SKIP
- 배포: PASS/FAIL/SKIP
```

#### Phase 6: 배운 것 + 플레이북 갱신 (경량화)

v4.0에서 Phase 6의 역할은 **이미 기록된 사실 위에 통찰 1줄을 추가하는 것**뿐이다.

```markdown
## 배운 것
- {이번 세션에서 배운 것 1~2줄}

## 플레이북 갱신
- {갱신한 플레이북명}: {변경 요약}
- (없으면 "갱신 없음")
```

**Phase 6에서 하는 것:**
1. 세션 파일에 "배운 것" 추가 (1~2줄)
2. 관련 플레이북 갱신/생성 (경험 기록, 체크리스트 보완)
3. skill-playbooks.md 갱신 (스킬 관련 새 인사이트 있으면)

**Phase 6에서 더 이상 하지 않는 것** (이미 실시간으로 완료):
- ~~세션 회고~~ → 타임라인에 이미 기록됨
- ~~user-model.md 갱신~~ → Phase 4에서 교정 즉시 갱신됨
- ~~performance.md 갱신~~ → Phase 4에서 Failure Log 즉시 갱신됨
- ~~세션 파일 생성~~ → Phase 0에서 이미 생성됨

#### Phase 7: 최종 기록

```markdown
## 최종
- 결과: 성공/실패/부분
- Post-Completion: {N}건
- Level: Lv.{N}
```

performance.md의 Performance Table + total_sessions 갱신.

---

## Express 등급 처리

v3.0: Express는 Phase 6 완전 면제 → 교정 누락
v4.0: **Express도 세션 파일 생성 + 교정 기록은 필수**

Express 세션 파일 (최소):
```markdown
# {YYYY-MM-DD} — {요청 요약}
- 등급: Express
- 스킬: {스킬명}
- 결과: 성공
- Post-Completion: 0건
```

Express에서 교정 발생 시 → 3중 동시 갱신 동일하게 적용.
Express에서 플레이북 갱신은 선택 (의미 있는 경험이면 갱신).

---

## 플레이북 시스템 (v3.0에서 유지)

### 구조

플레이북 = 상황별 경험 기반 절차서
- 검증된 절차 / 알려진 문제 / 사전 체크리스트 / 경험 기록

### Phase 4: 실행 중 조회

매 주요 액션 전:
1. 도메인 파악 → `_index.md`에서 매칭
2. 매칭 시 → Read로 로드 → 절차 따라 실행 → 세션 파일에 PLAYBOOK 기록
3. 미매칭 시 → 정상 실행

"불가능" 판단 시 → `resource-verification.md` 반드시 조회

### 에이전트 위임 시

위임 프롬프트에 플레이북의 절차/체크리스트 포함.

### 교정 실시간 캡처

교정 발생 시 3중 동시 갱신 (세션 파일 + user-model.md + Failure Log).
관련 플레이북도 즉시 갱신.

---

## Phase 6.5: 납품 전 검증 (v3.0에서 유지)

Delivery Report 작성 직전:
1. user-model.md 대조 (형식, 완결성, 품질)
2. 플레이북 체크리스트 최종 확인
3. 서비스 배포 시: 런타임 테스트, 보안 검증, 인프라 확인

---

## guard.py Stop Hook 강화

### 검증 로직

```python
# 세션 종료 시 guard.py가 확인:
# 1. 오늘 날짜의 세션 로그 파일이 SOT/sessions/에 존재하는가?
# 2. 없으면 → 첫 번째 stop을 block ("세션 로그를 작성하세요")
# 3. 있으면 → 기존 QC 검증 로직 실행
```

이로써 Phase 0에서 세션 파일을 생성하지 않으면 세션 종료 자체가 불가.
Phase 0 생성 → 이후 각 Phase에서 자연스럽게 append → 기록 보장.

---

## 안전장치

1. **백업**: 플레이북 대규모 수정 전 `SOT/playbook-backups/`에 원본 복사
2. **SKILL.md 수동 전용**: 자가 수정 대상 아님
3. **경험 기록은 사실만**: 추측/해석 금지
4. **세션 파일은 삭제 금지**: archive로만 이동

---

## 스킬 진화 트리거

- **자동**: 위임 프롬프트 최적화 (스킬 실패 시)
- **권고**: 동일 스킬 실패 3회+ → skill-evolve 권고
- **강제**: pass_rate < 20% (10+ calls) → 자동 skill-evolve

---

## 갱신 이력

| 날짜 | 변경 | 근거 |
|------|------|------|
| 260319 | v2.0.0 초기 생성 | 3-Tier 자가성장 아키텍처 |
| 260319 | v2.1.0 Tier 3 실시간 + North Star + Step 0/5 | 사용자 피드백 |
| 260320 | v3.0.0 전면 재설계: 규칙 → 플레이북 시스템 | "규칙이 행동을 바꾸지 못한다" |
| 260327 | v4.0.0 매 Phase 기록: Phase 6 일괄→각 Phase 점진 | Phase 6 스킵으로 세션 로그 5일간 미작성 — 구조적 해결 |
