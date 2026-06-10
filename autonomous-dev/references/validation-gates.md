# 스택별 검증 게이트 매핑 (v5.0)

빌더 에이전트가 코드 완성 후 실행하는 자체 검증 명령어 목록.
기획 단계에서 결정된 기술 스택에 따라 해당 섹션의 명령어를 빌더 프롬프트에 삽입한다.

---

## 매핑 테이블

| 기술 스택 | 타입체크 | 린트 | 빌드 | 테스트 | 추가 검증 |
|-----------|---------|------|------|--------|----------|
| TypeScript + React | `tsc --noEmit` | `npx eslint .` | `npm run build` | `npm test` | — |
| TypeScript + Next.js | `tsc --noEmit` | `npx eslint .` | `npm run build` | `npm test` | `next lint` |
| TypeScript + Node | `tsc --noEmit` | `npx eslint .` | `npm run build` | `npm test` | — |
| JavaScript (Vanilla) | — | `npx eslint .` | — | — | `node --check *.js` 문법 검사 |
| Python + FastAPI | `mypy .` | `ruff check .` | — | `pytest` | `ruff format --check .` |
| Python + Django | `mypy .` | `ruff check .` | — | `python manage.py test` | `python manage.py check` |
| Python (스크립트) | `mypy .` | `ruff check .` | — | `pytest` | — |
| Rust | `cargo check` | `cargo clippy -- -D warnings` | `cargo build --release` | `cargo test` | `cargo fmt --check` |
| Java + Spring Boot | — | — | `./mvnw verify` | `./mvnw test` | JaCoCo 커버리지 85%+ |
| Java + Gradle | — | — | `./gradlew build` | `./gradlew test` | — |
| Swift + SwiftUI | — | `swiftlint` | `xcodebuild build` | `xcodebuild test` | — |
| Go | `go vet ./...` | `golangci-lint run` | `go build ./...` | `go test ./...` | — |
| Electron + React | `tsc --noEmit` | `npx eslint .` | `electron-vite build` | `npm test` | — |
| Tauri + React | `tsc --noEmit` | `npx eslint .` | `npm run tauri build` | `npm test` | `cargo clippy` (Rust 백엔드) |
| HTML/CSS/JS (정적) | — | — | — | — | `npx serve .` + curl HTTP 200 확인 |

---

## 리더가 빌더 프롬프트에 삽입하는 방법

기획 단계(Phase 1)에서 기술 스택이 결정되면, 리더는 위 테이블에서 해당 스택의 명령어를 찾아 빌더 프롬프트의 `## 자체 검증 게이트` 섹션에 삽입한다.

### 예시: TypeScript + React 프로젝트

```
## 자체 검증 게이트 (빌더 완료 전 필수)

| 단계 | 명령어 | 통과 기준 |
|------|--------|----------|
| 1. 타입체크 | tsc --noEmit | 에러 0건 |
| 2. 린트 | npx eslint . | 에러 0건 (warning 허용) |
| 3. 빌드 | npm run build | exit code 0 |
| 4. 테스트 | npm test | 전체 PASS |

- 실패한 단계가 있으면 수정 후 재실행
- 각 단계의 실행 결과를 report.md에 첨부
```

### 예시: Rust 프로젝트

```
## 자체 검증 게이트 (빌더 완료 전 필수)

| 단계 | 명령어 | 통과 기준 |
|------|--------|----------|
| 1. 타입체크 | cargo check | 에러 0건 |
| 2. 린트 | cargo clippy -- -D warnings | 경고 0건 |
| 3. 빌드 | cargo build --release | exit code 0 |
| 4. 테스트 | cargo test | 전체 PASS |
| 5. 포맷 | cargo fmt --check | 포맷 일치 |

- 실패한 단계가 있으면 수정 후 재실행
- 각 단계의 실행 결과를 report.md에 첨부
```

---

## 도구가 없는 프로젝트 처리

빌드/테스트 도구가 설정되지 않은 프로젝트(순수 HTML/CSS/JS, 초기 프로토타입 등)에서는:

1. 해당 단계를 `N/A — 도구 미설정`으로 기록
2. 자동 검증으로 대체:
   - HTML 유효성: 코드 리뷰로 구조적 오류 확인
   - JS 에러: `node --check 파일명.js`로 문법 검사
   - 정적 파일 서빙: `npx serve .` 후 curl로 HTTP 200 확인
3. 검증 결과를 report.md에 기록

---

## QC와의 관계

빌더의 자체 검증 게이트는 **1차 필터**다. QC 에이전트(Phase 3)의 6단계 검증 체인과 중복되지만, 이는 의도적이다:

- **빌더 게이트**: 빌더가 코드를 완성하기 전에 기본적인 결함을 잡는다
- **QC 6단계**: 독립적인 QC가 동일한 검증을 재실행하여 빌더의 자체 판단을 검증한다

빌더 게이트를 통과했다고 QC를 생략하지 않는다. 빌더 게이트가 있으면 QC에서 발견되는 기본 결함이 줄어 QC 재작업 횟수가 감소한다.
