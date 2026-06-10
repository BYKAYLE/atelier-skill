# Skill Capability Map — release v3.2

## Internal Skills

| 스킬 | 역할 | 위임 시 필수 | 제약 |
|------|------|------------|------|
| service-factory (Release mode) | Google-style 다중 에이전트 제품화 모드. Worker/Reviewer/Critic/Auditor 분리, 상태/게이트/증거 관리, Agent Foundry 제안 | 프로젝트 경로, 목표, 금지선, Service Factory state | `plan`은 agent_requests/prompt/foundry/watchdog/handoff 생성. 실제 spawn은 Release가 단계별 수행. DB/data 삭제, prod, 유료 API, 공격성 테스트는 승인 게이트 |
| autonomous-dev (v5.2.2) | 0→1 서비스/기능 빌더. PRD→디자인→개발→QC | 프로젝트 경로, 서비스/피처 구분 | Checkpoint 2회, QC 3회 실패→에스컬 |
| sisyphus_claude | 출시 수준까지 Release Loop 반복 보강 | 서비스 상태, DoD 기준 | 중간 보고 금지 |
| sisyphus-workflow (v1.1.0) | 시니어 엔지니어 구현/수정/조사 | TASK, EXPECTED OUTCOME | 3회 실패→재평가 |
| security-router | L1(OWASP)+L2(Sentry)+L3(TrailOfBits)+cybersecurity corpus lens 자동 조합 | 코드 성격, 경로, 검토 범위 | 최종 보안검토의 기본 정적/코드 감사 |
| probe | 독립 QA + 저부작용 런타임 보안 smoke (headers/cookies/mixed content/sensitive URL) | 대상 URL/API 또는 probe plan | Release Phase 6.5 게이트. report.md 재해석 금지, exit + summary.json만 소비 |
| pentest-router | 명시 승인된 침투/공격성 런타임 테스트 | 대상 URL/IP, 소유권, 승인 scope | Docker 필수, ~$50/회. 대표님 명시 승인 전 실행 금지 |
| ui-ux-pro-max (v1.2.0) | 산업별 디자인 시스템 + Pencil 앱 아이콘 | 제품 유형, 산업, 스택 | 아이콘=G() AI 필수 |
| taste-skill | AI smell 차단, 3다이얼 프리미엄 UI | 3다이얼 값, Tailwind 버전 | — |
| k-dense-ai | 170개 과학 스킬 라우터 | 키워드 | 라우터만, 유료 DB 불가 |
| skill-evolve | 6-에이전트 스킬 버전업 | — | 5개 이하 개선 |
| simplify | 코드=공격적 최적화, 프롬프트=보호 | — | Step/Phase 삭제 금지 |
| bykayle-slide-team (v2.0) | 10 에이전트 PPT 생성 | — | 같은 레이아웃 연속 금지 |
| it-field-support | PC/서버 자동 진단→해결 | SSH/PowerShell | 시스템 변경 승인 필수 |
| notebooklm | NotebookLM 자동화 (팟캐스트/퀴즈/슬라이드) | notebook_id, 소스 | 비공식 API, 5-45분 |
| deploy-pilot | Docker→NAS/VPS 8Phase 배포 | 프로젝트 경로, 서버 정보 | Checkpoint 2회 |
| kmd (v1.2.0) | 회사 정보+시장 인텔 DB | — | 수정/삭제 금지 |
| bk-wiki (v1.0.0) | Karpathy식 자동 지식 위키. Ingest/Query/Lint | — | raw/ 불변, wiki/ LLM 전용 |
| stella (v3.3.0) | AI 프로덕트 오너. WHAT/WHY 판단, 백로그 관리, 릴리스 위임 | 프로젝트 경로, product-vision.md | 비용 태스크 자율 실행 금지. 릴리스→스텔라는 에스컬레이션 전용 (순환 위임 아님) |

## Peer Orchestrators (release 하위 아님 — Stella가 직접 위임)

| 스킬 | 역할 | 협조 방식 |
|------|------|----------|
| night-lab (v4.0.0) | 자율 심층 R&D (베가펑크+7연구원) | release 파이프라인에서 연구 필요 시 협조 요청. 상하 관계 아님 |

## Plugin Skills

| 스킬 | 역할 | 제약 |
|------|------|------|
| pumasi (v1.4.0) | Codex 병렬 외주 (4+모듈 동시) | Codex CLI 필수, 1-2개면 오버헤드 |
| show-me-the-prd | 인터뷰→PRD 4종 문서 | 코드 생성 안함 |
| kkirikkiri | AI 에이전트 팀 자동 구성 | 팀장=Opus 필수 |
| skillers-suda | 4전문가 토론→스킬 생성 | 4에이전트 동시 스폰 |
| deep-research | 멀티 에이전트 심층 리서치 | 소스 삼각검증 |
| docs-guide | llms.txt 기반 공식 문서 검색 | JS 렌더링 제한 |
| autoresearch | Karpathy식 자율 반복 루프 (수정→검증→유지/폐기) | — |
| orch-architect | 오케스트레이터 설계/진단/자가성장 점검 | 수정은 사용자 승인 후 |

## Design Quality Pipeline (구현 후 적용)

| 단계 | 스킬 | 역할 | 제약 |
|------|------|------|------|
| 설정 | teach-impeccable | 프로젝트별 디자인 컨텍스트 1회 설정 | 프로젝트당 1회 |
| 구조 | arrange | 레이아웃/스페이싱/시각 리듬 | — |
| 구조 | normalize | 디자인 시스템 일관성 | — |
| 구조 | extract | 디자인 토큰/패턴 추출→시스템화 | — |
| 콘텐츠 | clarify | UX 카피/에러메시지/마이크로카피 | — |
| 콘텐츠 | typeset | 타이포그래피 (폰트/위계/크기) | — |
| 시각 | colorize | 전략적 색상 추가 | — |
| 시각 | bolder | 시각적 임팩트 부여 | — |
| 시각 | quieter | 과도한 디자인 톤다운 | — |
| 동작 | animate | 마이크로 인터랙션/모션 | — |
| 동작 | adapt | 반응형/크로스 플랫폼 | — |
| 경험 | onboard | 온보딩/빈 상태/첫 경험 | — |
| 경험 | delight | 기쁨/개성/의외성 | — |
| 정리 | distill | 불필요한 복잡성 제거 | — |
| 검증 | audit | 접근성/성능/테마/반응형 감사 | — |
| 검증 | critique | 디자인 효과성 평가 | — |
| 최종 | polish | 출시 전 최종 품질 패스 | — |
| 강화 | frontend-design | 프로덕션급 프론트엔드 생성 | — |
| 강화 | harden | 에러 핸들링/i18n/엣지 케이스 | — |
| 강화 | optimize | 로딩/렌더링/번들 최적화 | — |
| 강화 | overdrive | 기술 한계 극한 구현 | — |

## Quick Routing

| 요청 유형 | 스킬 |
|----------|------|
| 새 서비스 | autonomous-dev (서비스) |
| 최종 제품급 자율 개발 | service-factory |
| 기능 추가 | sisyphus-workflow 또는 autonomous-dev (피처) |
| 출시 보강 | sisyphus_claude |
| 버그 수정 | 직접 또는 sisyphus-workflow |
| 병렬 개발 | pumasi |
| PRD 기획 | show-me-the-prd |
| 시장 리서치 | notebooklm |
| 심층 R&D | night-lab (peer — 직접 라우팅, release 하위 아님) |
| 코드 보안 | security-router |
| 런타임 보안 smoke | probe |
| 침투/공격성 보안 테스트 | pentest-router (명시 승인 필요) |
| 배포 | deploy-pilot |
| 제품 판단 | stella |
| PPT | bykayle-slide-team |
| 스킬 관리 | skill-evolve / skillers-suda |
| 디자인 품질 | teach-impeccable → arrange/normalize → ... → polish |
| 자율 반복 | autoresearch |
| 지식 위키 | bk-wiki |
| 오케스트레이션 점검 | orch-architect |
