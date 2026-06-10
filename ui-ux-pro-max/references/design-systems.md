# 디자인 시스템 구축 백과사전

## 1. 디자인 토큰 구조

### 1.1 3단계 토큰 체계

```
Primitive (원시) → Semantic (의미) → Component (컴포넌트)

예시:
Primitive:  blue-500 = #3B82F6
Semantic:   color-primary = blue-500
Component:  button-bg-primary = color-primary
```

### 1.2 Primitive 토큰 (Global)

```css
:root {
  /* === 색상 원시 토큰 === */
  --blue-50: #EFF6FF;
  --blue-100: #DBEAFE;
  --blue-200: #BFDBFE;
  --blue-300: #93C5FD;
  --blue-400: #60A5FA;
  --blue-500: #3B82F6;
  --blue-600: #2563EB;
  --blue-700: #1D4ED8;
  --blue-800: #1E40AF;
  --blue-900: #1E3A8A;

  --gray-50: #F9FAFB;
  --gray-100: #F3F4F6;
  --gray-200: #E5E7EB;
  --gray-300: #D1D5DB;
  --gray-400: #9CA3AF;
  --gray-500: #6B7280;
  --gray-600: #4B5563;
  --gray-700: #374151;
  --gray-800: #1F2937;
  --gray-900: #111827;

  --green-500: #10B981;
  --red-500: #EF4444;
  --yellow-500: #F59E0B;

  /* === 크기 원시 토큰 === */
  --size-0: 0px;
  --size-1: 4px;
  --size-2: 8px;
  --size-3: 12px;
  --size-4: 16px;
  --size-5: 20px;
  --size-6: 24px;
  --size-8: 32px;
  --size-10: 40px;
  --size-12: 48px;
  --size-16: 64px;
  --size-20: 80px;
  --size-24: 96px;

  /* === 폰트 크기 원시 토큰 === */
  --font-size-xs: 0.75rem;   /* 12px */
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-md: 1rem;      /* 16px */
  --font-size-lg: 1.125rem;  /* 18px */
  --font-size-xl: 1.25rem;   /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 1.875rem; /* 30px */
  --font-size-4xl: 2.25rem;  /* 36px */
  --font-size-5xl: 3rem;     /* 48px */

  /* === 보더 라디우스 원시 토큰 === */
  --radius-none: 0px;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 24px;
  --radius-full: 9999px;
}
```

### 1.3 Semantic 토큰 (Alias)

```css
:root {
  /* === 색상 의미 토큰 === */
  --color-primary: var(--blue-500);
  --color-primary-hover: var(--blue-600);
  --color-primary-active: var(--blue-700);
  --color-primary-light: var(--blue-50);

  --color-secondary: var(--gray-600);
  --color-secondary-hover: var(--gray-700);

  --color-success: var(--green-500);
  --color-warning: var(--yellow-500);
  --color-error: var(--red-500);
  --color-info: var(--blue-500);

  --color-bg-page: var(--gray-50);
  --color-bg-card: #FFFFFF;
  --color-bg-elevated: #FFFFFF;
  --color-bg-overlay: rgba(0, 0, 0, 0.5);

  --color-text-primary: var(--gray-900);
  --color-text-secondary: var(--gray-600);
  --color-text-tertiary: var(--gray-500);
  --color-text-disabled: var(--gray-400);
  --color-text-on-primary: #FFFFFF;

  --color-border: var(--gray-200);
  --color-border-hover: var(--gray-300);
  --color-border-focus: var(--blue-500);

  /* === 간격 의미 토큰 === */
  --spacing-xs: var(--size-1);   /* 4px */
  --spacing-sm: var(--size-2);   /* 8px */
  --spacing-md: var(--size-4);   /* 16px */
  --spacing-lg: var(--size-6);   /* 24px */
  --spacing-xl: var(--size-8);   /* 32px */
  --spacing-2xl: var(--size-12); /* 48px */
  --spacing-3xl: var(--size-16); /* 64px */
  --spacing-4xl: var(--size-24); /* 96px */

  /* === 보더 라디우스 의미 토큰 === */
  --radius-button: var(--radius-md);
  --radius-card: var(--radius-lg);
  --radius-modal: var(--radius-xl);
  --radius-input: var(--radius-md);
  --radius-badge: var(--radius-full);
  --radius-avatar: var(--radius-full);
}
```

### 1.4 Component 토큰

```css
:root {
  /* === 버튼 === */
  --btn-height-sm: 32px;
  --btn-height-md: 40px;
  --btn-height-lg: 48px;
  --btn-padding-sm: 0 12px;
  --btn-padding-md: 0 16px;
  --btn-padding-lg: 0 24px;
  --btn-font-size: var(--font-size-sm);
  --btn-font-weight: 500;
  --btn-radius: var(--radius-button);
  --btn-primary-bg: var(--color-primary);
  --btn-primary-bg-hover: var(--color-primary-hover);
  --btn-primary-color: var(--color-text-on-primary);

  /* === 입력 === */
  --input-height: 40px;
  --input-padding: 0 12px;
  --input-font-size: var(--font-size-sm);
  --input-border: 1px solid var(--color-border);
  --input-border-focus: 1px solid var(--color-border-focus);
  --input-radius: var(--radius-input);
  --input-bg: #FFFFFF;

  /* === 카드 === */
  --card-padding: var(--spacing-lg);
  --card-radius: var(--radius-card);
  --card-bg: var(--color-bg-card);
  --card-border: 1px solid var(--color-border);
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

---

## 2. 토큰 네이밍 컨벤션

### 2.1 구조

```
--{카테고리}-{속성}-{변형}-{상태}

예시:
--color-bg-primary
--color-text-on-primary
--btn-bg-primary-hover
--input-border-error
--spacing-card-padding
```

### 2.2 네이밍 규칙

| 규칙 | 예시 | 설명 |
|------|------|------|
| kebab-case | `--color-primary` | 하이픈 구분 |
| 카테고리 접두사 | `--color-`, `--spacing-`, `--font-` | 종류 구분 |
| 용도 기반 | `--color-bg-page` | "gray-50" 아닌 용도로 명명 |
| 상태 접미사 | `--btn-bg-hover` | hover, active, focus, disabled |
| 크기 접미사 | `--btn-height-sm` | sm, md, lg, xl |

---

## 3. CSS Custom Properties 구조

```css
/* 전체 구조 */
:root {
  /* 1. 원시 토큰 (절대 직접 사용하지 않음) */
  --_blue-500: #3B82F6;

  /* 2. 의미 토큰 (컴포넌트에서 사용) */
  --color-primary: var(--_blue-500);

  /* 3. 컴포넌트 토큰 (해당 컴포넌트 내에서 사용) */
  --btn-bg: var(--color-primary);
}

/* 다크 모드 전환: 의미 토큰만 변경 */
[data-theme="dark"] {
  --color-primary: var(--_blue-400); /* 더 밝은 파랑 */
  --color-bg-page: var(--_gray-900);
  --color-text-primary: var(--_gray-100);
  /* 컴포넌트 토큰은 변경 불필요 — 의미 토큰을 참조하므로 */
}
```

---

## 4. Tailwind 설정 템플릿

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,js,jsx,ts,tsx}'],
  darkMode: 'class', // 또는 'media'
  theme: {
    extend: {
      colors: {
        // 브랜드 색상
        primary: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6', // 기본
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        secondary: {
          50: '#F5F3FF',
          100: '#EDE9FE',
          200: '#DDD6FE',
          300: '#C4B5FD',
          400: '#A78BFA',
          500: '#8B5CF6',
          600: '#7C3AED',
          700: '#6D28D9',
          800: '#5B21B6',
          900: '#4C1D95',
        },
        // 시맨틱
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#3B82F6',
      },
      fontFamily: {
        sans: ['Pretendard', 'Inter', 'system-ui', 'sans-serif'],
        serif: ['Noto Serif KR', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'display': ['3.5rem', { lineHeight: '1.1', fontWeight: '800' }],
        'h1': ['2.75rem', { lineHeight: '1.15', fontWeight: '700' }],
        'h2': ['2.25rem', { lineHeight: '1.2', fontWeight: '700' }],
        'h3': ['1.75rem', { lineHeight: '1.25', fontWeight: '600' }],
        'h4': ['1.375rem', { lineHeight: '1.3', fontWeight: '600' }],
        'h5': ['1.125rem', { lineHeight: '1.35', fontWeight: '600' }],
      },
      spacing: {
        '18': '4.5rem',   // 72px
        '88': '22rem',     // 352px — 사이드바 등
        '128': '32rem',    // 512px
      },
      borderRadius: {
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '24px',
      },
      boxShadow: {
        'sm': '0 1px 2px rgba(0, 0, 0, 0.05)',
        'DEFAULT': '0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)',
        'md': '0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px rgba(0, 0, 0, 0.1), 0 8px 10px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px rgba(0, 0, 0, 0.25)',
      },
      animation: {
        'spin-slow': 'spin 2s linear infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
```

---

## 5. 컴포넌트 API 설계 원칙

### 5.1 Props 설계

| 원칙 | 예시 |
|------|------|
| 의미 기반 변형 | `variant="primary"` (색상 코드 아님) |
| 크기 스케일 | `size="sm" | "md" | "lg"` |
| 상태 Props | `disabled`, `loading`, `error` |
| 기본값 설정 | size 기본값 "md" |
| 합성 가능 | children, 슬롯, render props |

### 5.2 예시 (React)

```tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}
```

---

## 6. 테마 전환

### 6.1 라이트/다크 전환

```javascript
// 테마 토글 함수
function toggleTheme() {
  const current = document.documentElement.dataset.theme;
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('theme', next);
}

// 초기 로드 시 테마 적용
function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.dataset.theme = saved;
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.dataset.theme = 'dark';
  }
}

// 시스템 설정 변경 감지
window.matchMedia('(prefers-color-scheme: dark)')
  .addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      document.documentElement.dataset.theme = e.matches ? 'dark' : 'light';
    }
  });
```

### 6.2 CSS 다크 모드

```css
:root {
  color-scheme: light dark;
}
[data-theme="dark"] {
  color-scheme: dark;
}

/* 전체 토큰은 color-system.md의 "다크 모드 CSS 변수" 참조 */
```

### 6.3 커스텀 테마 (멀티 브랜드)

```css
[data-theme="brand-a"] {
  --color-primary: #FF6B35;
  --color-primary-hover: #E55A2B;
  --radius-button: 9999px; /* 둥근 버튼 */
}

[data-theme="brand-b"] {
  --color-primary: #2D3436;
  --color-primary-hover: #1A1E1F;
  --radius-button: 0px; /* 각진 버튼 */
}
```

---

## 7. 스페이싱 스케일

```css
:root {
  /* 4px 기반 (작은 간격) */
  --space-0: 0px;
  --space-px: 1px;
  --space-0-5: 2px;
  --space-1: 4px;
  --space-1-5: 6px;
  --space-2: 8px;
  --space-2-5: 10px;
  --space-3: 12px;
  --space-3-5: 14px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-7: 28px;
  --space-8: 32px;
  --space-9: 36px;
  --space-10: 40px;
  --space-11: 44px;
  --space-12: 48px;
  --space-14: 56px;
  --space-16: 64px;
  --space-20: 80px;
  --space-24: 96px;
  --space-28: 112px;
  --space-32: 128px;
  --space-36: 144px;
  --space-40: 160px;
  --space-44: 176px;
  --space-48: 192px;
  --space-52: 208px;
  --space-56: 224px;
  --space-60: 240px;
  --space-64: 256px;
  --space-72: 288px;
  --space-80: 320px;
  --space-96: 384px;
}
```

---

## 8. 아이콘 시스템

### 8.1 아이콘 라이브러리 비교

| 라이브러리 | 아이콘 수 | 스타일 | 크기 | 적합 |
|-----------|---------|--------|------|------|
| Lucide | 1500+ | Outlined (선명) | 24px 기본 | SaaS, 대시보드, 현대적 앱 |
| Phosphor | 7000+ | 6가지 스타일 | 16~48px | 범용, 다양한 분위기 |
| Heroicons | 300+ | Outline/Solid | 20/24px | Tailwind 프로젝트 |
| Tabler Icons | 5000+ | Outlined | 24px | 범용, 무료 |
| Material Symbols | 3000+ | 3스타일, 가변 | 20~48px | Material Design 프로젝트 |

### 8.2 아이콘 크기 규격

| 용도 | 크기 | 예시 |
|------|------|------|
| 인라인 텍스트 | 16px | 체크 아이콘, 상태 |
| 버튼 내부 | 18~20px | 버튼 좌측 아이콘 |
| 네비게이션 | 20~24px | 사이드바, 탭바 |
| 카드 아이콘 | 24~32px | 기능 카드, 설정 |
| 빈 상태 | 48~64px | Empty state 일러스트 |
| Hero 아이콘 | 64~96px | 온보딩, 기능 소개 |

### 8.3 CDN 사용

```html
<!-- Lucide -->
<script src="https://unpkg.com/lucide@latest"></script>
<i data-lucide="home"></i>
<script>lucide.createIcons();</script>

<!-- Phosphor -->
<script src="https://unpkg.com/@phosphor-icons/web"></script>
<i class="ph ph-house"></i>

<!-- Heroicons (SVG) -->
<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955..." />
</svg>
```

---

## 9. 그림자/엘리베이션 체계

```css
:root {
  /* 6단계 그림자 스케일 */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1), 0 8px 10px rgba(0, 0, 0, 0.04);
  --shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.25);

  /* 용도별 그림자 */
  --shadow-card: var(--shadow-sm);
  --shadow-card-hover: var(--shadow-md);
  --shadow-dropdown: var(--shadow-lg);
  --shadow-modal: var(--shadow-xl);
  --shadow-toast: var(--shadow-lg);
  --shadow-popover: var(--shadow-lg);
}

/* 다크 모드 그림자 */
[data-theme="dark"] {
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.35), 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.4), 0 4px 6px rgba(0, 0, 0, 0.3);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.45), 0 8px 10px rgba(0, 0, 0, 0.3);
  --shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.6);
}
```

### 9.1 엘리베이션 용도

| 레벨 | 그림자 | 용도 |
|------|--------|------|
| 0 | none | 평면 요소, 인라인 |
| 1 | xs | 카드 기본, 버튼 |
| 2 | sm | 카드 호버, 드롭다운 트리거 |
| 3 | md | 드롭다운 메뉴, 팝오버 |
| 4 | lg | 사이드바, 네비게이션 |
| 5 | xl | 모달, 대화상자 |
| 6 | 2xl | 전체 화면 오버레이 |

---

## 10. 보더 라디우스 체계

```css
:root {
  --radius-none: 0px;     /* 각진 요소 */
  --radius-sm: 4px;       /* 뱃지, 태그, 작은 요소 */
  --radius-md: 8px;       /* 버튼, 입력, 일반 요소 */
  --radius-lg: 12px;      /* 카드, 컨테이너 */
  --radius-xl: 16px;      /* 큰 카드, 모달 */
  --radius-2xl: 24px;     /* 큰 컨테이너, 섹션 */
  --radius-full: 9999px;  /* 원형: 아바타, 뱃지, 필 탭 */
}
```

### 10.1 라디우스 적용 규칙

| 요소 | 라디우스 | 이유 |
|------|---------|------|
| 아바타 | full | 원형 |
| 뱃지/태그 | full 또는 sm | 캡슐 또는 작은 둥근 |
| 버튼 | md (8px) | 표준 둥글기 |
| 입력 필드 | md (8px) | 버튼과 일치 |
| 카드 | lg (12px) | 부드러운 모서리 |
| 모달 | xl (16px) | 큰 요소는 더 둥글게 |
| 바텀 시트 | xl xl 0 0 | 상단만 둥글게 |
| 툴팁 | sm (4px) | 작고 날카롭게 |
| 이미지 | lg (12px) | 카드 내부와 일치 |

### 10.2 내부 라디우스 공식

컨테이너 안의 요소 라디우스 = 컨테이너 라디우스 - 패딩

```css
.card {
  border-radius: 12px;  /* 외부 */
  padding: 4px;
}
.card__image {
  border-radius: 8px;   /* 12px - 4px = 8px */
}
```

---

## 11. 디자인 시스템 체크리스트

프로젝트 시작 시 확인:

| 항목 | 확인 |
|------|------|
| 색상 팔레트 정의 (Primary, Secondary, Neutral, Semantic) | |
| 폰트 선정 + Google Fonts URL | |
| 타입 스케일 정의 (H1~H6, Body, Caption) | |
| 스페이싱 스케일 정의 (4px 또는 8px 기반) | |
| 보더 라디우스 스케일 정의 | |
| 그림자 스케일 정의 | |
| 브레이크포인트 정의 | |
| 아이콘 라이브러리 선정 | |
| 버튼 스타일 정의 (variant, size, state) | |
| 입력 스타일 정의 (state: default, focus, error, disabled) | |
| 카드 스타일 정의 | |
| 다크 모드 토큰 정의 | |
| z-index 스케일 정의 | |
| CSS Custom Properties 또는 Tailwind config 작성 | |
