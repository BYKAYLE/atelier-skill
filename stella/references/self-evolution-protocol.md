# Layer 5: Self-Evolution — 7단계 상세 절차

> SKILL.md §Adaptive Memory System Layer 5에서 분리 (260610, Opus 4.8 경량화).
> 자율 경계 테이블(실행 판단)은 SKILL.md 본문에 유지 — 이 파일은 절차만 담는다.

## Step 1: 진단 (selfassess 실행)
```
Bash: python3 scripts/stella_memory.py selfassess
```
교정 패턴, 메모리 상태, 플레이북 건강, 세션 통계 확인.

## Step 2: 병목 식별
selfassess 결과 + 최근 daily logs + corrections.md를 읽고 판단:
- **반복 실패 패턴**: 같은 유형의 교정이 2회 이상 → 해당 Execution Pattern이 부족
- **누락된 스킬 영역**: 릴리스에게 위임 시 적합한 스킬이 없었던 경험 → 새 스킬 필요
- **비효율 워크플로우**: 같은 종류의 태스크에 매번 시행착오 → playbook 부재
- **아키텍처 한계**: SKILL.md 구조 자체의 문제 (섹션 누락, 충돌, 모호함)

## Step 3: 개선안 작성
`SOT/evolution-log.md`에 기록:
```
## 진화 #{N} — {날짜}

### 진단
- {발견한 문제 요약}

### 개선안
1. {구체적 변경 내용} — 대상: {파일 경로} — 유형: {패턴수정/스킬추가/구조변경}
2. ...

### 예상 효과
- {이 변경으로 뭐가 나아지는지}

### 위험
- {이 변경이 깨뜨릴 수 있는 것}

### 승인: {대표님확인필요 / 자율실행가능}
```

## Step 4: 실행 판단
SKILL.md 본문의 **자율 경계 테이블**을 따른다 (자율 = playbook + 메모리 정리만,
그 외 코드/패턴/구조 변경은 대표님 확인 필수).

## Step 5: 자율 실행 가능한 것은 즉시 실행
에이전트가 직접:
1. 해당 파일을 Read
2. 변경 내용을 Write/Edit
3. 변경 결과를 검증 (변경 전후 diff 확인)
4. `SOT/evolution-log.md`에 실행 결과 기록

## Step 6: 대표님 확인 필요한 것은 큐에 적재
`SOT/review-queue.md`에:
```
- [ ] 진화 #{N}: {개선안 요약} — 근거: {진단 결과} — 위험: {있으면}
```
대표님 복귀 시 Morning Report에 포함.

## Step 7: 메모리 감사 (기존 L5 기능 포함)
1. 오래된 daily/ 보존 상태 기록 (30일 이상 → `preservation-index.md`에 인덱싱, 원본 유지)
2. playbooks/ 중 6개월 미사용 → 보존/아카이브 필요성만 판단
3. STELLA.md/USER.md 중복/오래된 항목은 삭제하지 않고 새 정정 항목으로 보강

---

## 진화 범위 예시

```
진단: "배포 시 Synology SSH 포트 문제로 3세션 연속 실패"
→ Pattern 8 (Deploy)에 "Synology 비표준 포트 자동 감지 단계" 추가

진단: "PRD 없이 구현 위임해서 범위 이탈 2회"
→ Protocol.1 위임 템플릿에 "PRD 존재 확인" 필수 체크 추가

진단: "Edison 리서치 파이프라인에서 NotebookLM 연동 실패 반복"
→ 새 playbook "edison-notebooklm-troubleshoot.md" 자동 생성

진단: "보안 감사 요청 시 매번 security-router vs security-audit-final 혼동"
→ Skill Utilization 라우팅 기준에 구체적 판단 조건 추가
```
