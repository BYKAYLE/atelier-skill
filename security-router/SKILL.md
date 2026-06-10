---
name: security-router
version: "1.0.0"
description: |
  Use when performing security checks by automatically selecting the right combination of security skills.
  Handles autonomous-dev QC security stage and direct security review requests.
  Triggers: "보안 검사", "보안 리뷰", "취약점 검사", "security check", "security review",
  "코드 보안", "보안 감사", "의존성 검사", "supply chain check",
  "최종 보안 테스트", "출시 전 보안 점검", "보안 감사 보고서", "final security audit"
---

# Security Router — 보안 검사 자동 라우터

사용자는 "보안 검사해줘"만 말한다. 어떤 스킬을 어떤 순서로 쓸지는 이 라우터가 결정한다.

---

## 보유 보안 스킬 (3개 레이어)

| Layer | 스킬 | 역할 | 경로 |
|-------|------|------|------|
| **L1** | owasp-security | 보안 교과서 — 안전한 패턴 유도 | `references/l1-owasp.md` |
| **L2** | sentry-security-review | 보안 심판 — HIGH 신뢰도 취약점 탐지 | `references/l2-sentry.md` |
| **L3** | trailofbits-security | 보안 감사관 — Semgrep/공급망/기본값 심층 분석 | `references/l3-trailofbits.md` |

---

## 판단 로직 (Decision Tree)

### Step 1: 상황 분류

```
사용자 요청 또는 코드 변경 감지
        ↓
┌─ A. 코드 작성 중 (새 기능 개발, 기존 코드 수정)
│       → 기본: L1만 적용 (안전한 패턴으로 코드 작성)
│
├─ B. 코드 리뷰 요청 ("이 코드 보안 괜찮아?", "보안 리뷰해줘")
│       → 기본: L1 + L2 적용
│
├─ C. 심층 보안 감사 요청 ("보안 감사", "취약점 전체 분석")
│       → 전체: L1 + L2 + L3 적용
│
├─ D. 최종 보안 감사 ("최종 보안 테스트", "출시 전 보안 점검", "보안 감사 보고서")
│       → 모드 D: 기능검증 + 3-Agent 코드리뷰 + 침투테스트 + PDF 보고서
│       → 플레이북: SOT/playbooks/final-security-audit.md
│
└─ E. 특정 상황 감지 (아래 테이블 참조)
        → 조건에 따라 L3 추가 여부 결정
```

### Step 2: L3 (trailofbits) 추가 호출 조건

다음 중 하나라도 해당하면 **L1 + L2 + L3** 모두 실행:

| 조건 | 감지 방법 | 이유 |
|------|-----------|------|
| **인증/인가 직접 구현** | JWT, OAuth, 세션, RBAC 관련 코드 작성/수정 | 인증은 틀리면 전체 시스템이 뚫림 |
| **암호화 직접 구현** | hashlib, crypto, 키 생성, 서명 로직 | 암호화 오류는 패턴 매칭으로 못 잡음 |
| **파일 업로드/처리** | multipart, file upload, 이미지 처리 | 경로 순회, RCE 위험 |
| **외부 API 호출 + 사용자 입력** | requests/fetch + user input으로 URL 구성 | SSRF 위험 |
| **역직렬화** | pickle, yaml.load, JSON.parse + eval | RCE 위험 |
| **의존성 대량 추가** | package.json/requirements.txt에 5개 이상 새 패키지 | 공급망 위험 |
| **인프라 설정 변경** | Dockerfile, K8s, Terraform, CI/CD 파이프라인 | 설정 오류 = 인프라 노출 |
| **사용자 명시 요청** | "깊이 분석", "보안 감사", "전체 스캔" | 사용자 의지 존중 |

다음 경우에는 **L1 + L2만** 실행 (L3 불필요):

| 상황 | 이유 |
|------|------|
| UI 컴포넌트 변경 | 프론트엔드 프레임워크가 자동 이스케이핑 |
| CSS/스타일 변경 | 보안 영향 없음 |
| 테스트 코드 작성 | 프로덕션 코드 아님 |
| 문서/주석 수정 | 보안 영향 없음 |
| ORM 사용 CRUD | 프레임워크가 SQL 인젝션 방어 |
| 환경변수로 설정 관리 | 이미 안전한 패턴 |

---

## 실행 프로세스

### 모드 A: 코드 작성 중 자동 적용 (L1)

```
코드 작성 시작
    ↓
L1(owasp-security) SKILL.md 참조
    ↓
해당 언어의 안전한 패턴으로 코드 생성
    ↓
완료
```

**이 모드는 명시적 호출 불필요.** owasp-security 스킬이 설치되어 있으면
Claude가 코드 작성 시 자동으로 안전한 패턴을 적용한다.

### 모드 B: 코드 리뷰 (L1 + L2)

```
사용자: "이 코드 보안 괜찮아?" 또는 코드 리뷰 요청
    ↓
L1 기준으로 체크리스트 확인
    ↓
L2(sentry) 프로세스 실행:
  1. 코드 유형 감지 → 관련 참조 파일 로드
  2. 데이터 흐름 추적
  3. 프레임워크 보호 확인
  4. HIGH 신뢰도 취약점만 보고
    ↓
보고서 출력 (VULN-001 형식)
```

### 모드 C: 심층 보안 감사 (L1 + L2 + L3)

```
심층 감사 조건 감지 또는 사용자 명시 요청
    ↓
L1 + L2 실행 (모드 B와 동일)
    ↓
L3(trailofbits) 추가 실행:
  1. Semgrep 정적 분석 (설치되어 있는 경우)
  2. 안전하지 않은 기본값 탐지
  3. 공급망 위험 평가 (의존성 변경 시)
    ↓
통합 보고서 출력
```

### 모드 D: 최종 보안 감사 (Final Security Audit)

**서비스 개발 완료 후 출시/배포 전 실행하는 종합 보안 감사.**
L1+L2+L3 코드 리뷰 + 실제 침투 테스트 + 기능 검증을 모두 포함하는 최상위 모드.

플레이북: `SOT/playbooks/final-security-audit.md`

```
서비스 완성 → "최종 보안 테스트" 또는 "보안 감사" 요청
    ↓
Phase 1: 기능 검증 (typecheck, lint, test, build)
    ↓ 전체 PASS만 통과
Phase 2: 3-Agent 병렬 코드 보안 리뷰
  - Agent A: 백엔드 (OWASP Top 10, 인젝션, 시크릿 노출)
  - Agent B: 프론트엔드 (XSS, CSP, API 노출)
  - Agent C: 의존성 + 설정 (audit, CVE, 키 관리)
    ↓
Phase 3: 침투 테스트 시뮬레이션 (10대 공격 시나리오)
  - 프로세스 스니핑, API 탈취, 설정 파일 접근 등
  - 발견 취약점은 실제 exploit 실증
    ↓
Phase 4: 취약점 보고서 (CRITICAL~LOW + PDF)
```

---

## 통합 보고서 형식

```markdown
# 보안 검사 보고서

## 검사 레벨
- [x] L1: OWASP 기준 패턴 검사
- [x] L2: Sentry 신뢰도 기반 취약점 분석
- [x/빈칸] L3: Trail of Bits 심층 감사

## L2 결과: 취약점 (HIGH 신뢰도)
[sentry-security-review 출력 형식]

## L3 결과: 심층 분석 (해당 시)
### 정적 분석
[Semgrep 결과]

### 안전하지 않은 기본값
[탐지 결과]

### 공급망 위험
[의존성 분석 결과]

## 종합 판정
- 위험도: Critical / High / Medium / Low / Clean
- 즉시 수정 필요: [항목]
- 권고 사항: [항목]
```

---

## autonomous-dev 연동

autonomous-dev 스킬의 QC 단계에서 이 라우터를 호출한다:

1. **Phase 3 (QC)** 에서 security-router 호출
2. 라우터가 변경된 코드의 성격을 분석
3. 적절한 레이어 조합을 자동 결정
4. 보안 검사 실행 + 결과 보고
5. Critical/High 발견 시 → QC 실패 → 수정 후 재검사

---

## 단독 사용

autonomous-dev 없이도 사용 가능:

```
사용자: "보안 검사해줘"         → 모드 B (L1+L2)
사용자: "보안 감사해줘"         → 모드 C (L1+L2+L3)
사용자: "의존성 검사해줘"       → L3 공급망 분석만 실행
사용자: "이 코드 안전해?"       → 모드 B (L1+L2)
사용자: "최종 보안 테스트"      → 모드 D (기능검증+리뷰+침투+보고서)
사용자: "출시 전 보안 점검"     → 모드 D
사용자: "보안 감사 보고서"      → 모드 D
```
