# 애니메이션/모션 백과사전

## 1. 모션 원칙

### 1.1 핵심 원칙

| 원칙 | 설명 | 예시 |
|------|------|------|
| 의미 있는 전환 | 상태 변화를 시각적으로 연결 | 카드 클릭 → 상세 페이지로 확장 |
| 주의 유도 | 중요한 변화에 시선 끌기 | 새 알림 뱃지 등장 |
| 피드백 | 사용자 행동에 대한 응답 | 버튼 클릭 시 눌림 효과 |
| 연속성 | 요소 간 관계 표현 | 목록 → 상세로 전환 시 이미지 연결 |
| 상태 표현 | 시스템 상태 시각화 | 로딩 스피너, 프로그레스 |
| 자연스러움 | 물리 법칙 모방 | 스프링 애니메이션, 관성 |

### 1.2 모션을 쓰면 안 되는 경우

| 상황 | 이유 |
|------|------|
| 정보 전달에 방해 | 텍스트 읽기를 방해하는 배경 애니메이션 |
| 빈번한 반복 | 매번 동일한 전환은 짜증 유발 |
| 느린 애니메이션 | 사용 흐름을 차단하는 1초+ 애니메이션 |
| 의미 없는 장식 | 목적 없이 요소가 움직임 |
| 접근성 무시 | prefers-reduced-motion 미대응 |

---

## 2. Easing 함수 레퍼런스

### 2.1 기본 Easing

| 이름 | cubic-bezier | 용도 |
|------|-------------|------|
| ease | (0.25, 0.1, 0.25, 1.0) | CSS 기본값 |
| ease-in | (0.42, 0, 1.0, 1.0) | 나가는 요소 (퇴장) |
| ease-out | (0, 0, 0.58, 1.0) | 들어오는 요소 (등장) |
| ease-in-out | (0.42, 0, 0.58, 1.0) | 화면 내 이동 |
| linear | (0, 0, 1, 1) | 로딩 프로그레스, 무한 회전 |

### 2.2 고급 Easing

```css
:root {
  /* 부드러운 감속 (가장 많이 사용) */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
  --ease-out-cubic: cubic-bezier(0.33, 1, 0.68, 1);

  /* 부드러운 가속-감속 */
  --ease-in-out-cubic: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-in-out-quart: cubic-bezier(0.76, 0, 0.24, 1);

  /* 강조 (오버슈트) */
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-in-back: cubic-bezier(0.36, 0, 0.66, -0.56);

  /* 바운스 */
  --ease-out-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* 스프링 (iOS 스타일) */
  --ease-spring: cubic-bezier(0.32, 0.72, 0, 1);
  --ease-spring-heavy: cubic-bezier(0.22, 0.68, 0, 1);
  --ease-spring-light: cubic-bezier(0.42, 0.97, 0.52, 1.02);

  /* Material Design 표준 */
  --md-standard: cubic-bezier(0.2, 0, 0, 1);
  --md-standard-decelerate: cubic-bezier(0, 0, 0, 1);
  --md-standard-accelerate: cubic-bezier(0.3, 0, 1, 1);
  --md-emphasized: cubic-bezier(0.2, 0, 0, 1);
  --md-emphasized-decelerate: cubic-bezier(0.05, 0.7, 0.1, 1);
  --md-emphasized-accelerate: cubic-bezier(0.3, 0, 0.8, 0.15);
}
```

### 2.3 Easing 선택 가이드

| 상황 | 추천 Easing |
|------|-----------|
| 등장 (화면 밖 → 안) | ease-out-expo, ease-out-quart |
| 퇴장 (화면 안 → 밖) | ease-in-cubic |
| 화면 내 이동 | ease-in-out-cubic, ease-in-out-quart |
| 크기 변화 | ease-out-expo |
| 투명도 변화 | ease-out (간단하게) |
| 토글/스위치 | ease-spring |
| 모달 등장 | ease-out-expo 또는 spring |
| 모달 퇴장 | ease-in-cubic (빠르게) |
| 드래그 후 놓기 | spring (바운스) |
| 스크롤 연동 | linear |

---

## 3. 마이크로인터랙션 패턴

### 3.1 버튼 클릭

```css
/* 기본 클릭 피드백 */
.btn {
  transition: all 0.15s ease;
}
.btn:hover {
  background: var(--hover-color);
}
.btn:active {
  transform: scale(0.97);
  transition-duration: 0.05s;
}

/* 좋아요 버튼 */
.like-btn {
  transition: transform 0.15s ease;
}
.like-btn:active {
  transform: scale(0.85);
}
.like-btn--liked {
  animation: like-pop 0.3s ease;
}
@keyframes like-pop {
  0% { transform: scale(1); }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

/* 복사 버튼 피드백 */
.copy-btn--copied {
  animation: copied 0.3s ease;
}
@keyframes copied {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}
```

### 3.2 토글 스위치

```css
.switch__thumb {
  transition: transform 0.2s cubic-bezier(0.32, 0.72, 0, 1);
}
.switch--on .switch__thumb {
  transform: translateX(20px);
}
.switch__track {
  transition: background-color 0.2s ease;
}
```

### 3.3 로딩 스피너 변형

```css
/* 기본 회전 스피너 */
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #E5E7EB;
  border-top-color: #3B82F6;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 점 3개 로딩 */
.dots-loading {
  display: flex;
  gap: 4px;
}
.dots-loading__dot {
  width: 8px;
  height: 8px;
  background: #3B82F6;
  border-radius: 50%;
  animation: dot-bounce 1.4s infinite ease-in-out both;
}
.dots-loading__dot:nth-child(1) { animation-delay: -0.32s; }
.dots-loading__dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 펄스 로딩 */
.pulse-loading {
  width: 40px;
  height: 40px;
  background: #3B82F6;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0% { transform: scale(0); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

/* 바 로딩 (진행률 불명) */
.bar-loading {
  width: 100%;
  height: 3px;
  background: #E5E7EB;
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}
.bar-loading::after {
  content: "";
  position: absolute;
  top: 0;
  left: -40%;
  width: 40%;
  height: 100%;
  background: #3B82F6;
  border-radius: 2px;
  animation: indeterminate 1.5s ease-in-out infinite;
}
@keyframes indeterminate {
  0% { left: -40%; }
  100% { left: 100%; }
}
```

### 3.4 체크박스 체크 애니메이션

```css
.checkbox-animated input:checked + .checkmark {
  animation: check-pop 0.3s ease;
}
.checkbox-animated .checkmark-path {
  stroke-dasharray: 24;
  stroke-dashoffset: 24;
  transition: stroke-dashoffset 0.3s ease 0.1s;
}
.checkbox-animated input:checked + .checkmark .checkmark-path {
  stroke-dashoffset: 0;
}
@keyframes check-pop {
  0% { transform: scale(1); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}
```

### 3.5 카운터 숫자 애니메이션

```css
.counter {
  transition: all 0.3s ease;
}
/* CSS Counter Animation (순수 CSS) */
@property --num {
  syntax: '<integer>';
  initial-value: 0;
  inherits: false;
}
.animated-number {
  --num: 0;
  animation: count-up 2s ease forwards;
  counter-reset: num var(--num);
}
.animated-number::after {
  content: counter(num);
}
@keyframes count-up {
  from { --num: 0; }
  to { --num: 1234; }
}
```

---

## 4. 페이지 전환

### 4.1 기본 전환

```css
/* 페이드 */
.page-enter { opacity: 0; }
.page-enter-active {
  opacity: 1;
  transition: opacity 0.3s ease-out;
}
.page-exit { opacity: 1; }
.page-exit-active {
  opacity: 0;
  transition: opacity 0.2s ease-in;
}

/* 슬라이드 (좌→우) */
.slide-enter {
  transform: translateX(100%);
}
.slide-enter-active {
  transform: translateX(0);
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}
.slide-exit {
  transform: translateX(0);
}
.slide-exit-active {
  transform: translateX(-30%);
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}

/* 줌 (카드 → 상세) */
.zoom-enter {
  opacity: 0;
  transform: scale(0.95);
}
.zoom-enter-active {
  opacity: 1;
  transform: scale(1);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
```

### 4.2 View Transitions API (네이티브)

```css
/* 기본 페이지 전환 */
::view-transition-old(root) {
  animation: fade-out 0.2s ease-in forwards;
}
::view-transition-new(root) {
  animation: fade-in 0.3s ease-out;
}

/* 요소 연결 전환 */
.card-image {
  view-transition-name: card-image;
}
::view-transition-old(card-image),
::view-transition-new(card-image) {
  animation-duration: 0.3s;
  animation-timing-function: cubic-bezier(0.32, 0.72, 0, 1);
}
```

---

## 5. 스크롤 애니메이션

### 5.1 Scroll-driven Animations (CSS)

```css
/* 스크롤에 따라 나타나기 */
.reveal {
  opacity: 0;
  transform: translateY(20px);
  animation: reveal linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 100%;
}
@keyframes reveal {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 스크롤 프로그레스 바 */
.scroll-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: #3B82F6;
  transform-origin: left;
  animation: scroll-progress linear;
  animation-timeline: scroll();
}
@keyframes scroll-progress {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}
```

### 5.2 Intersection Observer 패턴

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, {
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px'
});

document.querySelectorAll('.animate-on-scroll').forEach(el => {
  observer.observe(el);
});
```

```css
.animate-on-scroll {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s ease-out, transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.animate-on-scroll.visible {
  opacity: 1;
  transform: translateY(0);
}

/* 순차 등장 (stagger) */
.animate-on-scroll:nth-child(1) { transition-delay: 0s; }
.animate-on-scroll:nth-child(2) { transition-delay: 0.1s; }
.animate-on-scroll:nth-child(3) { transition-delay: 0.2s; }
.animate-on-scroll:nth-child(4) { transition-delay: 0.3s; }
```

### 5.3 패럴랙스

```css
/* 순수 CSS 패럴랙스 */
.parallax-container {
  perspective: 1px;
  height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
}
.parallax-bg {
  transform: translateZ(-1px) scale(2);
}
.parallax-fg {
  transform: translateZ(0);
}

/* 성능: transform만 사용, will-change: transform 추가 */
```

---

## 6. 스켈레톤 로딩 애니메이션

```css
.skeleton {
  background: linear-gradient(
    90deg,
    #E5E7EB 25%,
    #F3F4F6 50%,
    #E5E7EB 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: 8px;
}
@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 다크모드 스켈레톤 */
[data-theme="dark"] .skeleton {
  background: linear-gradient(
    90deg,
    #334155 25%,
    #475569 50%,
    #334155 75%
  );
  background-size: 200% 100%;
}

/* 스켈레톤 레이아웃 */
.skeleton-card {
  padding: 24px;
}
.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
}
.skeleton-title {
  height: 20px;
  width: 70%;
  margin-bottom: 12px;
}
.skeleton-text {
  height: 14px;
  margin-bottom: 8px;
}
.skeleton-text:last-child {
  width: 60%;
}
```

---

## 7. iOS 스프링 애니메이션

```css
:root {
  /* iOS-like 스프링 값 */
  --spring-bounce: cubic-bezier(0.32, 0.72, 0, 1);
  --spring-snappy: cubic-bezier(0.25, 0.46, 0.45, 0.94);
  --spring-gentle: cubic-bezier(0.42, 0, 0.58, 1);
  --spring-heavy: cubic-bezier(0.22, 0.68, 0, 1.71);

  /* 시트/모달 등장 */
  --sheet-enter: cubic-bezier(0.32, 0.72, 0, 1);
  --sheet-exit: cubic-bezier(0.32, 0.72, 0, 1);

  /* 네비게이션 전환 */
  --nav-push: cubic-bezier(0.36, 0.66, 0.04, 1);
  --nav-pop: cubic-bezier(0.36, 0.66, 0.04, 1);
}

/* iOS 바텀 시트 */
.ios-sheet {
  transform: translateY(100%);
  transition: transform 0.5s var(--sheet-enter);
}
.ios-sheet--open {
  transform: translateY(0);
}

/* iOS 네비게이션 Push */
.page-next-enter {
  transform: translateX(100%);
  transition: transform 0.35s var(--nav-push);
}
.page-next-enter-active {
  transform: translateX(0);
}
.page-current-exit {
  transform: translateX(0);
  transition: transform 0.35s var(--nav-push);
}
.page-current-exit-active {
  transform: translateX(-30%);
}
```

---

## 8. 듀레이션 가이드

| 범주 | 시간 | 용도 | 예시 |
|------|------|------|------|
| 즉각 | 50~100ms | 직접 피드백 | 버튼 상태, 호버, 토글 |
| 빠름 | 150~200ms | 간단한 전환 | 드롭다운, 툴팁, 페이드 |
| 보통 | 250~350ms | 중간 전환 | 모달, 사이드바, 탭 전환 |
| 느림 | 400~500ms | 큰 전환 | 페이지 전환, 풀스크린 모달 |
| 매우 느림 | 600~1000ms | 강조, 첫 등장 | Hero 섹션, 온보딩, 로고 |

### 8.1 규칙

| 규칙 | 설명 |
|------|------|
| 크기 비례 | 이동 거리가 길수록 시간을 늘림 |
| 등장 > 퇴장 | 등장 300ms → 퇴장 200ms (퇴장은 더 빠르게) |
| 300ms 이하 권장 | 대부분의 UI 전환은 300ms 이내 |
| 사용 빈도 반비례 | 자주 사용하는 인터랙션일수록 짧게 |
| 모바일은 더 짧게 | 데스크톱 대비 70~80% 듀레이션 |

```css
:root {
  --duration-instant: 50ms;
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
  --duration-slower: 600ms;
}
```

---

## 9. prefers-reduced-motion 대응

```css
/* 방법 1: 모든 애니메이션 비활성화 */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* 방법 2: 세밀한 제어 (권장) */
@media (prefers-reduced-motion: reduce) {
  /* 장식적 애니메이션만 제거 */
  .parallax { transform: none !important; }
  .floating-icon { animation: none; }
  .scroll-reveal { opacity: 1; transform: none; }

  /* 기능적 전환은 유지하되 간소화 */
  .modal {
    transition: opacity 0.01ms;
    /* transform 전환 제거, opacity만 유지 */
  }
  .tab-content {
    transition: none;
  }
}

/* 방법 3: 모션 선호 사용자에게만 애니메이션 적용 */
@media (prefers-reduced-motion: no-preference) {
  .animate-on-scroll {
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.6s ease;
  }
  .animate-on-scroll.visible {
    opacity: 1;
    transform: none;
  }
}
```

### 9.1 JavaScript 감지

```javascript
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

if (prefersReducedMotion.matches) {
  // 애니메이션 간소화 또는 비활성화
}

// 실시간 변경 감지
prefersReducedMotion.addEventListener('change', (e) => {
  if (e.matches) {
    // 애니메이션 비활성화
  } else {
    // 애니메이션 활성화
  }
});
```

---

## 10. Framer Motion / GSAP 패턴

### 10.1 Framer Motion (React)

```jsx
import { motion, AnimatePresence } from 'framer-motion';

// 기본 등장/퇴장
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -10 }}
  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
>
  콘텐츠
</motion.div>

// 리스트 순차 등장
<motion.ul>
  {items.map((item, i) => (
    <motion.li
      key={item.id}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: i * 0.05, duration: 0.3 }}
    >
      {item.name}
    </motion.li>
  ))}
</motion.ul>

// 스프링 애니메이션
<motion.div
  animate={{ scale: isOpen ? 1 : 0.95 }}
  transition={{ type: "spring", stiffness: 300, damping: 30 }}
/>

// 드래그
<motion.div
  drag="x"
  dragConstraints={{ left: -100, right: 100 }}
  dragElastic={0.2}
/>

// 레이아웃 애니메이션
<motion.div layout transition={{ duration: 0.3 }} />
```

### 10.2 GSAP (범용)

```javascript
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

// 기본 애니메이션
gsap.from('.element', {
  opacity: 0,
  y: 30,
  duration: 0.6,
  ease: 'power3.out'
});

// 순차 등장
gsap.from('.card', {
  opacity: 0,
  y: 30,
  duration: 0.6,
  stagger: 0.1,
  ease: 'power3.out'
});

// 스크롤 연동
gsap.from('.section', {
  scrollTrigger: {
    trigger: '.section',
    start: 'top 80%',
    end: 'bottom 20%',
    toggleActions: 'play none none reverse'
  },
  opacity: 0,
  y: 50,
  duration: 0.8,
  ease: 'power3.out'
});

// 타임라인
const tl = gsap.timeline();
tl.from('.hero-title', { opacity: 0, y: 30, duration: 0.6 })
  .from('.hero-desc', { opacity: 0, y: 20, duration: 0.4 }, '-=0.2')
  .from('.hero-cta', { opacity: 0, scale: 0.9, duration: 0.3 }, '-=0.1');
```

---

## 11. 성능 최적화

### 11.1 GPU 가속 가능한 속성 (리페인트 없음)

| 안전 | 위험 (리페인트/리플로우) |
|------|---------------------|
| `transform` | `width`, `height` |
| `opacity` | `margin`, `padding` |
| `filter` | `top`, `left`, `right`, `bottom` |
| `clip-path` | `border`, `box-shadow` |
| `background-color` (부분) | `font-size`, `line-height` |

```css
/* 좋은 예: transform + opacity만 애니메이션 */
.good-animation {
  transform: translateX(0);
  opacity: 1;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

/* 나쁜 예: layout 속성 애니메이션 */
.bad-animation {
  left: 0;
  width: 200px;
  transition: left 0.3s ease, width 0.3s ease; /* 리플로우 유발 */
}
```

### 11.2 will-change

```css
/* 곧 애니메이션될 요소에 미리 선언 */
.will-animate {
  will-change: transform, opacity;
}
/* 주의: 너무 많은 요소에 사용하면 메모리 낭비 */
/* 애니메이션 완료 후 제거 권장 */
```

### 11.3 contain

```css
/* 레이아웃 격리 */
.isolated-component {
  contain: layout style paint;
}
/* 이 요소 내부 변화가 외부에 영향을 주지 않음 → 성능 향상 */
```
