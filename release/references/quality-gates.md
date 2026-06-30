# Quality Gates — release

## Tier 1: 기계적 게이트 (자동 실행)

위임 결과를 받은 후 자동으로 실행한다. exit code 기반 판단.

### 게이트 목록

| Gate | Stack | Command | Pass |
|------|-------|---------|------|
| G1 Build | Node (npm) | `npm run build` | exit 0 |
| G1 Build | Node (pnpm) | `pnpm build` | exit 0 |
| G1 Build | Rust | `cargo build` | exit 0 |
| G1 Build | Go | `go build ./...` | exit 0 |
| G1 Build | Python | `python -c "import compileall; exit(0 if compileall.compile_dir('.', quiet=1) else 1)"` | exit 0 |
| G1 Build | Docker | `docker compose build` | exit 0 |
| G2 Test | Node (npm) | `npm test` | exit 0 |
| G2 Test | Node (pnpm) | `pnpm test` | exit 0 |
| G2 Test | Rust | `cargo test` | exit 0 |
| G2 Test | Go | `go test ./...` | exit 0 |
| G2 Test | Python | `pytest` | exit 0 |
| G3 Type | TypeScript (npm) | `npx tsc --noEmit` | 0 errors |
| G3 Type | TypeScript (pnpm) | `pnpm tsc --noEmit` | 0 errors |
| G3 Type | Python | `mypy .` | 0 errors |
| G3 Type | Rust | `cargo check` | exit 0 |
| G4 Lint | Node (npm) | `npx eslint .` or `npx biome check .` | 0 errors |
| G4 Lint | Node (pnpm) | `pnpm eslint .` or `pnpm biome check .` | 0 errors |
| G4 Lint | Python | `ruff check .` | 0 errors |
| G4 Lint | Go | `golangci-lint run ./...` (설치 시) | 0 errors |
| G4 Lint | Rust | `cargo clippy` | 0 warnings |

### 스택 감지

프로젝트 루트에서 아래 파일로 스택을 감지한다:
- `package.json` → Node (`pnpm-lock.yaml` 있으면 pnpm, 아니면 npm) (+ `tsconfig.json`이면 TypeScript, + `biome.json`이면 biome 린터)
- `Cargo.toml` → Rust
- `go.mod` → Go
- `pyproject.toml` 또는 `requirements.txt` → Python
- `Dockerfile` 또는 `docker-compose.yml` → Docker

린터 우선순위: `biome.json` 있으면 biome, `.eslintrc*` 있으면 eslint. 둘 다 있으면 biome 우선.

해당 없는 게이트는 N/A로 건너뛴다.

### 실행 순서

G1 → G2 → G3 → G4 순서. 앞 게이트 FAIL 시 즉시 중단 (뒤 게이트 실행 불필요).

## Tier 2: 작업별 게이트 (오케스트레이터 정의)

오케스트레이터가 위임 시 성공 기준으로 정의한 항목. Agent 결과 보고서에서 확인.

예시:
- "파일 {path} 존재하고 함수 {name} export"
- "API {endpoint} 호출 시 200 응답"
- "보안 보고서에 CRITICAL 0건"
- "PPT 파일 생성되고 validate.py PASS"
- "PRD 문서 4개 섹션 모두 포함"

## Tier 2.5: 비개발 산출물 구조 검증

Tier 1을 적용할 수 없는 비개발 스킬의 산출물을 기계적으로 검증한다.
Agent 보고서의 주관적 판단(Tier 2)에 추가하여, 아래 객관적 검증을 수행.

### Phase 진입 게이트 (Pipeline/Standard 모드)

**Phase 4 진입 전 필수 검증:**
- Pipeline/Standard 모드에서 Phase 2(Absorption) 완료 후, `SOT/project-absorptions/absorption-*.md` 파일이 **반드시 1개 이상 존재**해야 Phase 4 진입 가능
- 미생성 시: Phase 2로 돌아가 absorption 파일 생성 후 재진입
- Express 모드는 Phase 2 자체를 스킵하므로 이 게이트 미적용

### 검증 항목

| Check | 방법 | Pass 조건 |
|-------|------|----------|
| 파일 존재 | `test -f {path}` | exit 0 |
| 파일 비어있지 않음 | `test -s {path}` | exit 0 (size > 0) |
| 최소 크기 | `wc -c < {path}` | 문서 ≥ 500B, PPT ≥ 10KB |
| 필수 섹션 (MD/텍스트) | `grep -c "{section_header}" {path}` | 정의된 섹션 수 ≥ 기준 |

### 스킬별 기준

| Skill | 산출물 | 필수 검증 |
|-------|--------|----------|
| show-me-the-prd | PRD 4종 md | 4개 파일 존재 + 각 ≥ 500B |
| bykayle-slide-team | .pen/.pptx | 파일 존재 + ≥ 10KB |
| notebooklm | 리서치 보고서 md | 파일 존재 + ≥ 1KB |
| private-rd-orchestrator | 최종 보고서 md | 파일 존재 + ≥ 2KB |
| private-company-data-skill | records/ 파일 | 파일 존재 + JSON/MD 유효 |
| it-field-support | (산출물 없음) | Tier 2만 적용 |
| kkirikkiri | (다양) | 파일 존재만 |

오케스트레이터가 Bash로 직접 실행한다. 모두 PASS 시 다음 단계 진행.

## 비개발 스킬

bykayle-slide-team, show-me-the-prd, it-field-support, k-dense-ai, kkirikkiri 등
코드를 생산하지 않는 스킬은 Tier 1을 건너뛰고 **Tier 2 + Tier 2.5**를 적용한다.

## Tier 3: 프로덕션 필수 게이트 (배포 서비스 전용)

**트리거**: private-deployment-skill이 포함된 파이프라인에서 배포 전 반드시 실행.
배포가 없는 개발 작업에는 적용하지 않음.

### 3A. 런타임 보안 smoke (Probe)

코드 레벨 보안(security-router)과 별개로, 실제 동작 중인 서비스에 대한 저부작용 런타임 검수.
기본값은 Probe이며, 실제 침투/공격 실행/광범위 스캔은 `pentest-router`로 분리하고 사용자 명시 승인 + scope 기록 전에는 실행하지 않는다.

| Check | 방법 | Pass 조건 |
|-------|------|----------|
| HTTP 헤더 보안 | Probe `securityHeaders` | CSP/HSTS/프레임/콘텐츠타입/권한/리퍼러 정책 기준 통과 |
| 쿠키 보안 | Probe `cookieSecurity` | Secure/HttpOnly/SameSite 기준 통과 |
| Mixed content | Probe `noMixedContent` | HTTPS 표면에서 혼합 콘텐츠 없음 |
| 민감 URL 파라미터 | Probe `noSensitiveUrlParams` | token/key/secret/session 등 URL 노출 없음 |
| 런타임 리포트 | `summary.json` + exit code | exit 0 또는 실패 assertion을 수정 후 재검증 |

### 3B. 인프라 보안

| Check | 방법 | Pass 조건 |
|-------|------|----------|
| SSL/TLS 인증서 | `curl -vI https://{domain}` | 유효한 인증서 |
| 불필요 포트 노출 | NAS에서 외부 접근 가능한 포트 확인 | 서비스 포트만 오픈 |
| .env 파일 접근 | `curl https://{domain}/.env` 시도 | 404 또는 403 |
| API 키 git 노출 | `grep -r "sk-" --include="*.py" --include="*.ts"` | 하드코딩 0건 |
| Docker 이미지 보안 | non-root 사용자, 불필요 패키지 제거 | Dockerfile 검증 |
| 백업 설정 | DB 자동 백업 스크립트 존재 + 최근 백업 확인 | 24시간 이내 백업 |

### 3C. 법적 컴플라이언스

서비스 특성에 따라 필수 항목이 달라진다. 흡수 문서에서 해당 항목을 판별.

| Check | 해당 조건 | 필수 산출물 |
|-------|----------|-----------|
| 개인정보 처리방침 | 사용자 데이터 수집 시 | 웹페이지 또는 문서 |
| 이용약관 | 외부 사용자 접속 시 | 웹페이지 또는 문서 |
| 음성/녹음 동의 | STT/녹음 기능 시 | 동의 UI + 법적 고지 |
| 쿠키 동의 | 쿠키 사용 시 | 배너 또는 모달 |
| 데이터 보관/파기 | 개인정보 수집 시 | 보관 기간 명시 + 파기 절차 |
| 제3자 API 데이터 전송 | OpenAI/Anthropic 등 | 데이터 처리 위탁 고지 |

### 실행 방식

- 3A: Probe `run_probe.sh <plan-or-url>` 실행. Release는 `report.md`를 재해석하지 않고 exit code + `summary.json` pass/fail 카운트만 소비
- 3B: 오케스트레이터 직접 실행 (SSH + curl)
- 3C: 오케스트레이터가 체크리스트 대조 → 미비 항목은 코드/문서 생성
- FAIL 항목 → 수정 후 재검증. 모두 PASS 후에만 배포 완료 선언

---

## Level 2: Project-Level QC (v2.0)

파이프라인 전체 완료 후, 프로젝트 레벨에서 최종 검증한다.
release가 사람 대신 모든 판단을 수행. 상세: `references/autonomous-qc.md`

### 2A. 목표 달성 검증
- 흡수 문서(`absorption-{timestamp}.md`)의 Quality Criteria 하나씩 대조
- PASS / PARTIAL (허용 가능한 편차) / FAIL (해당 스텝 재실행)

### 2B. 교차 정합성 검증
- PRD 기능 ↔ 구현 코드 대조
- UI 가이드 ↔ 실제 UI 대조
- 보안 감사 결과 ↔ 수정 확인
- 데이터 모델 ↔ DB 스키마 대조

### 2C. 사용자 기대 모델링
- 세션 히스토리에서 추출한 사용자 선호 검증
- 토큰 효율 (예산 대비 과다 여부)
- 완성도 수준 (흡수 문서 scale에 부합하는지)
