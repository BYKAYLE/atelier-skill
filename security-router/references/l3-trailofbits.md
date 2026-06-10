---
name: trailofbits-security
version: "1.0.0"
description: |
  Use when conducting deep security audits with static analysis (Semgrep), unsafe defaults detection, and supply chain risk assessment.
  Invoked by security-router when Layer 1+2 analysis is insufficient.
  Source: github.com/trailofbits/skills (CC-BY-SA-4.0 License)
---

# Trail of Bits Deep Security Analysis

Layer 1(owasp-security)과 Layer 2(sentry-security-review)로 부족한 경우에만 사용한다.
전문 보안 감사 수준의 심층 분석을 수행한다.

---

## 사용 조건 (security-router가 판단)

이 스킬은 다음 조건에 해당할 때만 호출된다:

| 조건 | 예시 |
|------|------|
| 인증/인가 시스템 직접 구현 | JWT 토큰 발급, OAuth 플로우, RBAC 시스템 |
| 암호화 직접 구현 | 키 생성, 암호화/복호화 로직, 서명 검증 |
| 외부 입력 처리가 복잡한 경우 | 파일 업로드 + 처리, API 게이트웨이, 웹훅 수신 |
| 공급망 위험 평가 필요 | 새 의존성 대량 추가, 서드파티 라이브러리 도입 |
| 보안 감사 명시적 요청 | "보안 감사해줘", "취약점 분석해줘" |

---

## 기능 1: 정적 분석 (Semgrep 기반)

### 사용 조건
시스템에 Semgrep이 설치되어 있어야 한다: `pip install semgrep`

### 실행 프로세스
1. 대상 코드의 언어 자동 탐지
2. 적절한 룰셋 선택 (OWASP, CWE, Trail of Bits)
3. Semgrep 스캔 실행 (`--metrics=off` 텔레메트리 차단)
4. 결과 분류: 진양성 / 위양성 판별
5. 보고서 생성

### 실행 명령어
```bash
# 기본 스캔
semgrep scan --config auto --metrics=off --output results.json --json .

# OWASP 룰셋 스캔
semgrep scan --config "p/owasp-top-ten" --metrics=off .

# CWE 룰셋 스캔
semgrep scan --config "p/cwe-top-25" --metrics=off .
```

### 결과 분석 원칙
- 결과 0건이면 반드시 원인 조사 (룰셋 미스매치, 언어 미지원 가능성)
- 진양성/위양성을 코드 문맥을 분석하여 분류
- 진양성에 대해 수정 권고 제공

---

## 기능 2: 안전하지 않은 기본값 탐지

### 탐지 대상
| 카테고리 | 패턴 | 위험도 |
|----------|------|--------|
| 하드코딩된 시크릿 | `password = "admin123"`, `api_key = "sk-..."` | Critical |
| 기본 자격증명 | `username: admin, password: admin` | Critical |
| 약한 암호화 | `DES`, `MD5` for passwords, `ECB` mode | High |
| 과도한 권한 | `chmod 777`, `*` in CORS, `0.0.0.0` 바인딩 | High |
| 누락된 보안 설정 | `DEBUG=True` in production, 누락된 HTTPS 리다이렉트 | Medium |
| Fail-open 패턴 | 에러 시 접근 허용, 검증 실패 시 통과 | High |

### 핵심 원칙
> "적절한 설정 없이 크래시하는 앱은 안전하고, 안전하지 않은 기본값으로 실행되는 앱은 취약하다."

### 검사 방법
```bash
# 하드코딩된 시크릿 검색
grep -rn "password\s*=\s*[\"']" --include="*.py" --include="*.js" --include="*.ts" .
grep -rn "api_key\s*=\s*[\"']" --include="*.py" --include="*.js" --include="*.ts" .
grep -rn "secret\s*=\s*[\"']" --include="*.py" --include="*.js" --include="*.ts" .

# 디버그 모드 검색
grep -rn "DEBUG\s*=\s*True" --include="*.py" .
grep -rn "NODE_ENV.*development" --include="*.js" --include="*.ts" .
```

---

## 기능 3: 공급망 위험 평가

### 평가 항목
| 항목 | 확인 방법 | 위험 신호 |
|------|-----------|-----------|
| 인기도 | GitHub stars, npm downloads | 매우 낮은 다운로드 수 |
| 메인테이너 | 컨트리뷰터 수, 활동 이력 | 1인 유지보수, 장기 미활동 |
| CVE 이력 | `npm audit`, `pip audit` | 미패치 CVE 존재 |
| 유지보수 | 최근 커밋, 릴리스 주기 | 1년 이상 업데이트 없음 |
| 타이포스쿼팅 | 패키지명 유사성 검사 | 유사 이름의 악성 패키지 |

### 실행 명령어
```bash
# Python
pip audit
pip list --outdated

# Node.js
npm audit
npm outdated

# 의존성 트리 확인
pip install pipdeptree && pipdeptree
npm ls --all
```

---

## 출력 형식

```markdown
## Deep Security Audit: [프로젝트/컴포넌트]

### Static Analysis (Semgrep)
- **스캔 대상**: X개 파일 / Y개 언어
- **룰셋**: [사용된 룰셋]
- **결과**: Z개 발견 (진양성 A개 / 위양성 B개)

### Insecure Defaults
- **검사 항목**: X개
- **발견**: Y개

### Supply Chain
- **의존성 수**: X개 (직접) / Y개 (간접)
- **알려진 취약점**: Z개
- **위험 의존성**: [목록]

### 권고사항
1. [우선순위순 수정 사항]
```
