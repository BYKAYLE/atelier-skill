# 컴포넌트 패턴 백과사전

## 1. Button (버튼)

### 1.1 버튼 유형

| 유형 | 용도 | 시각적 특징 |
|------|------|-----------|
| Primary | 주요 CTA | 배경색 + 흰색 텍스트 |
| Secondary | 보조 액션 | 테두리 + 색상 텍스트 |
| Ghost | 3차 액션, 인라인 | 배경 없음 + 색상 텍스트 |
| Destructive | 삭제, 위험 | 빨간 배경 + 흰색 텍스트 |
| Link | 텍스트 내 링크 | 밑줄 + 색상 텍스트 |

### 1.2 버튼 크기

| 크기 | Height | Padding | Font Size | 용도 |
|------|--------|---------|-----------|------|
| xs | 28px | 4px 8px | 12px | 테이블 내, 인라인 |
| sm | 32px | 6px 12px | 13px | 밀집 UI, 도구 모음 |
| md | 40px | 8px 16px | 14px | 기본 |
| lg | 48px | 12px 24px | 16px | 폼 제출, CTA |
| xl | 56px | 16px 32px | 18px | Hero CTA, 랜딩 |

### 1.3 버튼 상태

```css
/* Primary Button */
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1;
  color: #FFFFFF;
  background: #3B82F6;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}
.btn-primary:hover {
  background: #2563EB;
}
.btn-primary:active {
  background: #1D4ED8;
  transform: scale(0.98);
}
.btn-primary:focus-visible {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
}
.btn-primary:disabled {
  background: #93C5FD;
  cursor: not-allowed;
  opacity: 0.7;
}

/* Secondary Button */
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  background: #FFFFFF;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-secondary:hover {
  background: #F9FAFB;
  border-color: #9CA3AF;
}

/* Ghost Button */
.btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-ghost:hover {
  background: #F3F4F6;
}

/* Destructive Button */
.btn-destructive {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 500;
  color: #FFFFFF;
  background: #EF4444;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-destructive:hover {
  background: #DC2626;
}

/* Loading State */
.btn-loading {
  position: relative;
  color: transparent;
  pointer-events: none;
}
.btn-loading::after {
  content: "";
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #FFFFFF;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
```

### 1.4 버튼 접근성
- 모든 아이콘 전용 버튼에 `aria-label` 필수
- 로딩 중: `aria-busy="true"`, `aria-label="로딩 중"`
- 토글 버튼: `aria-pressed="true/false"`
- 비활성: `disabled` 속성 (aria-disabled이 아닌 native disabled)
- 포커스 링: 반드시 visible (`focus-visible` 사용)

---

## 2. Input (입력 필드)

### 2.1 기본 텍스트 입력

```html
<div class="form-field">
  <label for="email" class="form-label">이메일</label>
  <input type="email" id="email" class="form-input" placeholder="name@example.com">
  <p class="form-helper">업무용 이메일을 입력해주세요</p>
</div>
```

```css
.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}
.form-input {
  height: 40px;
  padding: 0 12px;
  font-size: 14px;
  color: #111827;
  background: #FFFFFF;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  outline: none;
  transition: all 0.15s ease;
}
.form-input::placeholder {
  color: #9CA3AF;
}
.form-input:hover {
  border-color: #9CA3AF;
}
.form-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
.form-input--error {
  border-color: #EF4444;
}
.form-input--error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}
.form-helper {
  font-size: 12px;
  color: #6B7280;
}
.form-error {
  font-size: 12px;
  color: #EF4444;
}
```

### 2.2 입력 상태

| 상태 | Border | Background | 텍스트 |
|------|--------|-----------|--------|
| Default | #D1D5DB | #FFFFFF | #111827 |
| Hover | #9CA3AF | #FFFFFF | #111827 |
| Focus | #3B82F6 + ring | #FFFFFF | #111827 |
| Error | #EF4444 + ring | #FEF2F2 | #111827 |
| Disabled | #E5E7EB | #F9FAFB | #9CA3AF |
| Readonly | #E5E7EB | #F3F4F6 | #6B7280 |

### 2.3 입력 접근성
- 모든 `<input>`에 `<label>` 연결 (for/id 매칭)
- 에러 메시지: `aria-describedby` + `aria-invalid="true"`
- 필수 필드: `required` + `aria-required="true"`
- 비밀번호 보기/숨기기: 토글 버튼에 `aria-label`

---

## 3. Select / Dropdown / Combobox

```html
<!-- Native Select -->
<div class="form-field">
  <label for="country" class="form-label">국가</label>
  <div class="select-wrapper">
    <select id="country" class="form-select">
      <option value="">선택해주세요</option>
      <option value="kr">대한민국</option>
      <option value="us">미국</option>
      <option value="jp">일본</option>
    </select>
  </div>
</div>
```

```css
.select-wrapper {
  position: relative;
}
.form-select {
  width: 100%;
  height: 40px;
  padding: 0 36px 0 12px;
  font-size: 14px;
  color: #111827;
  background: #FFFFFF;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  appearance: none;
  cursor: pointer;
}
.select-wrapper::after {
  content: "";
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 5px solid #6B7280;
  pointer-events: none;
}
```

---

## 4. Checkbox / Radio / Toggle

```css
/* Custom Checkbox */
.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.checkbox input[type="checkbox"] {
  appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid #D1D5DB;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
}
.checkbox input[type="checkbox"]:checked {
  background: #3B82F6;
  border-color: #3B82F6;
}
.checkbox input[type="checkbox"]:checked::after {
  content: "";
  position: absolute;
  left: 4px;
  top: 1px;
  width: 6px;
  height: 10px;
  border: solid #FFFFFF;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}
.checkbox input[type="checkbox"]:focus-visible {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
}

/* Toggle Switch */
.toggle {
  position: relative;
  width: 44px;
  height: 24px;
  background: #D1D5DB;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}
.toggle__slider {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: #FFFFFF;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.toggle input:checked + .toggle__slider {
  transform: translateX(20px);
}
.toggle:has(input:checked) {
  background: #3B82F6;
}
```

접근성:
- Checkbox: `role="checkbox"`, `aria-checked`
- Radio: 그룹은 `role="radiogroup"`, 각 항목 `role="radio"`
- Toggle: `role="switch"`, `aria-checked`

---

## 5. Card

### 5.1 기본 카드

```css
.card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.15s ease;
}
.card--interactive:hover {
  border-color: #D1D5DB;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transform: translateY(-1px);
  cursor: pointer;
}
.card--elevated {
  border: none;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
}
```

### 5.2 카드 변형

| 카드 유형 | 구조 |
|----------|------|
| Article | 이미지 + 카테고리 + 제목 + 발췌 + 메타 |
| Product | 이미지 + 이름 + 가격 + 평점 + CTA |
| Profile | 아바타 + 이름 + 역할 + 소셜 링크 |
| Stat | 아이콘 + 레이블 + 숫자 + 변화량 |
| Pricing | 플랜명 + 가격 + 기능 목록 + CTA |

```html
<!-- Stat Card -->
<div class="stat-card">
  <div class="stat-card__header">
    <span class="stat-card__icon">📊</span>
    <span class="stat-card__label">총 매출</span>
  </div>
  <div class="stat-card__value">₩12,345,000</div>
  <div class="stat-card__change stat-card__change--positive">
    +12.5% 전월 대비
  </div>
</div>
```

```css
.stat-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 24px;
}
.stat-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.stat-card__label {
  font-size: 14px;
  color: #6B7280;
}
.stat-card__value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  font-variant-numeric: tabular-nums;
}
.stat-card__change {
  font-size: 13px;
  margin-top: 4px;
}
.stat-card__change--positive { color: #10B981; }
.stat-card__change--negative { color: #EF4444; }
```

---

## 6. Modal / Dialog / Drawer / Sheet

### 6.1 Modal

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 16px;
}
.modal {
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.2);
  max-width: 480px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}
.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 0;
}
.modal__title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}
.modal__close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: #6B7280;
}
.modal__close:hover {
  background: #F3F4F6;
}
.modal__body {
  padding: 16px 24px;
}
.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 24px 24px;
}
```

접근성:
- `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- 포커스 트랩: Tab이 모달 내부만 순환
- ESC로 닫기
- 닫을 때 트리거 요소로 포커스 복원
- 배경 콘텐츠: `aria-hidden="true"`, `inert`

### 6.2 Drawer / Sheet

```css
/* 우측 Drawer */
.drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  max-width: 90vw;
  height: 100vh;
  background: #FFFFFF;
  box-shadow: -4px 0 24px rgba(0,0,0,0.15);
  z-index: 50;
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}
.drawer--open {
  transform: translateX(0);
}

/* 하단 Sheet (모바일) */
.sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #FFFFFF;
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -4px 24px rgba(0,0,0,0.15);
  z-index: 50;
  max-height: 90vh;
  transform: translateY(100%);
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet--open {
  transform: translateY(0);
}
.sheet__handle {
  width: 36px;
  height: 4px;
  background: #D1D5DB;
  border-radius: 2px;
  margin: 8px auto;
}
```

---

## 7. Toast / Snackbar / Alert / Banner

### 7.1 Toast

```css
.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  border-left: 4px solid;
  max-width: 400px;
  animation: toast-in 0.3s ease;
}
.toast--success { border-color: #10B981; }
.toast--error { border-color: #EF4444; }
.toast--warning { border-color: #F59E0B; }
.toast--info { border-color: #3B82F6; }

@keyframes toast-in {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
```

접근성: `role="alert"`, `aria-live="polite"` (info) 또는 `aria-live="assertive"` (error)

### 7.2 Alert / Banner

```css
.alert {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  font-size: 14px;
}
.alert--success { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
.alert--error { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
.alert--warning { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
.alert--info { background: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; }
```

---

## 8. Table

```css
.table-container {
  overflow-x: auto;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
}
table {
  width: 100%;
  border-collapse: collapse;
}
thead th {
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #6B7280;
  text-align: left;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}
tbody td {
  padding: 12px 16px;
  font-size: 14px;
  color: #111827;
  border-bottom: 1px solid #F3F4F6;
}
tbody tr:hover {
  background: #F9FAFB;
}
tbody tr:last-child td {
  border-bottom: none;
}
/* 숫자 정렬 */
.cell-number {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
/* 상태 뱃지 */
.cell-status {
  display: inline-flex;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
}
.cell-status--active { background: #ECFDF5; color: #065F46; }
.cell-status--inactive { background: #F3F4F6; color: #6B7280; }
.cell-status--pending { background: #FFFBEB; color: #92400E; }
```

접근성: `<caption>`, `scope="col"` / `scope="row"`, `aria-sort` 정렬 시

---

## 9. Navigation

### 9.1 TopBar

```css
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 24px;
  background: #FFFFFF;
  border-bottom: 1px solid #E5E7EB;
  position: sticky;
  top: 0;
  z-index: 40;
}
.topbar__logo {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}
.topbar__nav {
  display: flex;
  align-items: center;
  gap: 4px;
}
.topbar__link {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.15s;
}
.topbar__link:hover { background: #F3F4F6; color: #111827; }
.topbar__link--active { background: #EFF6FF; color: #3B82F6; }
```

### 9.2 Sidebar

```css
.sidebar {
  width: 240px;
  height: 100vh;
  background: #FFFFFF;
  border-right: 1px solid #E5E7EB;
  padding: 16px 12px;
  position: fixed;
  left: 0;
  top: 0;
  overflow-y: auto;
  transition: width 0.2s ease;
}
.sidebar--collapsed {
  width: 60px;
}
.sidebar__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  color: #6B7280;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.15s;
  white-space: nowrap;
}
.sidebar__item:hover { background: #F3F4F6; color: #111827; }
.sidebar__item--active { background: #EFF6FF; color: #3B82F6; }
.sidebar__icon { width: 20px; height: 20px; flex-shrink: 0; }
.sidebar--collapsed .sidebar__label { display: none; }
```

### 9.3 Bottom Tab Bar (모바일)

```css
.bottom-tabs {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(56px + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: #FFFFFF;
  border-top: 1px solid #E5E7EB;
  z-index: 40;
}
.bottom-tabs__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 16px;
  color: #9CA3AF;
  font-size: 10px;
  text-decoration: none;
  min-width: 64px;
}
.bottom-tabs__item--active {
  color: #3B82F6;
}
.bottom-tabs__icon {
  width: 24px;
  height: 24px;
}
```

### 9.4 Breadcrumb

```html
<nav aria-label="Breadcrumb">
  <ol class="breadcrumb">
    <li><a href="/">홈</a></li>
    <li><a href="/products">제품</a></li>
    <li aria-current="page">상세</li>
  </ol>
</nav>
```

```css
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  list-style: none;
  font-size: 14px;
}
.breadcrumb li + li::before {
  content: "/";
  color: #D1D5DB;
  margin-right: 4px;
}
.breadcrumb a { color: #6B7280; text-decoration: none; }
.breadcrumb a:hover { color: #111827; }
.breadcrumb [aria-current] { color: #111827; font-weight: 500; }
```

---

## 10. Tabs / Segmented Control

```css
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid #E5E7EB;
}
.tab {
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: -1px;
}
.tab:hover { color: #111827; }
.tab--active {
  color: #3B82F6;
  border-bottom-color: #3B82F6;
}

/* Pill Tabs */
.pill-tabs {
  display: flex;
  gap: 4px;
  background: #F3F4F6;
  border-radius: 10px;
  padding: 4px;
}
.pill-tab {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}
.pill-tab--active {
  background: #FFFFFF;
  color: #111827;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
```

접근성: `role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected`, `aria-controls`

---

## 11. Avatar / Badge / Tag / Chip

```css
/* Avatar */
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  background: #E5E7EB;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: #6B7280;
}
.avatar--sm { width: 32px; height: 32px; font-size: 12px; }
.avatar--lg { width: 48px; height: 48px; font-size: 18px; }
.avatar--xl { width: 64px; height: 64px; font-size: 24px; }

/* Badge (숫자/상태) */
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  font-size: 11px;
  font-weight: 600;
  color: #FFFFFF;
  background: #EF4444;
  border-radius: 9999px;
}

/* Tag / Chip */
.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 9999px;
  background: #F3F4F6;
  color: #374151;
}
.tag--primary { background: #EFF6FF; color: #1D4ED8; }
.tag--success { background: #ECFDF5; color: #065F46; }
.tag--warning { background: #FFFBEB; color: #92400E; }
.tag--error { background: #FEF2F2; color: #991B1B; }
.tag__remove {
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 50%;
  opacity: 0.5;
}
.tag__remove:hover { opacity: 1; background: rgba(0,0,0,0.1); }
```

---

## 12. Skeleton / Shimmer Loading

```css
.skeleton {
  background: #E5E7EB;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}
.skeleton::after {
  content: "";
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.4),
    transparent
  );
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  100% { transform: translateX(100%); }
}
.skeleton--text { height: 16px; width: 80%; }
.skeleton--title { height: 24px; width: 60%; }
.skeleton--avatar { width: 40px; height: 40px; border-radius: 50%; }
.skeleton--image { height: 200px; width: 100%; }
.skeleton--button { height: 40px; width: 120px; }
```

---

## 13. Empty State

```html
<div class="empty-state">
  <div class="empty-state__icon">📭</div>
  <h3 class="empty-state__title">아직 데이터가 없습니다</h3>
  <p class="empty-state__description">첫 번째 항목을 추가해보세요</p>
  <button class="btn-primary">항목 추가</button>
</div>
```

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}
.empty-state__icon { font-size: 48px; margin-bottom: 16px; }
.empty-state__title { font-size: 18px; font-weight: 600; color: #111827; margin-bottom: 8px; }
.empty-state__description { font-size: 14px; color: #6B7280; margin-bottom: 24px; max-width: 320px; }
```

---

## 14. Tooltip / Popover

```css
.tooltip {
  position: relative;
  display: inline-block;
}
.tooltip__content {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 12px;
  font-size: 12px;
  color: #FFFFFF;
  background: #1F2937;
  border-radius: 6px;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
}
.tooltip:hover .tooltip__content,
.tooltip:focus-within .tooltip__content {
  opacity: 1;
}
.tooltip__content::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: #1F2937;
}
```

접근성: `role="tooltip"`, `aria-describedby`, 키보드 포커스로도 표시

---

## 15. Progress / Spinner

```css
/* Progress Bar */
.progress {
  width: 100%;
  height: 8px;
  background: #E5E7EB;
  border-radius: 4px;
  overflow: hidden;
}
.progress__bar {
  height: 100%;
  background: #3B82F6;
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* Spinner */
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
```

접근성: `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-label`

---

## 16. Command Palette (Cmd+K)

```css
.command-palette {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 20vh;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
}
.command-palette__container {
  width: 560px;
  max-width: 90vw;
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 24px 48px rgba(0,0,0,0.2);
  overflow: hidden;
}
.command-palette__input {
  width: 100%;
  height: 56px;
  padding: 0 20px;
  font-size: 16px;
  border: none;
  border-bottom: 1px solid #E5E7EB;
  outline: none;
}
.command-palette__results {
  max-height: 320px;
  overflow-y: auto;
  padding: 8px;
}
.command-palette__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
}
.command-palette__item:hover,
.command-palette__item--selected {
  background: #F3F4F6;
}
.command-palette__shortcut {
  margin-left: auto;
  font-size: 11px;
  color: #9CA3AF;
  display: flex;
  gap: 4px;
}
.command-palette__shortcut kbd {
  padding: 2px 6px;
  background: #F3F4F6;
  border: 1px solid #E5E7EB;
  border-radius: 4px;
  font-size: 11px;
}
```

---

## 17. Date Picker / Calendar

```css
.calendar {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 16px;
  width: 320px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.calendar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.calendar__title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}
.calendar__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}
.calendar__day-name {
  padding: 8px 0;
  font-size: 12px;
  font-weight: 600;
  color: #9CA3AF;
  text-align: center;
}
.calendar__day {
  padding: 8px 0;
  font-size: 14px;
  text-align: center;
  border-radius: 8px;
  cursor: pointer;
  color: #374151;
}
.calendar__day:hover { background: #F3F4F6; }
.calendar__day--today { font-weight: 700; color: #3B82F6; }
.calendar__day--selected { background: #3B82F6; color: #FFFFFF; }
.calendar__day--disabled { color: #D1D5DB; cursor: not-allowed; }
.calendar__day--range { background: #EFF6FF; }
```

---

## 18. File Upload / Drag & Drop

```css
.file-upload {
  border: 2px dashed #D1D5DB;
  border-radius: 12px;
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
}
.file-upload:hover {
  border-color: #3B82F6;
  background: #F8FAFC;
}
.file-upload--dragging {
  border-color: #3B82F6;
  background: #EFF6FF;
}
.file-upload__icon { font-size: 36px; margin-bottom: 12px; }
.file-upload__title { font-size: 16px; font-weight: 600; color: #111827; }
.file-upload__description { font-size: 14px; color: #6B7280; margin-top: 4px; }
```

---

## 19. Accordion / Collapsible

```css
.accordion {
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  overflow: hidden;
}
.accordion__item + .accordion__item {
  border-top: 1px solid #E5E7EB;
}
.accordion__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 16px 20px;
  font-size: 15px;
  font-weight: 500;
  color: #111827;
  background: #FFFFFF;
  border: none;
  cursor: pointer;
  text-align: left;
}
.accordion__trigger:hover { background: #F9FAFB; }
.accordion__icon {
  width: 20px;
  height: 20px;
  transition: transform 0.2s;
}
.accordion__item--open .accordion__icon {
  transform: rotate(180deg);
}
.accordion__content {
  padding: 0 20px 16px;
  font-size: 14px;
  color: #6B7280;
  line-height: 1.6;
}
```

접근성: `aria-expanded`, `aria-controls`, `id` 매칭

---

## 20. Carousel / Slider

```css
.carousel {
  position: relative;
  overflow: hidden;
}
.carousel__track {
  display: flex;
  transition: transform 0.3s ease;
}
.carousel__slide {
  min-width: 100%;
  flex-shrink: 0;
}
.carousel__nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  background: rgba(255,255,255,0.9);
  border: 1px solid #E5E7EB;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.carousel__nav--prev { left: 16px; }
.carousel__nav--next { right: 16px; }
.carousel__dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
}
.carousel__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #D1D5DB;
  border: none;
  cursor: pointer;
}
.carousel__dot--active {
  background: #3B82F6;
  width: 24px;
  border-radius: 4px;
}
```

접근성: `role="region"`, `aria-roledescription="carousel"`, `aria-label`, 자동 재생 시 일시정지 버튼 필수
