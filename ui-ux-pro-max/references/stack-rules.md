# 기술 스택별 구현 규칙

## 1. Tailwind CSS 규칙

### 1.1 유틸리티 클래스 조합

```html
<!-- 버튼 — Primary -->
<button class="inline-flex items-center justify-center gap-2 h-10 px-4 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 active:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
  버튼 텍스트
</button>

<!-- 버튼 — Secondary -->
<button class="inline-flex items-center justify-center gap-2 h-10 px-4 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 active:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 transition-colors">
  버튼 텍스트
</button>

<!-- 입력 필드 -->
<input class="w-full h-10 px-3 text-sm text-gray-900 bg-white border border-gray-300 rounded-lg outline-none hover:border-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 placeholder:text-gray-400 disabled:bg-gray-50 disabled:text-gray-500 transition-colors" placeholder="입력해주세요">

<!-- 카드 -->
<div class="bg-white border border-gray-200 rounded-xl p-6 hover:border-gray-300 hover:shadow-md transition-all">
  <h3 class="text-lg font-semibold text-gray-900 mb-2">카드 제목</h3>
  <p class="text-sm text-gray-600 leading-relaxed">카드 설명</p>
</div>

<!-- 뱃지 -->
<span class="inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full bg-blue-50 text-blue-700">
  뱃지
</span>

<!-- 아바타 -->
<div class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-sm font-semibold text-gray-600">
  AB
</div>

<!-- 모달 오버레이 -->
<div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
  <div class="bg-white rounded-2xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
    <!-- 모달 내용 -->
  </div>
</div>

<!-- 사이드바 항목 -->
<a class="flex items-center gap-3 px-3 py-2 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors">
  <svg class="w-5 h-5 shrink-0"><!-- 아이콘 --></svg>
  <span>메뉴 항목</span>
</a>

<!-- 테이블 -->
<div class="overflow-x-auto border border-gray-200 rounded-xl">
  <table class="w-full">
    <thead>
      <tr class="bg-gray-50 border-b border-gray-200">
        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">이름</th>
        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">상태</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      <tr class="hover:bg-gray-50 transition-colors">
        <td class="px-4 py-3 text-sm text-gray-900">데이터</td>
        <td class="px-4 py-3 text-sm">
          <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-green-50 text-green-700">활성</span>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### 1.2 다크 모드

```html
<!-- class 기반 다크 모드 (tailwind.config의 darkMode: 'class') -->
<div class="bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 border-gray-200 dark:border-gray-700">
  <h2 class="text-gray-900 dark:text-white">제목</h2>
  <p class="text-gray-600 dark:text-gray-400">본문</p>
</div>

<!-- 테마 토글 버튼 -->
<button onclick="document.documentElement.classList.toggle('dark')" class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
  <svg class="w-5 h-5 dark:hidden"><!-- 태양 아이콘 --></svg>
  <svg class="w-5 h-5 hidden dark:block"><!-- 달 아이콘 --></svg>
</button>
```

### 1.3 반응형 패턴

```html
<!-- 반응형 그리드 -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
  <!-- 카드들 -->
</div>

<!-- 반응형 사이드바 -->
<aside class="fixed inset-y-0 left-0 w-64 bg-white border-r transform -translate-x-full lg:translate-x-0 lg:static transition-transform z-30">
  <!-- 사이드바 내용 -->
</aside>

<!-- 반응형 타이포그래피 -->
<h1 class="text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-bold">
  반응형 제목
</h1>

<!-- 모바일에서만 표시 -->
<div class="block lg:hidden">모바일 전용</div>
<!-- 데스크톱에서만 표시 -->
<div class="hidden lg:block">데스크톱 전용</div>
```

### 1.4 커스텀 확장

```html
<!-- @apply로 재사용 클래스 생성 (styles.css) -->
<style>
@layer components {
  .btn-primary {
    @apply inline-flex items-center justify-center gap-2 h-10 px-4 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 active:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors;
  }
  .btn-secondary {
    @apply inline-flex items-center justify-center gap-2 h-10 px-4 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 active:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 transition-colors;
  }
  .input {
    @apply w-full h-10 px-3 text-sm text-gray-900 bg-white border border-gray-300 rounded-lg outline-none hover:border-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 placeholder:text-gray-400 transition-colors;
  }
  .card {
    @apply bg-white border border-gray-200 rounded-xl p-6;
  }
}
</style>
```

---

## 2. React 컴포넌트 패턴

### 2.1 Compound Component

```tsx
// Tabs 컴포넌트 — Compound 패턴
import { createContext, useContext, useState, ReactNode } from 'react';

interface TabsContextType {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextType | null>(null);

function Tabs({ defaultTab, children }: { defaultTab: string; children: ReactNode }) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div>{children}</div>
    </TabsContext.Provider>
  );
}

function TabList({ children }: { children: ReactNode }) {
  return <div className="flex gap-0 border-b border-gray-200">{children}</div>;
}

function Tab({ value, children }: { value: string; children: ReactNode }) {
  const ctx = useContext(TabsContext)!;
  const isActive = ctx.activeTab === value;
  return (
    <button
      role="tab"
      aria-selected={isActive}
      className={`px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors ${
        isActive ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
      }`}
      onClick={() => ctx.setActiveTab(value)}
    >
      {children}
    </button>
  );
}

function TabPanel({ value, children }: { value: string; children: ReactNode }) {
  const ctx = useContext(TabsContext)!;
  if (ctx.activeTab !== value) return null;
  return <div role="tabpanel" className="py-4">{children}</div>;
}

Tabs.List = TabList;
Tabs.Tab = Tab;
Tabs.Panel = TabPanel;

// 사용법
<Tabs defaultTab="tab1">
  <Tabs.List>
    <Tabs.Tab value="tab1">탭 1</Tabs.Tab>
    <Tabs.Tab value="tab2">탭 2</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel value="tab1">탭 1 내용</Tabs.Panel>
  <Tabs.Panel value="tab2">탭 2 내용</Tabs.Panel>
</Tabs>
```

### 2.2 Custom Hooks

```tsx
// useMediaQuery
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [query]);
  return matches;
}
// 사용: const isMobile = useMediaQuery('(max-width: 767px)');

// useTheme
function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || saved === 'light') return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggle = () => setTheme(t => t === 'light' ? 'dark' : 'light');
  return { theme, toggle };
}

// useIntersectionObserver (스크롤 등장)
function useIntersectionObserver(options?: IntersectionObserverInit) {
  const ref = useRef<HTMLElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsVisible(true);
        observer.unobserve(el);
      }
    }, { threshold: 0.1, ...options });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return { ref, isVisible };
}
```

### 2.3 forwardRef + 접근성

```tsx
import { forwardRef, ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, disabled, children, className, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2';

    const variantClasses = {
      primary: 'bg-blue-500 text-white hover:bg-blue-600 active:bg-blue-700 focus-visible:outline-blue-500',
      secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 active:bg-gray-100 focus-visible:outline-blue-500',
      ghost: 'text-gray-700 hover:bg-gray-100 active:bg-gray-200 focus-visible:outline-blue-500',
      destructive: 'bg-red-500 text-white hover:bg-red-600 active:bg-red-700 focus-visible:outline-red-500',
    };

    const sizeClasses = {
      sm: 'h-8 px-3 text-xs',
      md: 'h-10 px-4 text-sm',
      lg: 'h-12 px-6 text-base',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        aria-busy={loading}
        className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${disabled || loading ? 'opacity-50 cursor-not-allowed' : ''} ${className || ''}`}
        {...props}
      >
        {loading && <span className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

---

## 3. Next.js App Router UI 패턴

### 3.1 레이아웃 구조

```tsx
// app/layout.tsx — 루트 레이아웃
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 ml-0 lg:ml-60">{children}</main>
        </div>
      </body>
    </html>
  );
}

// app/(dashboard)/layout.tsx — 대시보드 레이아웃
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <TopBar />
      <div className="p-6">{children}</div>
    </div>
  );
}
```

### 3.2 서버/클라이언트 컴포넌트 분리

```tsx
// 서버 컴포넌트 (기본) — 데이터 페칭, 정적 UI
// app/dashboard/page.tsx
export default async function DashboardPage() {
  const data = await fetchDashboardData(); // 서버에서 직접 fetch
  return (
    <div>
      <h1>대시보드</h1>
      <StatCards data={data.stats} />        {/* 서버 컴포넌트 */}
      <InteractiveChart data={data.chart} /> {/* 클라이언트 컴포넌트 */}
    </div>
  );
}

// 클라이언트 컴포넌트 — 인터랙션, 상태, 브라우저 API
// components/InteractiveChart.tsx
'use client';

import { useState } from 'react';

export function InteractiveChart({ data }: { data: ChartData }) {
  const [range, setRange] = useState('7d');
  return (
    <div>
      <select value={range} onChange={e => setRange(e.target.value)}>
        <option value="7d">7일</option>
        <option value="30d">30일</option>
      </select>
      {/* 차트 렌더링 */}
    </div>
  );
}
```

### 3.3 로딩/에러 UI

```tsx
// app/dashboard/loading.tsx — 자동 스켈레톤
export default function Loading() {
  return (
    <div className="p-6 space-y-6 animate-pulse">
      <div className="grid grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 bg-gray-200 rounded-xl" />
        ))}
      </div>
      <div className="h-64 bg-gray-200 rounded-xl" />
    </div>
  );
}

// app/dashboard/error.tsx — 에러 바운더리
'use client';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <h2 className="text-lg font-semibold text-gray-900 mb-2">문제가 발생했습니다</h2>
      <p className="text-sm text-gray-600 mb-4">{error.message}</p>
      <button onClick={reset} className="btn-primary">다시 시도</button>
    </div>
  );
}
```

---

## 4. Vue 3 Composition API UI 패턴

### 4.1 컴포넌트 구조

```vue
<!-- BaseButton.vue -->
<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false,
})

const emit = defineEmits<{ click: [event: MouseEvent] }>()

const classes = computed(() => {
  const base = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors'
  const variants: Record<string, string> = {
    primary: 'bg-blue-500 text-white hover:bg-blue-600',
    secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50',
    ghost: 'text-gray-700 hover:bg-gray-100',
    destructive: 'bg-red-500 text-white hover:bg-red-600',
  }
  const sizes: Record<string, string> = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
  }
  return `${base} ${variants[props.variant]} ${sizes[props.size]}`
})
</script>

<template>
  <button
    :class="classes"
    :disabled="disabled || loading"
    :aria-busy="loading"
    @click="emit('click', $event)"
  >
    <span v-if="loading" class="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
    <slot />
  </button>
</template>
```

### 4.2 Composable (Custom Hook)

```typescript
// composables/useTheme.ts
export function useTheme() {
  const theme = ref<'light' | 'dark'>(
    localStorage.getItem('theme') as 'light' | 'dark' || 'light'
  )

  watch(theme, (val) => {
    document.documentElement.dataset.theme = val
    localStorage.setItem('theme', val)
  }, { immediate: true })

  function toggle() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return { theme, toggle }
}
```

---

## 5. Vanilla HTML/CSS/JS 패턴

### 5.1 CDN 기반 (빌드 도구 없음)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>내 앱</title>

  <!-- 폰트 -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">

  <!-- 아이콘 (Lucide) -->
  <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>

  <!-- CSS (인라인 또는 외부 파일) -->
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <!-- Skip Link -->
  <a href="#main" class="skip-link">메인 콘텐츠로 건너뛰기</a>

  <!-- 앱 구조 -->
  <div class="app">
    <nav class="sidebar" id="sidebar"><!-- 사이드바 --></nav>
    <div class="main-wrapper">
      <header class="topbar"><!-- 상단바 --></header>
      <main id="main" class="content"><!-- 메인 콘텐츠 --></main>
    </div>
  </div>

  <script src="app.js"></script>
  <script>lucide.createIcons();</script>
</body>
</html>
```

### 5.2 Vanilla JS 패턴

```javascript
// 테마 토글
function initTheme() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = saved || (prefersDark ? 'dark' : 'light');
  document.documentElement.dataset.theme = theme;
}

function toggleTheme() {
  const current = document.documentElement.dataset.theme;
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('theme', next);
}

// 모달
function openModal(id) {
  const modal = document.getElementById(id);
  modal.hidden = false;
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  // 포커스 트랩 설정
  const focusable = modal.querySelectorAll('button, input, a[href], [tabindex]:not([tabindex="-1"])');
  if (focusable.length) focusable[0].focus();
}

function closeModal(id) {
  const modal = document.getElementById(id);
  modal.hidden = true;
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

// 탭
function initTabs(container) {
  const tabs = container.querySelectorAll('[role="tab"]');
  const panels = container.querySelectorAll('[role="tabpanel"]');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.setAttribute('aria-selected', 'false'));
      panels.forEach(p => p.hidden = true);
      tab.setAttribute('aria-selected', 'true');
      const panel = document.getElementById(tab.getAttribute('aria-controls'));
      if (panel) panel.hidden = false;
    });
  });
}

// 토스트 알림
function showToast(message, type = 'info', duration = 3000) {
  const container = document.getElementById('toast-container') || createToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.setAttribute('role', 'alert');
  toast.textContent = message;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('toast--visible'));
  setTimeout(() => {
    toast.classList.remove('toast--visible');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function createToastContainer() {
  const container = document.createElement('div');
  container.id = 'toast-container';
  container.className = 'fixed top-4 right-4 z-[80] flex flex-col gap-2';
  document.body.appendChild(container);
  return container;
}
```

---

## 6. CSS Modules vs Styled Components vs CSS-in-JS

### 6.1 비교

| 방식 | 장점 | 단점 | 적합 |
|------|------|------|------|
| CSS Modules | 스코프 자동, 빌드타임, 성능 좋음 | JS에서 조건부 스타일 불편 | Next.js, Vite |
| Tailwind CSS | 빠른 개발, 일관된 토큰, 번들 작음 | 긴 클래스명, 학습 곡선 | 대부분의 프로젝트 |
| Styled Components | 동적 스타일, 테마 내장 | 런타임 비용, SSR 복잡 | 동적 테마 필요 시 |
| CSS Variables | 네이티브, 런타임 변경, 성능 | 복잡한 조건부 불가 | 테마 전환, 디자인 토큰 |
| Vanilla CSS | 의존성 없음, 가장 빠름 | 스코프 관리 수동 | 소규모, 빌드 없는 프로젝트 |

### 6.2 CSS Modules 사용법

```css
/* Button.module.css */
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.15s ease;
}
.primary {
  composes: button;
  background: #3B82F6;
  color: #FFFFFF;
}
.primary:hover {
  background: #2563EB;
}
```

```tsx
import styles from './Button.module.css';

function Button({ variant = 'primary', children }) {
  return <button className={styles[variant]}>{children}</button>;
}
```

---

## 7. SVG 아이콘 통합 방법

### 7.1 인라인 SVG (가장 유연)

```html
<button class="btn-icon" aria-label="검색">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <path d="m21 21-4.3-4.3"/>
  </svg>
</button>
```

### 7.2 SVG Sprite

```html
<!-- sprite.svg -->
<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
  <symbol id="icon-search" viewBox="0 0 24 24">
    <circle cx="11" cy="11" r="8" fill="none" stroke="currentColor" stroke-width="2"/>
    <path d="m21 21-4.3-4.3" fill="none" stroke="currentColor" stroke-width="2"/>
  </symbol>
  <symbol id="icon-home" viewBox="0 0 24 24">
    <!-- 홈 아이콘 path -->
  </symbol>
</svg>

<!-- 사용 -->
<svg width="20" height="20"><use href="sprite.svg#icon-search"/></svg>
```

### 7.3 React 컴포넌트

```tsx
// 아이콘 컴포넌트
interface IconProps {
  name: string;
  size?: number;
  className?: string;
}

function Icon({ name, size = 20, className }: IconProps) {
  return (
    <svg width={size} height={size} className={className}>
      <use href={`/icons/sprite.svg#${name}`} />
    </svg>
  );
}

// 사용
<Icon name="search" size={20} className="text-gray-500" />
```

---

## 8. 이미지 최적화

### 8.1 포맷 선택

| 포맷 | 용도 | 장점 |
|------|------|------|
| WebP | 사진, 일반 이미지 | JPEG 대비 25~34% 작음 |
| AVIF | 사진, 고품질 | WebP보다 20% 더 작음 |
| SVG | 아이콘, 로고, 일러스트 | 무한 확대, 매우 작음 |
| PNG | 투명 배경 필요 시 | 무손실, 투명 지원 |
| JPEG | 사진 폴백 | 최고 호환성 |

### 8.2 반응형 이미지

```html
<!-- 최적: picture + source -->
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <img src="image.jpg" alt="설명" loading="lazy" decoding="async" width="800" height="600">
</picture>

<!-- srcset + sizes -->
<img
  srcset="image-400.webp 400w, image-800.webp 800w, image-1200.webp 1200w"
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
  src="image-800.jpg"
  alt="설명"
  loading="lazy"
  decoding="async"
  width="800"
  height="600"
>
```

### 8.3 이미지 CSS

```css
/* 반응형 이미지 기본 */
img {
  max-width: 100%;
  height: auto;
  display: block;
}

/* 비율 유지 컨테이너 */
.img-container {
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border-radius: 12px;
  background: #E5E7EB; /* 로딩 중 배경 */
}
.img-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}
.img-container:hover img {
  transform: scale(1.05);
}

/* Next.js Image 최적화 */
/* <Image src={...} width={800} height={600} quality={75} placeholder="blur" /> */
```

### 8.4 이미지 성능 체크리스트

```
[ ] LCP 이미지에 loading="eager" + fetchpriority="high"
[ ] 뷰포트 밖 이미지에 loading="lazy"
[ ] width/height 속성으로 CLS 방지
[ ] WebP/AVIF 포맷 제공
[ ] srcset으로 적절한 크기 전달
[ ] 장식 이미지는 CSS background 사용
[ ] 아이콘은 SVG 사용
```
