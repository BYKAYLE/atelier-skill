---
name: ui-ux-pro-max
version: "1.2.0"
description: |
  Use when designing UI/UX with industry-specific and product-specific design standards.
  Provides verified design criteria for the autonomous-dev S-Phase 1.7 UI design stage.
  Includes Pencil MCP app icon generation system with validated G() AI prompt formulas.
  Triggers: "UI 디자인", "디자인 시스템", "UI/UX 가이드", "디자인 인텔리전스",
  "색상 팔레트", "타이포그래피", "앱 아이콘", "아이콘 디자인"
---

# UI/UX Pro Max — 디자인 인텔리전스 엔진

## 호출 방식

이 스킬은 단독으로 사용하거나, autonomous-dev 스킬의 S-Phase 1.7 Step 0에서 자동 호출된다.

**autonomous-dev 연동 시:**
1. autonomous-dev가 기획서(planning.md)에서 키워드를 추출한다
2. 이 스킬의 4단계 워크플로우를 실행한다
3. 결과를 SOT/design-intelligence.md에 저장한다
4. 이후 Stage 1~3 시안 제작의 기초로 사용한다

---

## 아이콘 디자인 모드

앱 아이콘, 앱 심볼, 아이콘 디자인 관련 요청이 감지되면 **아이콘 디자인 전용 워크플로우**를 실행한다.

### 아이콘 모드 트리거
- "앱 아이콘", "아이콘 디자인", "앱 심볼", "macOS 아이콘", "iOS 아이콘"
- autonomous-dev의 아이콘 에셋 제작 단계

### 아이콘 워크플로우 (3단계: 수집 → 숙지 → 제작)

> **핵심 원칙**: 디자인 전에 반드시 자료 수집·숙지를 완료한다. 바로 디자인에 들어가지 않는다.

#### Phase A — 자료 수집 & 숙지 (필수, 스킵 불가)

1. **NAS DB 전체 로드** — 저장된 모든 디자인 자료를 읽고 숙지:
   - `references/icon-design.md` (§1~8 핵심 요약)
   - NAS `trend-research-2026.md` (트렌드, 프롬프트 키워드, 카테고리 매칭)
   - NAS `app-icon-design-bible.md` (종합 디자인 기준 12개 섹션)
   - NAS `academic-research.md` (학술 논문, Apple 철학, 프로 공식)
   - NAS `deep-research-report.md` (경쟁사, 시장 분석)

2. **최신 트렌드 실시간 리서치** — WebSearch로 관련 분야 최신 동향 수집:
   - `"[앱 카테고리] app icon design trends [현재 연도]"` 검색
   - `"best [앱 카테고리] app icons [현재 연도]"` 검색
   - 기존 DB에 없는 새로운 트렌드/기법 발견 시 메모
   - 검색 결과에서 구체적인 시각적 기법, 색상, 소재 키워드 추출

3. **리서치 결과 NAS 자동 저장** — 수집한 새 자료는 묻지 않고 NAS에 저장:
   - 기존 파일 업데이트 가능하면 → 해당 파일에 추가
   - 새로운 주제면 → 새 파일 생성 (`~/CloudDrives/kansic/KMD/design-db/icon-design/`)
   - NAS README.md 인덱스도 함께 갱신

#### Phase B — 전략 수립

4. **앱 분석**: 앱 이름, 기능, 플랫폼, 타겟 사용자 파악
5. **경쟁사 색상 분석**: DB의 경쟁사 데이터 + 실시간 검색으로 회피 색상 결정
6. **트렌드 매칭**: NAS `trend-research-2026.md` §3 매트릭스에서 앱 카테고리 → 추천 트렌드 선택
7. **색상 5종 선정**: 다양한 컬러 톤, 경쟁사 차별화, 트렌드 반영

#### Phase C — 디자인 제작

8. **Pencil MCP 사용 시** → §8 시스템 + 트렌드 적용:
   - §8.2 프레임 설정 (512×512, cornerRadius:115, clip:true)
   - §8.3 검증된 프롬프트 공식 + §6 트렌드 키워드 조합으로 G() 생성
   - §8.4 색상 다양성 가이드 (5종 = 5가지 다른 컬러 톤)
   - §8.5 실행 규칙 (G() 1개씩, 생성 후 스크린샷 검증)
   - §8.6 7-Point 검증 체크리스트
9. **코드 기반 디자인 시** → §1~7 이론 적용:
   - macOS HIG 규격 (Squircle, 키라인, 크기 세트)
   - 심볼 이론 (Shape Language, Gestalt, Golden Ratio)
   - 색상 전략 (경쟁사 차별화, 접근성, 대비비)
   - 8-Point Quality Checklist로 최종 검증
10. 결과물에 적용 트렌드 + 체크리스트 점수 포함

---

## 4단계 워크플로우 (UI/UX 일반)

### Step 1: 요구사항 분석

기획서 또는 사용자 요청에서 다음을 식별한다:

| 항목 | 예시 |
|------|------|
| 제품 유형 | SaaS 대시보드, 이커머스, 랜딩 페이지, 모바일 앱 |
| 스타일 | 미니멀, 글래스모피즘, 뉴모피즘, 브루탈리즘, 클래식 |
| 산업 | 핀테크, 헬스케어, 교육, 푸드, 부동산 |
| 기술 스택 | Tailwind, React, Next.js, Vue, Vanilla HTML/CSS |
| 타겟 사용자 | B2B, B2C, 개발자, 시니어, 어린이 |

**참조 파일:**
- `references/industry-patterns.md` — 산업별 필수 패턴, 추천 레이아웃, 색상 톤
- `references/design-principles.md` — 타겟 사용자에 맞는 원칙 선택

### Step 2: 디자인 시스템 생성

Step 1에서 식별한 조건을 조합하여 Master 디자인 시스템을 생성한다.

**생성 항목:**
- 색상 팔레트 (Primary / Secondary / Accent / Background / Text / Border / Status)
- 폰트 페어링 (제목 / 본문 / 코드) + Google Fonts URL
- 타입 스케일 (제목 1~6, 본문, 캡션)
- 스페이싱 스케일 (4px 기반)
- 보더 라디우스 체계
- 그림자/엘리베이션 체계
- 아이콘 스타일 추천
- 레이아웃 패턴 추천

**참조 파일:**
- `references/color-system.md` — 산업별 팔레트, 색상 이론, 시맨틱 컬러
- `references/typography.md` — 폰트 페어링, 타입 스케일, 반응형 타이포그래피
- `references/design-systems.md` — 디자인 토큰, 테마 전환, Tailwind 설정
- `references/components.md` — 컴포넌트별 스타일 기준

### Step 3: 보조 리서치

디자인 시스템의 각 영역을 심화 검증한다.

| 영역 | 참조 파일 | 검증 내용 |
|------|----------|----------|
| 색상 | `references/color-system.md` | WCAG 대비비, 다크모드 전환, CTA 전략 |
| 폰트 | `references/typography.md` | 가독성, 줄 높이, 반응형 크기 |
| UX 원칙 | `references/design-principles.md` | 인지 부하, 어포던스, 피츠의 법칙 |
| 접근성 | `references/accessibility.md` | WCAG 2.1 AA, ARIA, 키보드 내비게이션 |
| 반응형 | `references/responsive-mobile.md` | 브레이크포인트, 터치 타겟, Safe Area |
| 모션 | `references/animation-motion.md` | Easing, 듀레이션, reduced-motion |
| 레이아웃 | `references/layout-patterns.md` | 그리드, Flexbox, 대시보드 패턴 |
| 컴포넌트 | `references/components.md` | 상태, 접근성, 안티패턴 |
| 안티패턴 | `references/anti-patterns.md` | 피해야 할 패턴 목록 |

### Step 4: 스택 구현 규칙

기술 스택에 맞는 구현 규칙을 적용한다.

**참조 파일:**
- `references/stack-rules.md` — Tailwind, React, Next.js, Vue, Vanilla 등 스택별 규칙

**출력 예시:**
- Tailwind 사용 시: `tailwind.config.js` 설정, 유틸리티 클래스 조합
- React 사용 시: 컴포넌트 패턴, Hooks, 상태 관리
- Next.js 사용 시: App Router 패턴, 서버 컴포넌트 vs 클라이언트 컴포넌트

---

## 출력 형식

4단계 완료 후, 아래 구조의 디자인 인텔리전스 문서를 생성한다:

```markdown
# Design Intelligence — {프로젝트명}

## 1. 분석 결과
- 제품 유형: {타입}
- 산업: {산업}
- 스타일: {스타일}
- 기술 스택: {스택}

## 2. 디자인 시스템
### 색상 팔레트
- Primary: {헥스코드}
- Secondary: {헥스코드}
- ...

### 폰트
- 제목: {폰트명} (Google Fonts URL)
- 본문: {폰트명} (Google Fonts URL)

### 타입 스케일
- H1: {크기}
- ...

### 스페이싱
- xs: 4px, sm: 8px, ...

## 3. 추천 스타일 + 안티패턴
### 추천
- {패턴 1}
- {패턴 2}

### 안티패턴 (피할 것)
- {안티패턴 1}
- {안티패턴 2}

## 4. 접근성 필수 규칙
- {규칙 1}
- {규칙 2}

## 5. 반응형 필수 규칙
- {규칙 1}
- {규칙 2}

## 6. 스택 구현 규칙
- {규칙 1}
- {규칙 2}
```

---

## 참조 파일 목록

| 파일 | 내용 | 사용 시점 |
|------|------|----------|
| `references/design-principles.md` | 디자인 원칙 백과사전 | Step 1, 3 |
| `references/color-system.md` | 색상 체계 백과사전 | Step 2, 3 |
| `references/typography.md` | 타이포그래피 백과사전 | Step 2, 3 |
| `references/components.md` | 컴포넌트 패턴 백과사전 | Step 2, 3 |
| `references/layout-patterns.md` | 레이아웃 패턴 백과사전 | Step 2, 3 |
| `references/accessibility.md` | 접근성 백과사전 | Step 3 |
| `references/responsive-mobile.md` | 반응형/모바일 백과사전 | Step 3 |
| `references/animation-motion.md` | 애니메이션/모션 백과사전 | Step 3 |
| `references/industry-patterns.md` | 산업별 UI 패턴 백과사전 | Step 1, 3 |
| `references/design-systems.md` | 디자인 시스템 구축 백과사전 | Step 2 |
| `references/anti-patterns.md` | UI/UX 안티패턴 모음 | Step 3 |
| `references/stack-rules.md` | 기술 스택별 구현 규칙 | Step 4 |
| **`references/icon-design.md`** | **앱 아이콘 디자인 백과사전** | **아이콘 모드 전용** |

## NAS 외부 DB 연동

아이콘 디자인 시 NAS DB의 리서치 자료를 **자동 수집·적용**한다.

### 핵심 원칙 (반드시 준수)
1. **NAS 저장은 기본 동작** — 사용자가 요청하지 않아도 리서치 결과는 항상 NAS에 자동 저장
2. **DB 전체 숙지 후 디자인** — 저장된 모든 자료를 읽고 이해한 후에만 디자인 진행
3. **최신 트렌드 리서치 필수** — 매 디자인 작업 전 WebSearch로 관련 분야 최신 동향 수집
4. **리서치 → 숙지 → 저장 → 디자인** 순서를 절대 건너뛰지 않음

### 자동 로드 규칙 (Phase A에서 전부 읽기)
1. `references/icon-design.md` (§1~8 요약본) — 항상
2. NAS `trend-research-2026.md` (트렌드, 프롬프트 키워드, 카테고리 매칭) — 항상
3. NAS `app-icon-design-bible.md` (종합 디자인 기준 12개 섹션) — 항상
4. NAS `academic-research.md` (학술 논문, Apple 철학) — 항상
5. NAS `deep-research-report.md` (경쟁사, 시장 분석) — 경쟁사 분석 필요 시

### 자동 저장 규칙
- 새 트렌드 리서치 수행 시 → NAS에 바로 저장 (기존 파일 업데이트 또는 신규 생성)
- NAS README.md 인덱스 자동 갱신
- 저장 경로: `~/CloudDrives/kansic/KMD/design-db/icon-design/`

### DB 파일 목록

| 경로 | 내용 | 자동 로드 시점 |
|------|------|-------------|
| `~/CloudDrives/kansic/KMD/design-db/icon-design/trend-research-2026.md` | **2026 트렌드** — 핵심 5 + 보조 7 트렌드, G() 프롬프트, 카테고리 매칭, 성과 데이터 | **아이콘 디자인 시 항상 로드** |
| `~/CloudDrives/kansic/KMD/design-db/icon-design/app-icon-design-bible.md` | 아이콘 디자인 종합 레퍼런스 (12개 섹션) | 상세 디자인 기준 필요 시 |
| `~/CloudDrives/kansic/KMD/design-db/icon-design/academic-research.md` | 학술 논문, Apple 철학, 프로 공식, 시장 데이터 | 심화 연구 시 |
| `~/CloudDrives/kansic/KMD/design-db/icon-design/deep-research-report.md` | 심층 리서치 (Gestalt, Golden Ratio, 경쟁사, Liquid Glass, 시장 분석) | 경쟁사 분석/시장 조사 시 |
