# Hermes Execution Patterns — 상세 절차

> SKILL.md §Hermes Execution Patterns에서 분리 (260610, Opus 4.8 경량화).
> 스텔라가 위임 지시문을 작성하거나 완료 보고를 검증할 때 해당 패턴만 Read한다.

## Pattern 1: Systematic Debugging (4Phase 근본 원인 조사)

**트리거**: 버그, 테스트 실패, 예상 밖 동작. 특히 "빠른 수정" 유혹이 클 때.

1. 에러 전체 읽기 → 재현 → 최근 변경 확인 → 데이터 흐름 추적 → 가설 수립 (코드 수정 전)
2. 유사한 정상 코드 찾기 → 고장 코드와 차이점 식별
3. 단일 가설 → 최소 변경으로 테스트 → 한 번에 한 변수만
4. 실패 회귀 테스트 작성 → 단일 수정 → 전체 회귀 검증
5. **Rule of Three**: 3회 이상 수정 실패 → 중단, 아키텍처 문제로 에스컬레이션

**금지**: 근본 원인 조사 완료 전 수정 제안.

## Pattern 2: Test-Driven Development (RED→GREEN→REFACTOR)

**트리거**: 모든 새 기능, 버그 수정, 리팩토링.

1. **RED**: 최소 실패 테스트 1개 작성 → 올바른 이유로 실패하는지 확인
2. **GREEN**: 테스트 통과하는 최소 코드 (하드코딩도 가능)
3. **REFACTOR**: 중복 제거, 이름 개선, 구조 정리 — 테스트 항상 녹색 유지
4. 다음 동작에 대해 1~3 반복

**금지**: 테스트 없이 코드 작성. 사후 테스트는 아무것도 증명 안 함.

## Pattern 3: Subagent-Driven Development (병렬 위임 + 2단계 리뷰)

**트리거**: 독립적 태스크 3개 이상 병렬 실행 시.

1. 계획에서 전체 태스크 추출 → 서브에이전트에 완전한 컨텍스트 전달 (파일 읽기 시키지 말 것)
2. 태스크당 독립 implementer 디스패치 (TDD 지시 포함)
3. **1차 리뷰**: spec 준수 확인 (요구사항 매칭, 범위 이탈 없음)
4. **2차 리뷰**: 코드 품질 (1차 통과 후에만)
5. 수정 → 재리뷰 루프, 양쪽 통과 후 다음 태스크

**금지**: 같은 파일 건드리는 태스크를 병렬 디스패치.

## Pattern 4: Implementation Planning (바이트사이즈 계획)

**트리거**: 다단계 기능 구현 전. 서브에이전트 위임 전.

1. 코드베이스 먼저 탐색 → 구조/컨벤션/기존 패턴 이해
2. 2~5분 단위 태스크로 분해, 각각 정확한 파일 경로 + 복사 가능한 코드 + 예상 결과
3. 각 태스크 = TDD 사이클 (실패 테스트 → 실패 확인 → 구현 → 통과 → 커밋)
4. DRY, YAGNI — 지금 필요한 것만

**금지**: "인증 추가" 같은 모호한 태스크. "src/models/user.py에 email+password_hash 필드 User 모델 생성" 수준.

## Pattern 5: Code Review (보안 우선 리뷰)

**트리거**: PR 리뷰, 코드 감사, 완료 보고 검증.

1. **보안 먼저**: 하드코딩 시크릿, 입력 검증, 파라미터화 쿼리, 경로 순회, 인증/인가
2. **에러 핸들링**: 외부 호출 try/catch, 민감 데이터 미노출 로깅, 리소스 정리
3. **코드 품질**: 함수 단일 책임(<50줄), 서술적 이름, 주석처리된 코드 삭제, DRY
4. **테스트**: 엣지 케이스, happy+error 경로, 새 코드에 테스트 존재

**출력 형식**: 요약 → 치명적(필수 수정) → 제안(선택) → 질문.

## Pattern 6: Resume from SOT (프로젝트 재개)

**트리거**: "이어서 하자", "어디까지 했지", 세션 재개.

1. 크로스세션 검색 + 실제 프로젝트 경로 확인
2. SOT/, sessions/, PRD/, plans/ 읽기 — 최근 세션 로그가 최우선
3. 마지막 세션 이후 추가된 코드 검사 — 정의 vs 실제 사용 구분
4. **4버킷 요약**: 마지막 마일스톤 / 추가된 것 / 미완성·스텁 / 다음 단계

**금지**: 파일 존재 = 완료로 판단. 실행 경로가 연결되었는지 반드시 검증.

## Pattern 7: Security Audit (6Phase 상용화 보안 감사)

**트리거**: 상용화 전, "보안 검사", "최종 감사".
**실행 스킬**: Phase 1-2 = `security-router` (릴리스 경유), Phase 2.5 = `pentest-router` (릴리스 경유), Phase 3-5 = 후처리.

1. Phase 1: 자동화 스캔 (CVE + 보안 린팅, CRITICAL/HIGH 0건 필수)
2. Phase 2: 4인 병렬 정적 감사 (STRIDE + OWASP Top 10 + Red Team + 시크릿 스캔)
3. Phase 2.5: 3인 병렬 런타임 공격 (localhost/staging만, 절대 프로덕션 아님)
4. Phase 3-4: 중복 제거 → 심각도 분류 → 수정 → 전체 테스트 통과 필수
5. Phase 5: 감사 보고서 (MD+PDF) — 수정 이력, 잔여 리스크, 점수

## Pattern 8: Deploy (체크포인트 기반 배포)

**트리거**: Docker 프로젝트 NAS/VPS/로컬 배포.

1. 프로젝트 분석 (compose/Dockerfile/nginx) → .env.production 준비 (절대 맹목 덮어쓰기 금지)
2. 프로덕션 인프라 패치 (헬스 엔드포인트, 보안 헤더, rate limiting)
3. rsync 전송 → 파일 도착 검증 → Docker Compose build+start
4. 공개 노출 (Cloudflare Tunnel) → 헬스체크 + DB 마이그레이션 + 검증

**Synology 주의**: 비표준 SSH 포트, docker 바이너리 경로, `docker rm -f` + sleep 후 `compose up -d`.

## Pattern 9: Research Pipeline (Edison 리서치 오케스트레이션)

**트리거**: Edison 프로젝트 리서치 실행.

1. 트리거 시 Research row 생성 → flush → context packet + loop plan 저장 → 커밋 (반쪽 커밋 금지)
2. 아키텍처 분리: Backend=컨텍스트+영속화, Runner=실행 브릿지, NotebookLM=슬라이드만, Hermes=루프+보고서
3. Runner가 저장된 JSON blob 소비 → 루프별 산출물 → NotebookLM 슬라이드
4. E2E 전 스키마 드리프트 필수 확인 (Alembic 버전 vs 실제 DB)
5. 신규 실행 + 재시도 경로 각각 별도 검증
