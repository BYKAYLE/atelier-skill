# 접근성 백과사전

## 1. WCAG 2.1 전체 체크리스트

### 1.1 레벨 A (최소 요구사항)

| 기준 | 설명 | 검증 방법 |
|------|------|----------|
| 1.1.1 비텍스트 콘텐츠 | 모든 이미지에 alt 텍스트 | `img` 태그에 `alt` 속성 확인 |
| 1.2.1 오디오/비디오 | 자막 또는 대체 텍스트 제공 | 미디어 요소 확인 |
| 1.3.1 정보와 관계 | 시맨틱 HTML 사용 | heading 순서, list, table 구조 확인 |
| 1.3.2 의미있는 순서 | DOM 순서 = 시각적 순서 | CSS order, flexbox 순서 확인 |
| 1.3.3 감각 특성 | 색상/모양만으로 정보 전달하지 않음 | 색맹 모드에서 확인 |
| 1.4.1 색상 사용 | 색상만으로 구분하지 않음 | 아이콘, 텍스트, 패턴 추가 |
| 1.4.2 오디오 제어 | 자동 재생 오디오 3초 이내 중지 가능 | 자동 재생 요소 확인 |
| 2.1.1 키보드 | 모든 기능 키보드로 접근 가능 | Tab 키로 전체 순회 |
| 2.1.2 키보드 트랩 없음 | 포커스가 특정 요소에 갇히지 않음 | 모달 외 요소에서 확인 |
| 2.2.1 타이밍 조절 | 시간 제한 있으면 연장/해제 가능 | 세션 타임아웃 확인 |
| 2.3.1 번쩍임 | 3회/초 이상 번쩍이지 않음 | 애니메이션 확인 |
| 2.4.1 반복 건너뛰기 | Skip to content 링크 제공 | 페이지 최상단 확인 |
| 2.4.2 페이지 제목 | 각 페이지에 고유 `<title>` | `<title>` 태그 확인 |
| 2.4.3 포커스 순서 | Tab 순서가 논리적 | Tab 키로 순서 확인 |
| 2.4.4 링크 목적 | 링크 텍스트만으로 목적 파악 가능 | "여기 클릭" 같은 모호한 텍스트 금지 |
| 3.1.1 페이지 언어 | `<html lang="ko">` | lang 속성 확인 |
| 3.2.1 포커스 시 변경 없음 | 포커스만으로 페이지 이동 안 됨 | Tab 시 의도치 않은 변경 확인 |
| 3.3.1 에러 식별 | 에러 발생 시 텍스트로 설명 | 폼 에러 메시지 확인 |
| 3.3.2 레이블/지시문 | 입력에 레이블 연결 | label + for 매칭 확인 |
| 4.1.1 파싱 | 유효한 HTML | W3C Validator |
| 4.1.2 이름, 역할, 값 | ARIA 속성 올바르게 사용 | ARIA 속성 확인 |

### 1.2 레벨 AA (권장)

| 기준 | 설명 | 검증 방법 |
|------|------|----------|
| 1.4.3 대비(최소) | 텍스트 4.5:1, 대형 3:1 | 대비비 도구 |
| 1.4.4 텍스트 크기 조절 | 200%까지 확대해도 콘텐츠 유지 | 브라우저 줌 200% |
| 1.4.5 이미지 속 텍스트 | 텍스트는 이미지가 아닌 실제 텍스트로 | 이미지 내 텍스트 확인 |
| 1.4.10 리플로우 | 320px에서 가로 스크롤 없음 | 320px 뷰포트 테스트 |
| 1.4.11 비텍스트 대비 | UI 컴포넌트 3:1 대비 | 버튼 테두리, 입력 테두리 |
| 1.4.12 텍스트 간격 | 줄 높이 1.5배, 문단 간격 2배, 자간 0.12em, 단어 간격 0.16em까지 조절 가능 | 브라우저 확장 테스트 |
| 1.4.13 호버/포커스 콘텐츠 | 툴팁 등 ESC로 닫기 가능, 포인터 이동 가능 | 호버 콘텐츠 확인 |
| 2.4.5 다양한 방법 | 콘텐츠 접근 경로 2개 이상 (네비게이션 + 검색) | 사이트맵/검색 확인 |
| 2.4.6 제목과 레이블 | 제목이 콘텐츠를 설명 | heading 텍스트 확인 |
| 2.4.7 포커스 표시 | 포커스된 요소가 시각적으로 구분 | focus-visible 확인 |
| 3.2.3 일관된 내비게이션 | 반복 내비게이션 일관적 | 페이지 간 네비 비교 |
| 3.2.4 일관된 식별 | 같은 기능 같은 아이콘/텍스트 | 페이지 간 비교 |
| 3.3.3 에러 제안 | 에러 시 수정 방법 제안 | 폼 에러 메시지 확인 |
| 3.3.4 에러 방지 | 법적/금전 행위 시 확인/검토/취소 가능 | 결제/삭제 플로우 확인 |

### 1.3 레벨 AAA (최고 수준)

| 기준 | 설명 |
|------|------|
| 1.4.6 대비(향상) | 텍스트 7:1, 대형 4.5:1 |
| 1.4.8 시각적 표현 | 전경/배경색 선택 가능, 너비 80자 이내 |
| 2.2.3 타이밍 없음 | 시간 제한 없이 사용 가능 |
| 2.4.8 현재 위치 | 사이트 내 현재 위치 표시 (브레드크럼) |
| 3.1.3 특이한 단어 | 전문 용어 정의 제공 |
| 3.2.5 요청에 의한 변경 | 사용자 요청 없이 컨텍스트 변경 없음 |

---

## 2. ARIA 역할/속성/상태 레퍼런스

### 2.1 랜드마크 역할

```html
<header role="banner">  <!-- 또는 <header> -->
<nav role="navigation">  <!-- 또는 <nav> -->
<main role="main">  <!-- 또는 <main> -->
<aside role="complementary">  <!-- 또는 <aside> -->
<footer role="contentinfo">  <!-- 또는 <footer> -->
<form role="search">  <!-- 검색 폼 -->
<section role="region" aria-labelledby="section-title">
```

**규칙:** 시맨틱 HTML 태그가 있으면 role 속성 불필요. 둘 다 쓰면 중복.

### 2.2 위젯 역할

| 역할 | 용도 | 필수 속성 |
|------|------|----------|
| `role="button"` | 비 button 요소를 버튼으로 | `tabindex="0"`, keydown 핸들러 |
| `role="dialog"` | 모달/대화상자 | `aria-modal`, `aria-labelledby` |
| `role="alertdialog"` | 확인 대화상자 | `aria-modal`, `aria-labelledby` |
| `role="tab"` | 탭 | `aria-selected`, `aria-controls` |
| `role="tablist"` | 탭 목록 | 자식에 `role="tab"` |
| `role="tabpanel"` | 탭 패널 | `aria-labelledby` |
| `role="menu"` | 메뉴 | 자식에 `role="menuitem"` |
| `role="menuitem"` | 메뉴 항목 | 부모에 `role="menu"` |
| `role="listbox"` | 선택 목록 | 자식에 `role="option"` |
| `role="option"` | 선택 항목 | `aria-selected` |
| `role="switch"` | 토글 스위치 | `aria-checked` |
| `role="progressbar"` | 진행률 | `aria-valuenow`, `aria-valuemin`, `aria-valuemax` |
| `role="tooltip"` | 툴팁 | 트리거에 `aria-describedby` |
| `role="alert"` | 알림 | 자동으로 `aria-live="assertive"` |
| `role="status"` | 상태 표시 | 자동으로 `aria-live="polite"` |
| `role="tree"` | 트리 뷰 | 자식에 `role="treeitem"` |
| `role="grid"` | 데이터 그리드 | 자식에 `role="row"`, `role="gridcell"` |

### 2.3 상태/속성

```html
<!-- 확장/축소 -->
<button aria-expanded="false" aria-controls="panel-1">메뉴 열기</button>
<div id="panel-1" hidden>패널 내용</div>

<!-- 선택 상태 -->
<li role="option" aria-selected="true">선택됨</li>

<!-- 체크 상태 -->
<div role="checkbox" aria-checked="true" tabindex="0">체크됨</div>
<div role="checkbox" aria-checked="mixed" tabindex="0">부분 체크</div>

<!-- 비활성 -->
<button aria-disabled="true">비활성 버튼</button>

<!-- 숨김 -->
<div aria-hidden="true">스크린리더에서 숨김</div>

<!-- 현재 상태 -->
<a aria-current="page">현재 페이지</a>
<li aria-current="step">현재 단계</li>

<!-- 에러 상태 -->
<input aria-invalid="true" aria-describedby="error-msg">
<p id="error-msg" role="alert">이메일 형식이 올바르지 않습니다</p>

<!-- 필수 필드 -->
<input aria-required="true">

<!-- 바쁜 상태 -->
<div aria-busy="true">로딩 중...</div>

<!-- 레이블링 -->
<input aria-label="검색어 입력">
<input aria-labelledby="label-1 label-2">
<input aria-describedby="helper-text">
```

---

## 3. 키보드 내비게이션 패턴

### 3.1 Tab 순서

```css
/* 기본 Tab 순서: DOM 순서를 따름 */
/* tabindex 사용 규칙: */
/* tabindex="0"  — Tab 순서에 포함 (비대화형 요소를 대화형으로) */
/* tabindex="-1" — 프로그래밍으로만 포커스 가능 (Skip Link 대상 등) */
/* tabindex="1+" — 절대 사용하지 않는다 (순서 혼란) */
```

### 3.2 포커스 트랩 (모달)

```javascript
function trapFocus(element) {
  const focusable = element.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), ' +
    'select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  element.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });

  first.focus();
}
```

### 3.3 Skip Link

```html
<a href="#main-content" class="skip-link">메인 콘텐츠로 건너뛰기</a>
<!-- ... 네비게이션 ... -->
<main id="main-content" tabindex="-1">
  <!-- 메인 콘텐츠 -->
</main>
```

```css
.skip-link {
  position: absolute;
  top: -100%;
  left: 16px;
  z-index: 9999;
  padding: 12px 24px;
  background: #3B82F6;
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 600;
  border-radius: 0 0 8px 8px;
  text-decoration: none;
  transition: top 0.15s;
}
.skip-link:focus {
  top: 0;
}
```

### 3.4 컴포넌트별 키보드 패턴

| 컴포넌트 | 키보드 조작 |
|---------|-----------|
| 버튼 | Enter/Space → 클릭 |
| 링크 | Enter → 이동 |
| 체크박스 | Space → 토글 |
| 라디오 그룹 | 화살표 → 선택 이동, Space → 선택 |
| 탭 | 화살표 → 탭 이동, Enter/Space → 활성화 |
| 드롭다운 | 화살표 → 항목 이동, Enter → 선택, ESC → 닫기 |
| 모달 | ESC → 닫기, Tab → 내부 순환 |
| 메뉴 | 화살표 → 항목 이동, Enter → 선택, ESC → 닫기 |
| 트리 | 화살표 위/아래 → 이동, 좌/우 → 축소/확장 |
| 슬라이더 | 화살표 → 값 조절, Home/End → 최소/최대 |
| 아코디언 | Enter/Space → 토글, 화살표 → 헤더 간 이동 |
| 캐러셀 | 화살표 → 이전/다음, Tab → 컨트롤 |
| 커맨드 팔레트 | 화살표 → 항목 이동, Enter → 실행, ESC → 닫기 |

---

## 4. 스크린 리더 호환 패턴

### 4.1 시각적으로만 숨기기 (스크린 리더에는 보임)

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: inherit;
}
```

### 4.2 스크린 리더에서 숨기기 (시각적으로는 보임)

```html
<div aria-hidden="true">장식용 아이콘</div>
<img src="decorative.svg" alt="" role="presentation">
```

### 4.3 라이브 영역

```html
<!-- 폼 제출 결과 -->
<div aria-live="polite" aria-atomic="true">
  저장되었습니다.
</div>

<!-- 긴급 알림 -->
<div aria-live="assertive" role="alert">
  세션이 만료됩니다.
</div>

<!-- 카운터 업데이트 -->
<div aria-live="polite">
  장바구니: <span>3</span>개
</div>
```

| 속성 | 값 | 용도 |
|------|---|------|
| `aria-live="polite"` | 현재 읽기 끝나면 알림 | 상태 업데이트, 성공 메시지 |
| `aria-live="assertive"` | 즉시 알림 | 에러, 긴급 알림 |
| `aria-atomic="true"` | 전체 영역 다시 읽기 | 카운터, 요약 |
| `aria-relevant="additions"` | 추가된 내용만 읽기 | 채팅, 로그 |

---

## 5. 색맹 친화 디자인

### 5.1 색맹 유형

| 유형 | 비율 | 구분 어려운 색상 |
|------|------|----------------|
| 적록 색맹 (가장 흔함) | 남성 8%, 여성 0.5% | 빨강 ↔ 녹색 |
| 청황 색맹 | 0.003% | 파랑 ↔ 노랑 |
| 완전 색맹 | 매우 드묾 | 모든 색 |

### 5.2 규칙

| 규칙 | 구현 |
|------|------|
| 색상만으로 정보 전달 금지 | 아이콘 + 텍스트 + 색상 조합 |
| 그래프에서 색상 외 구분자 | 패턴, 모양, 라벨 추가 |
| 성공/실패 표시 | 초록/빨강 + 체크/X 아이콘 |
| 링크 구분 | 색상 + 밑줄 |
| 필수 필드 표시 | 빨강 별표 + "필수" 텍스트 |

```css
/* 에러 표시 — 색상 + 아이콘 + 텍스트 */
.form-input--error {
  border-color: #EF4444;
  /* 색상만이 아닌 아이콘도 표시 */
  background-image: url("data:image/svg+xml,..."); /* X 아이콘 */
  background-position: right 12px center;
  background-repeat: no-repeat;
}
.form-error-text {
  color: #EF4444;
  /* 아이콘 추가 */
}
.form-error-text::before {
  content: "! ";
  font-weight: bold;
}
```

---

## 6. 터치 타겟 크기

| 플랫폼 | 최소 크기 | 권장 크기 |
|--------|----------|----------|
| iOS (Apple HIG) | 44x44pt | 48x48pt |
| Android (Material) | 48x48dp | 48x48dp |
| WCAG 2.1 AAA | 44x44 CSS px | — |
| WCAG 2.2 AA | 24x24 CSS px (최소) | 44x44 CSS px |

```css
/* 터치 타겟 확보 */
.touch-target {
  position: relative;
  min-width: 44px;
  min-height: 44px;
}
/* 작은 요소도 터치 영역 확보 */
.small-button::after {
  content: "";
  position: absolute;
  inset: -8px; /* 패딩 확장 */
}
/* 인접 터치 타겟 간 간격 */
.touch-row {
  display: flex;
  gap: 8px; /* 최소 8px 간격 */
}
```

---

## 7. 움직임 감소 (prefers-reduced-motion)

```css
/* 기본: 애니메이션 적용 */
.animated {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

/* 사용자가 움직임 감소를 원할 때 */
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

/* 또는 세밀하게 제어 */
@media (prefers-reduced-motion: reduce) {
  .animated {
    transition: none;
  }
  .parallax {
    transform: none;
  }
  .carousel {
    /* 자동 재생 중지, 수동 전환만 */
    animation: none;
  }
}
```

---

## 8. 고대비 모드 (prefers-contrast)

```css
@media (prefers-contrast: high) {
  :root {
    --border: #000000;
    --text-primary: #000000;
    --bg-primary: #FFFFFF;
  }
  .btn-primary {
    border: 2px solid #000000;
  }
  .card {
    border: 2px solid #000000;
  }
  .form-input {
    border: 2px solid #000000;
  }
}

/* 강제 색상 모드 (Windows 고대비) */
@media (forced-colors: active) {
  .btn-primary {
    border: 1px solid ButtonText;
    forced-color-adjust: none;
  }
}
```

---

## 9. Alt 텍스트 작성 가이드

### 9.1 규칙

| 이미지 유형 | alt 처리 |
|-----------|---------|
| 정보 전달 이미지 | 이미지가 전달하는 정보를 텍스트로 기술 |
| 장식용 이미지 | `alt=""` 또는 `role="presentation"` |
| 기능적 이미지 (아이콘 버튼) | 기능을 설명 (예: "검색", "닫기") |
| 텍스트가 포함된 이미지 | 이미지 속 텍스트를 alt에 기입 |
| 복잡한 이미지 (차트, 그래프) | 요약 alt + 상세 설명 (aria-describedby) |
| 로고 | 회사명 (예: "삼성 로고") |
| 썸네일/프로필 | 대상 설명 (예: "김철수 프로필 사진") |

### 9.2 좋은/나쁜 예시

```html
<!-- 나쁜 예시 -->
<img src="chart.png" alt="차트">
<img src="photo.jpg" alt="이미지">
<img src="icon.svg"> <!-- alt 없음 -->

<!-- 좋은 예시 -->
<img src="chart.png" alt="2024년 월별 매출 추이: 1월 120만, 6월 최고 350만, 12월 280만">
<img src="photo.jpg" alt="서울 남산타워 야경, 도시 불빛이 반짝이는 풍경">
<img src="decorative.svg" alt="" role="presentation"> <!-- 장식용 -->
<button aria-label="검색"><img src="search.svg" alt=""></button> <!-- 아이콘 버튼 -->
```

---

## 10. 폼 접근성

```html
<!-- 완전한 접근성 폼 예시 -->
<form aria-label="회원가입 폼" novalidate>

  <!-- 필수 필드 -->
  <div class="form-field">
    <label for="name">
      이름 <span aria-hidden="true" class="required">*</span>
      <span class="sr-only">(필수)</span>
    </label>
    <input
      type="text"
      id="name"
      name="name"
      required
      aria-required="true"
      autocomplete="name"
    >
  </div>

  <!-- 에러 상태 -->
  <div class="form-field">
    <label for="email">이메일</label>
    <input
      type="email"
      id="email"
      name="email"
      required
      aria-required="true"
      aria-invalid="true"
      aria-describedby="email-error email-hint"
      autocomplete="email"
    >
    <p id="email-hint" class="form-hint">업무용 이메일을 사용해주세요</p>
    <p id="email-error" class="form-error" role="alert">
      올바른 이메일 형식을 입력해주세요
    </p>
  </div>

  <!-- 비밀번호 (토글) -->
  <div class="form-field">
    <label for="password">비밀번호</label>
    <div class="input-group">
      <input
        type="password"
        id="password"
        name="password"
        required
        aria-required="true"
        aria-describedby="password-requirements"
        autocomplete="new-password"
        minlength="8"
      >
      <button
        type="button"
        aria-label="비밀번호 표시"
        aria-pressed="false"
        onclick="togglePassword()"
      >
        표시
      </button>
    </div>
    <p id="password-requirements" class="form-hint">
      8자 이상, 영문+숫자+특수문자 포함
    </p>
  </div>

  <!-- 라디오 그룹 -->
  <fieldset>
    <legend>알림 수신 방법</legend>
    <label>
      <input type="radio" name="notification" value="email" checked> 이메일
    </label>
    <label>
      <input type="radio" name="notification" value="sms"> SMS
    </label>
    <label>
      <input type="radio" name="notification" value="push"> 푸시 알림
    </label>
  </fieldset>

  <!-- 제출 -->
  <button type="submit">가입하기</button>
</form>
```

---

## 11. 모달 접근성

```html
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
>
  <h2 id="modal-title">계정 삭제</h2>
  <p id="modal-description">
    이 작업은 되돌릴 수 없습니다. 정말 삭제하시겠습니까?
  </p>

  <div class="modal-actions">
    <button type="button" onclick="closeModal()">취소</button>
    <button type="button" class="btn-destructive" onclick="deleteAccount()">삭제</button>
  </div>
</div>

<!-- 배경 콘텐츠 비활성화 -->
<div id="app" aria-hidden="true" inert>
  <!-- ... 앱 콘텐츠 ... -->
</div>
```

**모달 접근성 체크리스트:**
- `role="dialog"` + `aria-modal="true"`
- `aria-labelledby`로 제목 연결
- 포커스 트랩 구현 (Tab이 모달 내부만 순환)
- ESC로 닫기
- 열릴 때: 첫 번째 포커스 가능 요소로 포커스 이동
- 닫힐 때: 트리거 요소로 포커스 복원
- 배경에 `aria-hidden="true"` + `inert` 추가
- 배경 클릭으로 닫기 (확인 대화상자 제외)

---

## 12. 실시간 영역 (aria-live)

```html
<!-- 채팅 메시지 -->
<div aria-live="polite" aria-relevant="additions">
  <div class="message">새 메시지가 도착했습니다</div>
</div>

<!-- 검색 결과 개수 -->
<div aria-live="polite" aria-atomic="true">
  검색 결과: <strong>42</strong>건
</div>

<!-- 폼 유효성 실시간 피드백 -->
<div aria-live="polite">
  <span class="validation-ok">사용 가능한 아이디입니다</span>
</div>

<!-- 타이머/카운트다운 -->
<div aria-live="assertive" aria-atomic="true">
  남은 시간: 2분 30초
</div>

<!-- 로딩 상태 -->
<div aria-live="polite" aria-busy="true">
  데이터를 불러오는 중...
</div>
```

---

## 13. 접근성 테스트 도구

| 도구 | 유형 | 용도 |
|------|------|------|
| axe DevTools | 브라우저 확장 | 자동 WCAG 검사 |
| Lighthouse | Chrome 내장 | 접근성 점수 측정 |
| WAVE | 브라우저 확장 | 시각적 에러 표시 |
| NVDA | 스크린 리더 (Windows) | 실제 스크린 리더 테스트 |
| VoiceOver | 스크린 리더 (macOS/iOS) | 실제 스크린 리더 테스트 |
| Colour Contrast Analyser | 데스크톱 앱 | 대비비 측정 |
| Stark | Figma 플러그인 | 디자인 단계 접근성 검사 |

### 13.1 수동 테스트 체크리스트

1. 키보드만으로 모든 기능 사용 가능한가
2. Tab 순서가 논리적인가
3. 포커스 표시가 보이는가
4. 모든 이미지에 적절한 alt가 있는가
5. 색상 대비가 충분한가
6. 200% 줌에서 콘텐츠가 정상인가
7. 스크린 리더로 읽혔을 때 이해 가능한가
8. 모바일에서 터치 타겟이 충분한가
9. 에러 메시지가 텍스트로 명확한가
10. 동적 콘텐츠 변경이 스크린 리더에 전달되는가
