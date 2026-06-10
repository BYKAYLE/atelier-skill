# 반응형/모바일 백과사전

## 1. Mobile-First 설계 원칙

### 1.1 핵심 개념

| 원칙 | 설명 |
|------|------|
| 콘텐츠 우선 | 모바일에서 핵심 콘텐츠만 보여주고, 넓은 화면에서 부가 요소 추가 |
| 성능 우선 | 모바일 네트워크를 기준으로 최적화 |
| 터치 우선 | 터치 인터랙션을 기본으로 설계, 마우스는 확장 |
| 점진적 향상 | 기본 기능 → 화면 크기에 따라 기능 추가 |

### 1.2 CSS 작성 순서

```css
/* 1. 모바일 기본 (375px 기준) */
.container {
  padding: 16px;
}
.grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 2. 태블릿 (768px+) */
@media (min-width: 768px) {
  .container { padding: 32px; }
  .grid {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .grid > * { flex: 1 1 calc(50% - 12px); }
}

/* 3. 데스크톱 (1024px+) */
@media (min-width: 1024px) {
  .container { padding: 32px 64px; max-width: 1200px; margin: 0 auto; }
  .grid > * { flex: 1 1 calc(33.33% - 16px); }
}
```

---

## 2. 브레이크포인트 전략

### 2.1 콘텐츠 기반 (권장)

콘텐츠가 깨지는 지점에서 브레이크포인트를 설정.

```css
/* 카드가 너무 좁아지는 시점에서 전환 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}
/* 브레이크포인트가 아닌 최소 너비로 자동 대응 */
```

### 2.2 디바이스 기반

| 브레이크포인트 | 대상 | 대표 디바이스 |
|-------------|------|-------------|
| 320px | 소형 모바일 | iPhone SE |
| 375px | 기본 모바일 | iPhone 12/13/14 |
| 390px | 프로 모바일 | iPhone 14 Pro |
| 428px | 맥스 모바일 | iPhone 14 Pro Max |
| 768px | 태블릿 세로 | iPad Mini/Air |
| 834px | 태블릿 큰 세로 | iPad Pro 11" |
| 1024px | 태블릿 가로, 작은 노트북 | iPad Pro 12.9" |
| 1280px | 노트북 | MacBook Air 13" |
| 1440px | 데스크톱 | 일반 모니터 |
| 1920px | 풀HD | 대형 모니터 |
| 2560px | QHD+ | 울트라와이드 |

### 2.3 실용적 브레이크포인트 세트

```css
/* 최소 세트 (3개) — 대부분의 프로젝트에 충분 */
@media (min-width: 768px) { /* 태블릿+ */ }
@media (min-width: 1024px) { /* 데스크톱+ */ }

/* 표준 세트 (5개) — Tailwind CSS 호환 */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

---

## 3. 터치 인터랙션

### 3.1 제스처 패턴

| 제스처 | 동작 | 일반적 사용 |
|--------|------|-----------|
| 탭 | 클릭/선택 | 버튼, 링크, 항목 선택 |
| 더블 탭 | 확대/축소 | 이미지, 지도 |
| 롱 프레스 | 컨텍스트 메뉴 | 드래그 시작, 다중 선택 |
| 스와이프 좌→우 | 뒤로 가기 | 네비게이션 |
| 스와이프 우→좌 | 삭제/액션 표시 | 리스트 항목 |
| 스와이프 아래 | 새로고침 | Pull-to-refresh |
| 핀치 | 확대/축소 | 이미지, 지도 |
| 팬 (드래그) | 이동 | 지도, 캐러셀 |

### 3.2 터치 피드백

```css
/* 터치 시 즉각 피드백 */
.touchable {
  -webkit-tap-highlight-color: transparent; /* 기본 하이라이트 제거 */
  touch-action: manipulation; /* 더블탭 줌 방지 */
  user-select: none;
}
.touchable:active {
  opacity: 0.7;
  transform: scale(0.98);
}

/* 리플 효과 */
.ripple {
  position: relative;
  overflow: hidden;
}
.ripple::after {
  content: "";
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background: radial-gradient(circle, rgba(0,0,0,0.1) 10%, transparent 10.01%);
  background-position: center;
  background-repeat: no-repeat;
  background-size: 1000%;
  opacity: 0;
  transition: background-size 0.5s, opacity 0.3s;
}
.ripple:active::after {
  background-size: 100%;
  opacity: 1;
  transition: 0s;
}
```

### 3.3 스와이프 삭제 패턴

```css
.swipe-item {
  position: relative;
  overflow: hidden;
  touch-action: pan-y; /* 세로 스크롤은 허용 */
}
.swipe-item__content {
  transition: transform 0.2s ease;
  background: #FFFFFF;
  position: relative;
  z-index: 1;
}
.swipe-item__action {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #EF4444;
  color: #FFFFFF;
}
/* JS로 translateX 제어 */
```

---

## 4. Safe Area

### 4.1 iOS 안전 영역

```css
/* 전체 페이지 */
body {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

/* 고정 하단 바 */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding-bottom: env(safe-area-inset-bottom);
  background: #FFFFFF;
}

/* 고정 상단 바 */
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  padding-top: env(safe-area-inset-top);
}

/* viewport-fit=cover 필수 */
```

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

### 4.2 Safe Area 크기 참고

| 디바이스 | 상단 | 하단 | 좌우 |
|---------|------|------|------|
| iPhone SE | 20px | 0px | 0px |
| iPhone 12~15 | 47px | 34px | 0px |
| iPhone 15 Pro (다이내믹 아일랜드) | 59px | 34px | 0px |
| iPad | 20~24px | 0px | 0px |

---

## 5. iOS Human Interface Guidelines 핵심 규칙

| 규칙 | 구체적 수치 |
|------|-----------|
| 최소 터치 타겟 | 44x44pt |
| 네비게이션 바 높이 | 44pt (Large Title: 96pt) |
| 탭바 높이 | 49pt (Safe Area 제외) |
| 아이콘 크기 (탭바) | 25x25pt ~ 31x31pt |
| 최소 폰트 | 11pt |
| 기본 본문 폰트 | 17pt (SF Pro) |
| 모달 모서리 | 10pt radius |
| 카드 모서리 | 10~16pt radius |
| 시스템 색상 | systemBlue: #007AFF, systemGreen: #34C759, systemRed: #FF3B30, systemOrange: #FF9500, systemYellow: #FFCC00, systemPurple: #AF52DE |
| 배경 | systemBackground: #FFFFFF (light), #000000 (dark) |
| 뒤로 가기 | 좌상단 chevron + 텍스트 |
| 스와이프 뒤로 | 좌측 가장자리에서 우측으로 |
| 동적 타입 | 사용자 폰트 크기 설정 존중 |

---

## 6. Material Design 3 핵심 규칙

| 규칙 | 구체적 수치 |
|------|-----------|
| 최소 터치 타겟 | 48x48dp |
| 앱바 높이 | 64dp (Top), 80dp (Bottom) |
| FAB 크기 | 56x56dp (기본), 40x40dp (소) |
| 네비게이션 바 높이 | 80dp |
| 네비게이션 레일 너비 | 80dp |
| 네비게이션 드로어 너비 | 360dp (max) |
| 기본 폰트 | Roboto, 14sp (본문) |
| 최소 폰트 | 12sp |
| 모서리 라디우스 스케일 | None: 0, Extra Small: 4dp, Small: 8dp, Medium: 12dp, Large: 16dp, Extra Large: 28dp, Full: 50% |
| 그림자 레벨 | Level 0~5 (0dp~12dp elevation) |
| 톤 서피스 | Surface 1~5 (Primary 색상 투명도 오버레이) |
| 상태 레이어 | Hover: 8%, Focus: 12%, Press: 12%, Drag: 16% |

---

## 7. 모바일 네비게이션 패턴

### 7.1 탭바 (iOS/Android 표준)

```css
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 56px;
  padding-bottom: env(safe-area-inset-bottom);
  background: #FFFFFF;
  border-top: 1px solid #E5E7EB;
  z-index: 40;
}
.tab-bar__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 8px 0;
  min-width: 64px;
  color: #9CA3AF;
  font-size: 10px;
  font-weight: 500;
  text-decoration: none;
}
.tab-bar__item--active {
  color: #3B82F6;
}
.tab-bar__icon {
  width: 24px;
  height: 24px;
}
```

**규칙:**
- 항목 3~5개 (5개 초과 시 "더 보기" 사용)
- 첫 번째 = 홈, 마지막 = 프로필/설정
- 아이콘 + 텍스트 (아이콘만은 접근성 위반)
- 활성 탭은 색상 + filled 아이콘으로 구분

### 7.2 햄버거 메뉴

```css
.hamburger {
  width: 44px;
  height: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.hamburger__line {
  width: 20px;
  height: 2px;
  background: #374151;
  border-radius: 1px;
  transition: all 0.2s ease;
}
/* 열린 상태: X 형태 */
.hamburger--open .hamburger__line:nth-child(1) {
  transform: rotate(45deg) translate(5px, 5px);
}
.hamburger--open .hamburger__line:nth-child(2) {
  opacity: 0;
}
.hamburger--open .hamburger__line:nth-child(3) {
  transform: rotate(-45deg) translate(5px, -5px);
}
```

### 7.3 바텀 시트

```css
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #FFFFFF;
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -4px 24px rgba(0,0,0,0.15);
  z-index: 50;
  max-height: 90vh;
  max-height: 90dvh;
  overflow-y: auto;
  transform: translateY(100%);
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
  padding-bottom: env(safe-area-inset-bottom);
}
.bottom-sheet--open {
  transform: translateY(0);
}
.bottom-sheet__handle {
  width: 36px;
  height: 4px;
  background: #D1D5DB;
  border-radius: 2px;
  margin: 8px auto 16px;
}
.bottom-sheet__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px 16px;
  border-bottom: 1px solid #E5E7EB;
}
.bottom-sheet__content {
  padding: 16px 20px;
}
```

---

## 8. PWA 디자인 규칙

### 8.1 manifest.json 관련

```json
{
  "name": "내 앱",
  "short_name": "앱",
  "theme_color": "#3B82F6",
  "background_color": "#FFFFFF",
  "display": "standalone",
  "orientation": "portrait-primary",
  "scope": "/",
  "start_url": "/",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

### 8.2 PWA UI 규칙

| 규칙 | 설명 |
|------|------|
| 오프라인 페이지 | 네트워크 없을 때 표시할 페이지 준비 |
| 설치 프롬프트 | 적절한 시점에 설치 유도 (첫 방문이 아닌 재방문 시) |
| 스플래시 화면 | theme_color + icon + name으로 자동 생성 |
| 상태바 | standalone 모드에서 상태바 영역 고려 |
| 뒤로가기 | 브라우저 뒤로가기 없으므로 앱 내 네비게이션 필수 |
| 풀스크린 | 주소창 없으므로 사이트 정보 접근 방법 제공 |

---

## 9. 모바일 폼 최적화

### 9.1 inputmode 속성

| inputmode | 표시되는 키보드 | 용도 |
|-----------|-------------|------|
| `text` | 일반 키보드 | 이름, 주소 |
| `email` | @ 포함 키보드 | 이메일 |
| `tel` | 숫자 다이얼패드 | 전화번호 |
| `url` | / . .com 포함 | URL |
| `numeric` | 숫자 키패드 | 숫자 입력 (인증번호) |
| `decimal` | 숫자 + 소수점 | 금액, 수량 |
| `search` | 검색(Enter → 검색) | 검색창 |
| `none` | 키보드 숨김 | 커스텀 키보드 사용 시 |

```html
<input type="text" inputmode="numeric" pattern="[0-9]*" placeholder="인증번호 6자리">
<input type="text" inputmode="decimal" placeholder="금액">
<input type="email" inputmode="email" autocomplete="email">
<input type="tel" inputmode="tel" autocomplete="tel">
```

### 9.2 autocomplete 속성

```html
<input autocomplete="name" name="name">           <!-- 이름 -->
<input autocomplete="email" name="email">          <!-- 이메일 -->
<input autocomplete="tel" name="phone">            <!-- 전화번호 -->
<input autocomplete="street-address" name="addr">  <!-- 주소 -->
<input autocomplete="postal-code" name="zip">      <!-- 우편번호 -->
<input autocomplete="cc-number" name="cardnum">    <!-- 카드번호 -->
<input autocomplete="cc-exp" name="cardexp">       <!-- 카드 만료일 -->
<input autocomplete="new-password" name="pw">      <!-- 새 비밀번호 -->
<input autocomplete="current-password" name="pw">  <!-- 현재 비밀번호 -->
<input autocomplete="one-time-code" name="otp">    <!-- OTP -->
```

### 9.3 모바일 폼 UX 규칙

| 규칙 | 이유 |
|------|------|
| 본문 16px 이상 | iOS에서 16px 미만이면 입력 시 자동 줌 |
| 레이블 위에 배치 | 모바일에서 좌측 레이블은 공간 낭비 |
| 싱글 컬럼 | 모바일에서 2컬럼 폼은 혼란 |
| 다음 필드 자동 포커스 | OTP, 카드번호 등 분할 입력 시 |
| 키보드 위 고정 CTA | 키보드가 올라와도 제출 버튼 보임 |
| 에러 즉시 피드백 | 제출 후가 아닌 입력 중 유효성 검사 |

```css
/* iOS 자동 줌 방지 */
input, select, textarea {
  font-size: 16px; /* 16px 이상 */
}

/* 키보드 위 고정 버튼 */
.fixed-bottom-cta {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
  background: #FFFFFF;
  border-top: 1px solid #E5E7EB;
  z-index: 30;
}
```

---

## 10. 뷰포트 단위

### 10.1 단위 비교

| 단위 | 설명 | 사용 시점 |
|------|------|----------|
| `vh` | 뷰포트 높이 (주소창 무시) | 데스크톱 전용 |
| `dvh` | Dynamic viewport (주소창 변화 반영) | 모바일 권장 |
| `svh` | Small viewport (주소창 표시 상태) | 최소 높이 보장 |
| `lvh` | Large viewport (주소창 숨김 상태) | 최대 높이 |
| `vw` | 뷰포트 너비 | 너비 기반 크기 |
| `dvw` | Dynamic viewport width | 모바일 권장 |

```css
/* 풀스크린 Hero — 모바일 주소창 대응 */
.hero {
  min-height: 100vh; /* 폴백 */
  min-height: 100dvh; /* 동적 뷰포트 */
}

/* 모바일 모달 — 주소창 고려 */
.modal {
  max-height: 90vh;
  max-height: 90dvh;
}

/* 스크롤 가능 영역 */
.scrollable-area {
  height: 100vh;
  height: 100dvh;
  overflow-y: auto;
}
```

---

## 11. 가로 모드 대응

```css
/* 가로 모드 감지 */
@media (orientation: landscape) and (max-height: 500px) {
  /* 모바일 가로 모드 */
  .hero { min-height: auto; padding: 24px; }
  .modal { max-height: 95dvh; }
  .bottom-bar { display: none; } /* 또는 축소 */
}

/* 태블릿 가로 모드 */
@media (orientation: landscape) and (min-width: 768px) {
  .sidebar { display: flex; }
  .hamburger { display: none; }
}
```

---

## 12. 폴더블/태블릿 대응

### 12.1 폴더블 디바이스

```css
/* 폴더블 — 접힌 상태 (작은 화면) */
@media (max-width: 523px) {
  /* 일반 모바일과 동일 */
}

/* 폴더블 — 펼친 상태 */
@media (min-width: 524px) and (max-width: 767px) {
  /* 넓은 모바일 / 작은 태블릿 */
  .grid { grid-template-columns: repeat(2, 1fr); }
}

/* 듀얼 스크린 (Surface Duo 등) */
@media (horizontal-viewport-segments: 2) {
  .dual-pane {
    display: grid;
    grid-template-columns: env(viewport-segment-width 0 0) env(viewport-segment-width 1 0);
    column-gap: env(viewport-segment-left 1 0);
  }
}
```

### 12.2 태블릿 최적화

| 패턴 | 설명 |
|------|------|
| Split View | 좌측 목록 + 우측 상세 (이메일, 메시징) |
| 사이드바 상시 표시 | 768px 이상에서 사이드바 고정 |
| 다중 컬럼 | 태블릿에서 2~3컬럼 그리드 |
| 모달 → 사이드 패널 | 태블릿에서 모달 대신 우측 패널 |
| 팝오버 | 태블릿에서 바텀시트 대신 팝오버 |

```css
/* 태블릿 Split View */
@media (min-width: 768px) {
  .split-view {
    display: grid;
    grid-template-columns: 320px 1fr;
    height: 100vh;
  }
  .split-view__list {
    border-right: 1px solid #E5E7EB;
    overflow-y: auto;
  }
  .split-view__detail {
    overflow-y: auto;
    padding: 24px;
  }
}
@media (max-width: 767px) {
  .split-view__detail {
    /* 모바일: 별도 페이지로 이동 */
    position: fixed;
    inset: 0;
    z-index: 10;
    background: #FFFFFF;
  }
}
```

---

## 13. 반응형 이미지

```html
<!-- srcset + sizes -->
<img
  src="image-800.jpg"
  srcset="image-400.jpg 400w, image-800.jpg 800w, image-1200.jpg 1200w"
  sizes="(max-width: 767px) 100vw, (max-width: 1023px) 50vw, 33vw"
  alt="제품 이미지"
  loading="lazy"
  decoding="async"
>

<!-- picture 태그 (아트 디렉션) -->
<picture>
  <source media="(min-width: 1024px)" srcset="hero-desktop.webp" type="image/webp">
  <source media="(min-width: 768px)" srcset="hero-tablet.webp" type="image/webp">
  <source srcset="hero-mobile.webp" type="image/webp">
  <img src="hero-mobile.jpg" alt="Hero 배너" loading="eager">
</picture>
```

```css
/* 반응형 이미지 기본 */
img {
  max-width: 100%;
  height: auto;
  display: block;
}
/* aspect-ratio */
.img-wrapper {
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border-radius: 12px;
}
.img-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

---

## 14. 모바일 성능 최적화

| 최적화 | 방법 |
|--------|------|
| 이미지 포맷 | WebP/AVIF 우선, JPEG/PNG 폴백 |
| 이미지 로딩 | `loading="lazy"` (뷰포트 밖) |
| 폰트 로딩 | `font-display: swap`, preload |
| CSS 최소화 | Critical CSS 인라인, 나머지 비동기 |
| JS 최소화 | Code splitting, tree shaking |
| 터치 지연 | `touch-action: manipulation` |
| 스크롤 성능 | `will-change: transform`, `contain: layout` |
| 애니메이션 | transform + opacity만 사용 (리페인트 방지) |

```html
<!-- Critical CSS 인라인 -->
<head>
  <style>
    /* 첫 화면에 필요한 CSS만 인라인 */
    body { margin: 0; font-family: system-ui; }
    .header { height: 64px; }
    .hero { min-height: 50vh; }
  </style>
  <!-- 나머지 CSS 비동기 로드 -->
  <link rel="preload" href="styles.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
</head>
```
