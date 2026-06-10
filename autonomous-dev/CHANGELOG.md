# Changelog — autonomous-dev

## v5.2.2 (2026-03-09)
전체 파일 용어 일원화. 8개 파일 교차 분석 기반 6건 수정.
- phase-details.md: Mode A/B 잔여 참조 → 서비스 빌더/피처 빌더 (2건)
- qc-checklist.md: Audit 2 Performance P0/P1/P2 → CRITICAL/HIGH/MEDIUM
- sot-management.md: checkpoint Phase 이름 3건 통일 (빌드+런타임/보안품질QC/브라우저시각)
- 중복/비효율 프로세스 0건 (다층 검증은 모두 의도적 중복으로 확인)

## v5.2.1 (2026-03-09)
Simplify 리뷰 기반 8건 수정.
- Phase 3 이름 '기능 QC (정적 분석)'으로 3개 파일 통일
- Mode A/B → 서비스 빌더/피처 빌더 용어 통일
- P0/P1/P2 → CRITICAL/HIGH/MEDIUM 심각도 스케일 통일
- qc-checklist.md Final QC 실행 타이밍에 Phase 3.3 추가
- SOT 폴더 구조에 누락 파일 5개 추가
- changelog을 CHANGELOG.md로 분리 (~800 토큰 절감)
- checkpoint 템플릿에 Phase 3.3/3.5/3.7 추가
- S-Phase 1.7 UI 디자인 섹션 압축 (190줄 → 45줄)

## v5.2.0 (2026-03-08)
내부 정합성 수정. skill-evolve 내부 분석 기반.
- security-router 연동 동기화 (OWASP 직접 감사 → security-router 위임으로 전 파일 통일)
- Phase 흐름 불일치 수정 (Phase 3 PASS → 3.5가 아닌 → 3.3으로 교정, 서비스/피처 빌더 양쪽)
- RT-3/Audit 6 Smoke Test 역할 분담 명확화 (빠른 산점 검사 vs 심층 기능 검증)
- RT-1 빌드 검증에 의도적 중복 설명 추가 (빌더 1차 필터 vs RT 독립 검증)
- QC 차단 보고서 출력 형식을 QC 에이전트 프롬프트에 추가
- Phase 3.3 문서 게이트 누락 수정 (sot-management.md 게이트 테이블)
- 문서 에이전트 템플릿 D/E 추가 (Phase 3.3/3.5 완료 시)
- 권한 사전 승인 범위 확장 (Phase 2~3.5 → 2~3.7)
- QC 결과 보고서 테이블 "Security (OWASP)" → "Security (security-router)" 통일

## v5.1.0 (2026-03-07)
빌더 코드 품질 가드레일 강화. Jeffallan/alirezarezvani 스킬 벤치마킹 기반.
- MUST NOT DO 안티패턴 목록 추가 (빌더 프롬프트에 20+ 금지 패턴 삽입)
- 스택별 CLI 자체 검증 게이트 추가 (타입체크/린트/빌드/테스트 자동 실행)
- code-standards.md 신규 생성 (7개 스택별 필수 규칙 + 안티패턴)
- validation-gates.md 신규 생성 (14개 스택별 CLI 검증 명령어 매핑)
- 빌더가 코딩 표준 레퍼런스를 자동 참조하도록 프롬프트 연결

## v5.0.0 (2026-03-08)
런타임 검증 QC 레이어 추가. 정적 분석 → 실동작 검증 진화.
- Phase 3.3 신설: 빌드 검증 + DB 마이그레이션 + 런타임 Smoke Test + API 계약 테스트
- Phase 3.7 신설: 브라우저 스크린샷 시각 검증 (선택적)
- 런타임 QC 에이전트 프롬프트 템플릿 추가
- qc-checklist.md에 런타임 검증 체크리스트 추가
- QC 파이프라인: Phase 3 → 3.3 → 3.5 → (3.7) → 4 로 확장

## v4.0.0 (2026-03-05)
UI/UX 디자인 인텔리전스 연동. ui-ux-pro-max 벤치마킹 기반.
- 디자인 인텔리전스 연동 (ui-ux-pro-max 4단계 워크플로우 호출)
- 디자인 에이전트 프롬프트 템플릿 신규 추가
- QC 접근성/반응형/터치 체크리스트 대폭 확장
- 디자인 시스템 준수 QC 항목 추가
- SOT에 design-intelligence.md 추가

## v3.0.0 (2026-03-05)
QC 강화 + 에이전트 규율 보강. superpowers/ECC/OMC 분석 기반.
- 합리화 방지 패턴 (빌더/QC 프롬프트에 변명-반박 테이블 추가)
- 6단계 검증 체인 (Build→Lint→Test→Security→Diff→Report)
- 증거 언어 규칙 (실행 결과 첨부 필수, 추측 표현 금지)
- QC 차단 보고서 + 에스컬레이션 보고서 구조화
- Phase 전환 핸드오프 문서 (결정/거부/리스크/진입조건)
- 빌드 전 일관성 확인 (SOT vs 코드 정합성 체크)
- 모호성 내부 게이트 (S-Phase 0에서 Goal/Constraints/Criteria/Context 자가 판정)
- 자기 개선 루프 3중 게이트 (재현 가능성/일반화 가능성/명확성 + 규칙 충돌 확인)

## v2.0.0 (2026-03-04)
권한 관리 레이어 추가. gptaku-plugins 4종 비교 분석 기반 버전업.

## v1.0.0 (원본)
~/.claude/skills-archive/autonomous-dev-v1/ 에 백업 보관.
