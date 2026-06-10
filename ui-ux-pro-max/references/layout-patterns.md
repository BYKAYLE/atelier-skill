# 레이아웃 패턴 백과사전

## 1. 그리드 시스템

### 1.1 12컬럼 그리드

```css
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 24px;
}
.col-1 { grid-column: span 1; }
.col-2 { grid-column: span 2; }
.col-3 { grid-column: span 3; }
.col-4 { grid-column: span 4; }
.col-5 { grid-column: span 5; }
.col-6 { grid-column: span 6; }
.col-7 { grid-column: span 7; }
.col-8 { grid-column: span 8; }
.col-9 { grid-column: span 9; }
.col-10 { grid-column: span 10; }
.col-11 { grid-column: span 11; }
.col-12 { grid-column: span 12; }

/* 반응형 */
@media (max-width: 767px) {
  .grid { grid-template-columns: 1fr; gap: 16px; }
  [class^="col-"] { grid-column: span 1; }
}
@media (min-width: 768px) and (max-width: 1023px) {
  .grid { gap: 20px; }
}
```

### 1.2 8pt 그리드 시스템

모든 간격과 크기를 8의 배수로 통일.

```css
:root {
  --space-1: 4px;    /* 하프 유닛 (예외적으로만 사용) */
  --space-2: 8px;    /* 기본 유닛 */
  --space-3: 12px;   /* 1.5 유닛 */
  --space-4: 16px;   /* 2 유닛 */
  --space-5: 20px;   /* 2.5 유닛 */
  --space-6: 24px;   /* 3 유닛 */
  --space-8: 32px;   /* 4 유닛 */
  --space-10: 40px;  /* 5 유닛 */
  --space-12: 48px;  /* 6 유닛 */
  --space-16: 64px;  /* 8 유닛 */
  --space-20: 80px;  /* 10 유닛 */
  --space-24: 96px;  /* 12 유닛 */
  --space-32: 128px; /* 16 유닛 */
}
```

### 1.3 4pt 서브그리드

텍스트와 작은 요소 정렬에 4px 단위 사용:

| 용도 | 크기 |
|------|------|
| 아이콘-텍스트 간격 | 4px 또는 8px |
| 인라인 패딩 | 4px, 8px, 12px |
| 레이블-입력 간격 | 4px, 8px |
| 리스트 항목 간격 | 4px, 8px |

---

## 2. Flexbox 패턴

### 2.1 Holy Grail 레이아웃

```css
/* 헤더 + 사이드바 + 메인 + 사이드바 + 푸터 */
.holy-grail {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.holy-grail__header {
  height: 64px;
  flex-shrink: 0;
}
.holy-grail__body {
  display: flex;
  flex: 1;
}
.holy-grail__sidebar {
  width: 240px;
  flex-shrink: 0;
}
.holy-grail__main {
  flex: 1;
  min-width: 0; /* 오버플로 방지 */
}
.holy-grail__footer {
  flex-shrink: 0;
}

@media (max-width: 767px) {
  .holy-grail__body { flex-direction: column; }
  .holy-grail__sidebar { width: 100%; }
}
```

### 2.2 Sidebar + Content

```css
.layout-sidebar {
  display: flex;
  min-height: 100vh;
}
.layout-sidebar__nav {
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid #E5E7EB;
  background: #FFFFFF;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}
.layout-sidebar__content {
  flex: 1;
  min-width: 0;
  padding: 32px;
  background: #F8FAFC;
}

@media (max-width: 1023px) {
  .layout-sidebar__nav {
    position: fixed;
    left: -240px;
    z-index: 40;
    transition: left 0.3s ease;
  }
  .layout-sidebar__nav--open {
    left: 0;
  }
}
```

### 2.3 Equal Height Cards

```css
.card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}
.card-grid__item {
  flex: 1 1 300px; /* 최소 300px, 균등 분배 */
  display: flex;
  flex-direction: column;
}
.card-grid__item .card__body {
  flex: 1; /* 본문 영역이 늘어나서 높이 균등 */
}
.card-grid__item .card__footer {
  margin-top: auto; /* 푸터는 항상 하단 */
}
```

### 2.4 센터링 패턴

```css
/* Flex 센터링 (가장 범용) */
.center-flex {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Grid 센터링 (가장 간결) */
.center-grid {
  display: grid;
  place-items: center;
}

/* 절대 위치 센터링 */
.center-absolute {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* 마진 센터링 (수평만) */
.center-margin {
  margin-left: auto;
  margin-right: auto;
}
```

---

## 3. CSS Grid 패턴

### 3.1 Dashboard Grid

```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: auto;
  gap: 24px;
  padding: 24px;
}
/* KPI 카드 — 한 줄 4개 */
.dashboard-grid__kpi {
  grid-column: span 1;
}
/* 넓은 차트 — 2칸 */
.dashboard-grid__chart-wide {
  grid-column: span 2;
}
/* 전체 너비 테이블 */
.dashboard-grid__table {
  grid-column: 1 / -1;
}

@media (max-width: 1023px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
}
@media (max-width: 767px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}
```

### 3.2 Bento Box Grid

```css
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: 200px;
  gap: 16px;
}
.bento-grid__item--tall {
  grid-row: span 2;
}
.bento-grid__item--wide {
  grid-column: span 2;
}
.bento-grid__item--large {
  grid-column: span 2;
  grid-row: span 2;
}

@media (max-width: 767px) {
  .bento-grid {
    grid-template-columns: repeat(2, 1fr);
    grid-auto-rows: 150px;
  }
}
```

### 3.3 Masonry (CSS Grid 근사)

```css
/* CSS columns 기반 Masonry */
.masonry {
  columns: 3;
  column-gap: 24px;
}
.masonry__item {
  break-inside: avoid;
  margin-bottom: 24px;
}

@media (max-width: 1023px) { .masonry { columns: 2; } }
@media (max-width: 767px) { .masonry { columns: 1; } }
```

### 3.4 Auto-fill / Auto-fit

```css
/* Auto-fill: 최소 280px, 빈 공간은 빈 트랙으로 유지 */
.grid-auto-fill {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

/* Auto-fit: 최소 280px, 빈 공간은 기존 트랙이 확장 */
.grid-auto-fit {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

/* 차이: auto-fill은 빈 자리 유지, auto-fit은 늘려서 채움 */
/* 카드 그리드에는 auto-fill 권장 (일정한 카드 크기 유지) */
```

---

## 4. 반응형 브레이크포인트

### 4.1 표준 브레이크포인트

| 이름 | 범위 | 대상 디바이스 | 컬럼 | 마진 |
|------|------|-------------|------|------|
| Mobile S | ~374px | 작은 폰 | 4 | 16px |
| Mobile | 375~767px | 일반 폰 | 4 | 20px |
| Tablet | 768~1023px | 태블릿 | 8 | 32px |
| Desktop | 1024~1439px | 노트북/데스크톱 | 12 | 32~64px |
| Wide | 1440px+ | 대형 모니터 | 12 | auto (센터링) |

```css
/* Mobile First 미디어 쿼리 */
/* 기본: 모바일 (375px) */

@media (min-width: 640px) {
  /* sm: 작은 태블릿, 가로 모바일 */
}
@media (min-width: 768px) {
  /* md: 태블릿 */
}
@media (min-width: 1024px) {
  /* lg: 데스크톱 */
}
@media (min-width: 1280px) {
  /* xl: 넓은 데스크톱 */
}
@media (min-width: 1536px) {
  /* 2xl: 울트라와이드 */
}
```

### 4.2 컨테이너 최대 너비

```css
.container {
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  padding-left: 20px;
  padding-right: 20px;
}
@media (min-width: 640px) { .container { max-width: 640px; } }
@media (min-width: 768px) { .container { max-width: 768px; padding: 0 32px; } }
@media (min-width: 1024px) { .container { max-width: 1024px; } }
@media (min-width: 1280px) { .container { max-width: 1200px; } }
```

---

## 5. 컨테이너 쿼리

```css
/* 부모 컨테이너 기준으로 스타일 적용 */
.card-container {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 16px;
  }
}
@container card (max-width: 399px) {
  .card {
    display: flex;
    flex-direction: column;
  }
}
```

---

## 6. 사이드바 레이아웃

### 6.1 크기 규격

| 상태 | 너비 | 콘텐츠 |
|------|------|--------|
| 확장 | 240~280px | 아이콘 + 텍스트 + 섹션 헤더 |
| 축소 | 60~72px | 아이콘만 + 툴팁 |
| 오버레이 (모바일) | 280~320px | 전체 내비게이션 |

```css
.sidebar {
  width: 240px;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  background: #FFFFFF;
  border-right: 1px solid #E5E7EB;
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  z-index: 30;
  overflow: hidden;
}
.sidebar--collapsed {
  width: 60px;
}
.sidebar__content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.sidebar__footer {
  padding: 8px;
  border-top: 1px solid #E5E7EB;
}

/* 메인 콘텐츠 오프셋 */
.main-content {
  margin-left: 240px;
  transition: margin-left 0.2s ease;
}
.sidebar--collapsed ~ .main-content {
  margin-left: 60px;
}
@media (max-width: 1023px) {
  .sidebar {
    transform: translateX(-100%);
    width: 280px;
    box-shadow: 4px 0 24px rgba(0,0,0,0.15);
  }
  .sidebar--open {
    transform: translateX(0);
  }
  .main-content {
    margin-left: 0;
  }
}
```

---

## 7. 대시보드 레이아웃

```
┌──────────────────────────────────────┐
│              Top Bar (64px)          │
├──────┬───────────────────────────────┤
│      │  ┌──┐ ┌──┐ ┌──┐ ┌──┐       │
│ Side │  │KPI│ │KPI│ │KPI│ │KPI│      │
│ Bar  │  └──┘ └──┘ └──┘ └──┘       │
│      │  ┌─────────┐ ┌─────────┐    │
│ 240px│  │ Chart   │ │ Chart   │    │
│      │  │ (2col)  │ │ (2col)  │    │
│      │  └─────────┘ └─────────┘    │
│      │  ┌──────────────────────┐    │
│      │  │       Table          │    │
│      │  │     (full width)     │    │
│      │  └──────────────────────┘    │
└──────┴───────────────────────────────┘
```

```css
.dashboard {
  display: flex;
  min-height: 100vh;
}
.dashboard__sidebar {
  width: 240px;
  flex-shrink: 0;
}
.dashboard__main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.dashboard__topbar {
  height: 64px;
  flex-shrink: 0;
}
.dashboard__content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}
.dashboard__kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}
.dashboard__chart-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}
.dashboard__table-row {
  margin-bottom: 24px;
}

@media (max-width: 1023px) {
  .dashboard__kpi-row { grid-template-columns: repeat(2, 1fr); }
  .dashboard__chart-row { grid-template-columns: 1fr; }
}
@media (max-width: 767px) {
  .dashboard__kpi-row { grid-template-columns: 1fr; }
  .dashboard__content { padding: 16px; }
}
```

---

## 8. 랜딩 페이지 레이아웃

```
┌──────────────────────────────────┐
│         Navigation Bar           │
├──────────────────────────────────┤
│                                  │
│          Hero Section            │
│    제목 + 설명 + CTA + 이미지    │
│        (100vh 또는 80vh)         │
├──────────────────────────────────┤
│        Social Proof / Logo       │
├──────────────────────────────────┤
│        Features (3~4 col)        │
├──────────────────────────────────┤
│    Feature Detail (zigzag)       │
│    이미지 좌/텍스트 우 교차       │
├──────────────────────────────────┤
│       Testimonials / Reviews     │
├──────────────────────────────────┤
│        Pricing (3 plans)         │
├──────────────────────────────────┤
│          FAQ (Accordion)         │
├──────────────────────────────────┤
│        Final CTA Section         │
├──────────────────────────────────┤
│            Footer                │
└──────────────────────────────────┘
```

```css
/* Hero Section */
.hero {
  min-height: 80vh;
  display: flex;
  align-items: center;
  padding: 80px 24px;
}
.hero__content {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;
}
.hero__title {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
}
.hero__description {
  font-size: 18px;
  color: #6B7280;
  line-height: 1.6;
  margin-top: 16px;
  max-width: 540px;
}
.hero__cta {
  display: flex;
  gap: 12px;
  margin-top: 32px;
}

/* Features Grid */
.features {
  padding: 96px 24px;
}
.features__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 48px;
  max-width: 1200px;
  margin: 0 auto;
}
.feature-card__icon {
  width: 48px;
  height: 48px;
  background: #EFF6FF;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}
.feature-card__title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}
.feature-card__description {
  font-size: 14px;
  color: #6B7280;
  line-height: 1.6;
}

/* Zigzag Feature Detail */
.zigzag {
  padding: 96px 24px;
  max-width: 1200px;
  margin: 0 auto;
}
.zigzag__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;
  margin-bottom: 96px;
}
.zigzag__row:nth-child(even) {
  direction: rtl; /* 이미지/텍스트 좌우 교차 */
}
.zigzag__row:nth-child(even) > * {
  direction: ltr;
}

@media (max-width: 767px) {
  .hero__content { grid-template-columns: 1fr; gap: 32px; }
  .features__grid { grid-template-columns: 1fr; gap: 32px; }
  .zigzag__row { grid-template-columns: 1fr; gap: 32px; }
  .zigzag__row:nth-child(even) { direction: ltr; }
}
```

---

## 9. 폼 레이아웃

### 9.1 Single Column (기본 추천)

```css
.form-single {
  max-width: 480px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
```

### 9.2 Two Column

```css
.form-two-col {
  max-width: 720px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px 16px;
}
.form-two-col__full {
  grid-column: 1 / -1;
}

@media (max-width: 767px) {
  .form-two-col { grid-template-columns: 1fr; }
}
```

### 9.3 Wizard / Stepper

```css
.wizard {
  max-width: 640px;
  margin: 0 auto;
}
.wizard__stepper {
  display: flex;
  justify-content: center;
  gap: 0;
  margin-bottom: 48px;
}
.wizard__step {
  display: flex;
  align-items: center;
  gap: 8px;
}
.wizard__step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}
.wizard__step--active .wizard__step-number {
  background: #3B82F6;
  color: #FFFFFF;
}
.wizard__step--completed .wizard__step-number {
  background: #10B981;
  color: #FFFFFF;
}
.wizard__step--pending .wizard__step-number {
  background: #E5E7EB;
  color: #9CA3AF;
}
.wizard__connector {
  width: 60px;
  height: 2px;
  background: #E5E7EB;
  margin: 0 8px;
  align-self: center;
}
.wizard__connector--completed {
  background: #10B981;
}
.wizard__actions {
  display: flex;
  justify-content: space-between;
  margin-top: 32px;
}
```

---

## 10. 목록 레이아웃

### 10.1 카드 그리드

```css
.list-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}
```

### 10.2 리스트 뷰

```css
.list-view {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: #E5E7EB; /* 간격선 */
}
.list-view__item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: #FFFFFF;
}
.list-view__item:hover {
  background: #F9FAFB;
}
```

### 10.3 뷰 전환 (그리드/리스트)

```css
.view-toggle {
  display: flex;
  gap: 4px;
  background: #F3F4F6;
  border-radius: 8px;
  padding: 4px;
}
.view-toggle__btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: #6B7280;
}
.view-toggle__btn--active {
  background: #FFFFFF;
  color: #111827;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
```

---

## 11. Z-index 관리 전략

### 11.1 Z-index 스케일

```css
:root {
  --z-base: 0;
  --z-dropdown: 10;
  --z-sticky: 20;
  --z-fixed: 30;
  --z-sidebar: 30;
  --z-backdrop: 40;
  --z-modal: 50;
  --z-popover: 60;
  --z-tooltip: 70;
  --z-toast: 80;
  --z-max: 9999;    /* 최후 수단 — 사용 자제 */
}
```

### 11.2 쌓임 규칙

| 레벨 | Z-index | 요소 |
|------|---------|------|
| 기본 | 0 | 일반 콘텐츠 |
| 드롭다운 | 10 | Select, Dropdown, Combobox |
| 고정 | 20~30 | Sticky header, Sidebar, Fixed 요소 |
| 오버레이 | 40 | Modal backdrop, Drawer backdrop |
| 모달 | 50 | Modal, Dialog, Drawer |
| 팝오버 | 60 | Popover, Floating menu |
| 툴팁 | 70 | Tooltip |
| 알림 | 80 | Toast, Snackbar |

**금지 사항:**
- `z-index: 999999` 같은 임의 값 사용 금지
- 스케일 없이 z-index 사용 금지
- 새 z-index 레벨 추가 시 기존 스케일에 맞춰 추가

---

## 12. 여백/패딩 스케일

### 12.1 스페이싱 스케일 (8pt 기반)

| 토큰 | 값 | 용도 |
|------|---|------|
| space-0.5 | 2px | 극소 간격 |
| space-1 | 4px | 아이콘-텍스트, 인라인 요소 |
| space-1.5 | 6px | 작은 패딩 |
| space-2 | 8px | 기본 간격, 리스트 항목 |
| space-3 | 12px | 폼 필드 패딩 |
| space-4 | 16px | 카드 패딩 (소), 폼 필드 간격 |
| space-5 | 20px | 모바일 좌우 마진 |
| space-6 | 24px | 카드 패딩 (중), 그리드 갭 |
| space-8 | 32px | 섹션 내 간격, 큰 카드 패딩 |
| space-10 | 40px | 섹션 간 간격 (소) |
| space-12 | 48px | 섹션 간 간격 (중) |
| space-16 | 64px | 섹션 간 간격 (대) |
| space-20 | 80px | 페이지 섹션 간 간격 |
| space-24 | 96px | 큰 섹션 구분 |
| space-32 | 128px | Hero/풀페이지 섹션 |

### 12.2 실무 적용

```css
/* 페이지 래퍼 */
.page { padding: 24px; }                         /* 데스크톱 */
@media (max-width: 767px) { .page { padding: 16px; } } /* 모바일 */

/* 카드 내부 */
.card { padding: 24px; }
.card--compact { padding: 16px; }
.card--spacious { padding: 32px; }

/* 섹션 */
.section { padding: 64px 0; }
@media (max-width: 767px) { .section { padding: 48px 0; } }

/* 폼 */
.form-group { margin-bottom: 24px; }
.form-group label { margin-bottom: 6px; }

/* 목록 */
.list-item { padding: 12px 16px; }
.list-item + .list-item { border-top: 1px solid #F3F4F6; }
```

---

## 13. 인증 레이아웃

```css
/* 로그인/회원가입 페이지 */
.auth-layout {
  min-height: 100vh;
  display: flex;
}
.auth-layout__form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.auth-layout__visual-side {
  flex: 1;
  background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 64px;
}
.auth-form {
  width: 100%;
  max-width: 400px;
}
.auth-form__title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}
.auth-form__subtitle {
  font-size: 14px;
  color: #6B7280;
  margin-bottom: 32px;
}

@media (max-width: 1023px) {
  .auth-layout__visual-side { display: none; }
}
```

---

## 14. 설정/프로필 레이아웃

```css
.settings-layout {
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
  gap: 48px;
  padding: 32px 24px;
}
.settings-layout__nav {
  width: 200px;
  flex-shrink: 0;
  position: sticky;
  top: 96px;
  height: fit-content;
}
.settings-layout__nav-item {
  display: block;
  padding: 8px 16px;
  font-size: 14px;
  color: #6B7280;
  border-radius: 8px;
  text-decoration: none;
  margin-bottom: 2px;
}
.settings-layout__nav-item:hover { background: #F3F4F6; color: #111827; }
.settings-layout__nav-item--active { background: #EFF6FF; color: #3B82F6; font-weight: 500; }

.settings-layout__content {
  flex: 1;
  min-width: 0;
}
.settings-section {
  margin-bottom: 48px;
  padding-bottom: 48px;
  border-bottom: 1px solid #E5E7EB;
}
.settings-section:last-child {
  border-bottom: none;
}

@media (max-width: 767px) {
  .settings-layout { flex-direction: column; gap: 24px; }
  .settings-layout__nav { width: 100%; position: static; display: flex; overflow-x: auto; }
}
```
