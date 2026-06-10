# 색상 체계 백과사전

## 1. 색상 이론

### 1.1 색상환 (Color Wheel)

12색 색상환 기준 주요 관계:

| 관계 | 설명 | 예시 |
|------|------|------|
| 보색 (Complementary) | 정반대 위치 | 파랑 #3B82F6 ↔ 주황 #F97316 |
| 유사색 (Analogous) | 인접 3색 | 파랑 #3B82F6, 남색 #6366F1, 청록 #06B6D4 |
| 삼색 조화 (Triadic) | 120도 간격 3색 | 빨강 #EF4444, 파랑 #3B82F6, 노랑 #EAB308 |
| 분할 보색 (Split-Complementary) | 보색의 양옆 | 파랑 #3B82F6 + 빨주 #F43F5E + 주황 #F97316 |
| 사각 조화 (Tetradic) | 4색 조화 | 파랑, 보라, 주황, 노랑 |
| 단색 조화 (Monochromatic) | 한 색의 명도/채도 변주 | #DBEAFE → #93C5FD → #3B82F6 → #1D4ED8 → #1E3A8A |

### 1.2 색상 속성

| 속성 | 설명 | UI 활용 |
|------|------|--------|
| 색상 (Hue) | 색의 종류 (0~360도) | 브랜드 정체성, 카테고리 구분 |
| 채도 (Saturation) | 색의 선명도 (0~100%) | 높으면 활발, 낮으면 차분 |
| 명도 (Lightness) | 밝기 (0~100%) | 계층 구분, 상태 표현 |

---

## 2. 색상 심리학

### 2.1 색상별 심리적 효과

| 색상 | 긍정적 | 부정적 | 적합 산업 |
|------|--------|--------|----------|
| 파랑 (#3B82F6) | 신뢰, 안정, 전문성 | 차가움, 무미건조 | 금융, IT, 의료, 기업 |
| 초록 (#10B981) | 성장, 건강, 자연 | 미숙, 지루함 | 헬스, 환경, 금융(수익) |
| 빨강 (#EF4444) | 열정, 긴급, 에너지 | 위험, 공격적 | 푸드, 엔터, 세일 |
| 주황 (#F97316) | 따뜻함, 친근, 활력 | 유치함 | 푸드, 여행, 크리에이티브 |
| 노랑 (#EAB308) | 낙관, 주의, 창의 | 불안, 경고 | 어린이, 크리에이티브 |
| 보라 (#8B5CF6) | 고급, 창의, 신비 | 인위적 | 럭셔리, 테크, 뷰티 |
| 분홍 (#EC4899) | 부드러움, 로맨스, 현대적 | 유치함 | 뷰티, 패션, 웨딩 |
| 검정 (#111827) | 고급, 권위, 세련 | 무거움, 억압 | 럭셔리, 패션, 테크 |
| 흰색 (#FFFFFF) | 깨끗, 단순, 현대적 | 공허, 차가움 | 의료, 미니멀, 테크 |
| 회색 (#6B7280) | 중립, 균형, 전문 | 무관심 | 기업, B2B, 뉴스 |
| 청록 (#06B6D4) | 소통, 명확, 혁신 | — | 테크, SaaS, 미디어 |

### 2.2 산업별 색상 심리

| 산업 | 주요 색상 | 이유 |
|------|----------|------|
| 금융/핀테크 | 파랑, 짙은 녹색, 네이비 | 신뢰, 안정, 보안 |
| 헬스케어 | 파랑, 녹색, 흰색 | 청결, 건강, 전문성 |
| 푸드/배달 | 빨강, 주황, 노랑 | 식욕, 따뜻함, 긴급 |
| 테크/SaaS | 파랑, 보라, 청록 | 혁신, 신뢰, 현대 |
| 교육 | 파랑, 녹색, 주황 | 신뢰, 성장, 활력 |
| 럭셔리 | 검정, 금색, 보라 | 고급, 권위, 세련 |
| 환경/에코 | 녹색, 갈색, 하늘색 | 자연, 지속가능 |
| 어린이 | 밝은 원색들 | 즐거움, 호기심 |
| 부동산 | 파랑, 녹색, 갈색 | 신뢰, 안정, 자연 |
| 미디어/뉴스 | 빨강, 파랑, 검정 | 긴급, 권위, 무게감 |

---

## 3. 라이트/다크 모드 색상 전환 규칙

### 3.1 전환 원칙

| 요소 | 라이트 모드 | 다크 모드 | 규칙 |
|------|-----------|----------|------|
| 배경 | #FFFFFF | #0F172A | 완전 흰 → 완전 검정 아닌 짙은 네이비/회색 |
| 표면 | #F8FAFC | #1E293B | 라이트보다 한 단계 밝은 어두운 색 |
| 카드 배경 | #FFFFFF | #1E293B | 배경보다 한 단계 밝게 |
| 일반 텍스트 | #111827 | #F1F5F9 | 충분한 대비, 순백은 피함 |
| 보조 텍스트 | #6B7280 | #94A3B8 | 살짝 밝게 |
| 테두리 | #E5E7EB | #334155 | 어둡게 |
| Primary | #3B82F6 | #60A5FA | 살짝 밝게 (채도 유지) |
| Success | #10B981 | #34D399 | 살짝 밝게 |
| Warning | #F59E0B | #FBBF24 | 살짝 밝게 |
| Error | #EF4444 | #F87171 | 살짝 밝게 |

### 3.2 다크 모드 CSS 변수

```css
:root {
  /* 라이트 모드 (기본) */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8FAFC;
  --bg-tertiary: #F1F5F9;
  --surface: #FFFFFF;
  --surface-hover: #F8FAFC;
  --text-primary: #111827;
  --text-secondary: #4B5563;
  --text-tertiary: #6B7280;
  --text-quaternary: #9CA3AF;
  --border: #E5E7EB;
  --border-hover: #D1D5DB;
  --ring: #3B82F6;
  --shadow: rgba(0, 0, 0, 0.1);
}

[data-theme="dark"] {
  --bg-primary: #0F172A;
  --bg-secondary: #1E293B;
  --bg-tertiary: #334155;
  --surface: #1E293B;
  --surface-hover: #334155;
  --text-primary: #F1F5F9;
  --text-secondary: #CBD5E1;
  --text-tertiary: #94A3B8;
  --text-quaternary: #64748B;
  --border: #334155;
  --border-hover: #475569;
  --ring: #60A5FA;
  --shadow: rgba(0, 0, 0, 0.4);
}

/* 시스템 설정 따르기 */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg-primary: #0F172A;
    --bg-secondary: #1E293B;
    --bg-tertiary: #334155;
    --surface: #1E293B;
    --surface-hover: #334155;
    --text-primary: #F1F5F9;
    --text-secondary: #CBD5E1;
    --text-tertiary: #94A3B8;
    --text-quaternary: #64748B;
    --border: #334155;
    --border-hover: #475569;
    --ring: #60A5FA;
    --shadow: rgba(0, 0, 0, 0.4);
  }
}
```

### 3.3 다크 모드 금지사항
- 순수 검정(#000000)을 배경으로 쓰지 않는다 → #0F172A, #1A1A2E 등 사용
- 순수 흰색(#FFFFFF)을 텍스트로 쓰지 않는다 → #F1F5F9, #E2E8F0 등 사용
- 그림자를 밝게 바꾸지 않는다 → 투명도를 높여 더 진한 그림자 사용
- Primary 색상을 그대로 유지하면 너무 어둡게 보일 수 있다 → 밝기를 1~2단계 올린다

---

## 4. WCAG 2.1 대비비 규칙

### 4.1 기준

| 레벨 | 일반 텍스트 | 대형 텍스트 (18px+ 또는 14px+ Bold) |
|------|-----------|----------------------------------|
| AA | 4.5:1 | 3:1 |
| AAA | 7:1 | 4.5:1 |
| UI 컴포넌트 | 3:1 | — |

### 4.2 대비비 통과하는 색상 조합

```
배경 #FFFFFF에서:
  ✅ #111827 (15.39:1) — 제목, 본문
  ✅ #374151 (10.14:1) — 본문
  ✅ #4B5563 (7.46:1) — AAA 통과
  ✅ #6B7280 (4.97:1) — AA 통과
  ❌ #9CA3AF (3.29:1) — AA 미달 (대형만 가능)
  ❌ #D1D5DB (1.87:1) — 장식용만 가능

배경 #0F172A (다크모드)에서:
  ✅ #F1F5F9 (14.02:1) — 제목, 본문
  ✅ #CBD5E1 (10.11:1) — 본문
  ✅ #94A3B8 (6.26:1) — AA 통과
  ❌ #64748B (3.83:1) — 대형만 가능
  ❌ #475569 (2.52:1) — 장식용만 가능
```

### 4.3 대비비 계산 도구
- Chrome DevTools: Elements 탭에서 색상 클릭
- Figma: Stark 플러그인
- 온라인: https://webaim.org/resources/contrastchecker/

---

## 5. 시맨틱 컬러 (Semantic Colors)

| 용도 | 색상 | 헥스코드 | 사용처 |
|------|------|---------|--------|
| Success | 초록 | #10B981 (bg: #ECFDF5) | 성공 메시지, 완료, 온라인 상태 |
| Warning | 주황/노랑 | #F59E0B (bg: #FFFBEB) | 경고, 주의, 보류 상태 |
| Error | 빨강 | #EF4444 (bg: #FEF2F2) | 에러, 삭제, 실패 |
| Info | 파랑 | #3B82F6 (bg: #EFF6FF) | 정보, 도움말, 알림 |

```css
/* 시맨틱 컬러 시스템 */
:root {
  /* Success */
  --success-50: #ECFDF5;
  --success-100: #D1FAE5;
  --success-200: #A7F3D0;
  --success-500: #10B981;
  --success-600: #059669;
  --success-700: #047857;

  /* Warning */
  --warning-50: #FFFBEB;
  --warning-100: #FEF3C7;
  --warning-200: #FDE68A;
  --warning-500: #F59E0B;
  --warning-600: #D97706;
  --warning-700: #B45309;

  /* Error */
  --error-50: #FEF2F2;
  --error-100: #FEE2E2;
  --error-200: #FECACA;
  --error-500: #EF4444;
  --error-600: #DC2626;
  --error-700: #B91C1C;

  /* Info */
  --info-50: #EFF6FF;
  --info-100: #DBEAFE;
  --info-200: #BFDBFE;
  --info-500: #3B82F6;
  --info-600: #2563EB;
  --info-700: #1D4ED8;
}
```

---

## 6. 뉴트럴 팔레트 생성법 (50~950 스케일)

### 6.1 Slate (차가운 회색 — 기본 추천)
```css
--slate-50: #F8FAFC;
--slate-100: #F1F5F9;
--slate-200: #E2E8F0;
--slate-300: #CBD5E1;
--slate-400: #94A3B8;
--slate-500: #64748B;
--slate-600: #475569;
--slate-700: #334155;
--slate-800: #1E293B;
--slate-900: #0F172A;
--slate-950: #020617;
```

### 6.2 Gray (순수 회색)
```css
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
--gray-950: #030712;
```

### 6.3 Zinc (따뜻한 회색)
```css
--zinc-50: #FAFAFA;
--zinc-100: #F4F4F5;
--zinc-200: #E4E4E7;
--zinc-300: #D4D4D8;
--zinc-400: #A1A1AA;
--zinc-500: #71717A;
--zinc-600: #52525B;
--zinc-700: #3F3F46;
--zinc-800: #27272A;
--zinc-900: #18181B;
--zinc-950: #09090B;
```

### 6.4 뉴트럴 선택 가이드
| 앱 분위기 | 추천 뉴트럴 | 이유 |
|----------|-----------|------|
| 차분하고 전문적 | Slate | 약간의 파란 톤이 전문성 부여 |
| 중립적 | Gray | 가장 무채색에 가까움 |
| 따뜻하고 친근 | Zinc | 약간의 따뜻한 톤 |
| 매우 따뜻한 | Stone | 갈색 톤의 회색 |

---

## 7. CTA 색상 전략

### 7.1 CTA 색상 규칙

| 규칙 | 설명 |
|------|------|
| 보색 활용 | 배경의 보색을 CTA에 사용하면 가장 눈에 띔 |
| 고채도 | CTA는 주변보다 채도가 높아야 함 |
| 크기 차별화 | 1차 CTA > 2차 CTA > 3차 CTA |
| 한 화면 1개 | 주요 CTA는 화면당 1개만 |
| 반복 배치 | 랜딩 페이지에서 CTA를 스크롤 위치마다 반복 |

### 7.2 CTA 상태별 색상

```css
/* Primary CTA */
.btn-cta {
  background: #3B82F6;
  color: #FFFFFF;
}
.btn-cta:hover {
  background: #2563EB; /* 한 단계 어둡게 */
}
.btn-cta:active {
  background: #1D4ED8; /* 두 단계 어둡게 */
}
.btn-cta:focus-visible {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
}
.btn-cta:disabled {
  background: #93C5FD;
  cursor: not-allowed;
}
```

---

## 8. 그라데이션 사용 가이드

### 8.1 효과적인 그라데이션

```css
/* 미묘한 그라데이션 (배경) */
.gradient-subtle {
  background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
}

/* 따뜻한 그라데이션 */
.gradient-warm {
  background: linear-gradient(135deg, #F093FB 0%, #F5576C 100%);
}

/* 차가운 그라데이션 */
.gradient-cool {
  background: linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%);
}

/* 일몰 그라데이션 */
.gradient-sunset {
  background: linear-gradient(135deg, #FA709A 0%, #FEE140 100%);
}

/* 오로라 그라데이션 */
.gradient-aurora {
  background: linear-gradient(135deg, #A9F1DF 0%, #FFBBBB 100%);
}

/* 다크모드 그라데이션 */
.gradient-dark {
  background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
}

/* 메시 그라데이션 (최신 트렌드) */
.gradient-mesh {
  background:
    radial-gradient(at 40% 20%, #3B82F6 0px, transparent 50%),
    radial-gradient(at 80% 0%, #8B5CF6 0px, transparent 50%),
    radial-gradient(at 0% 50%, #06B6D4 0px, transparent 50%);
}
```

### 8.2 그라데이션 규칙
- 인접 색상 사이의 그라데이션이 가장 자연스럽다 (유사색)
- 보색 그라데이션은 중간에 탁한 색이 나타남 → 중간 색상을 추가하여 해결
- 텍스트 위의 그라데이션은 가독성 확보 필수 (오버레이 또는 text-shadow)
- 그라데이션 각도: 135deg (좌상→우하)가 가장 자연스러움
- 그라데이션은 2~3색이 적정, 4색 이상은 혼란

---

## 9. 브랜드 컬러에서 팔레트 확장하는 공식

### 9.1 단일 브랜드 컬러에서 10단계 팔레트 생성

브랜드 컬러 예시: #3B82F6 (파랑)

```
방법: HSL 기반 명도 조절

#3B82F6 → HSL(217, 91%, 60%)

50:  HSL(217, 91%, 97%) → #EFF6FF (배경)
100: HSL(217, 91%, 93%) → #DBEAFE
200: HSL(217, 91%, 85%) → #BFDBFE
300: HSL(217, 91%, 74%) → #93C5FD
400: HSL(217, 91%, 67%) → #60A5FA
500: HSL(217, 91%, 60%) → #3B82F6 (브랜드 원색)
600: HSL(217, 91%, 51%) → #2563EB
700: HSL(217, 91%, 42%) → #1D4ED8
800: HSL(217, 91%, 33%) → #1E40AF
900: HSL(217, 91%, 24%) → #1E3A8A
950: HSL(217, 91%, 14%) → #172554
```

### 9.2 확장 공식

| 단계 | 명도 조절 | 채도 조절 | 용도 |
|------|----------|----------|------|
| 50 | +37% | -10% | 매우 밝은 배경 |
| 100 | +33% | -5% | 밝은 배경 |
| 200 | +25% | 0% | 호버 배경 |
| 300 | +14% | 0% | 테두리 (활성) |
| 400 | +7% | 0% | 아이콘, 보조 |
| 500 | 0% | 0% | 원색 (버튼, 링크) |
| 600 | -9% | +5% | 호버 상태 |
| 700 | -18% | +5% | 클릭 상태 |
| 800 | -27% | 0% | 텍스트 (강조) |
| 900 | -36% | 0% | 텍스트 (제목) |
| 950 | -46% | 0% | 다크모드 배경 |

---

## 10. 산업별 추천 팔레트

### 10.1 SaaS / 프로덕트
```css
:root {
  --primary: #3B82F6;      /* 파랑 — 신뢰, 전문 */
  --primary-hover: #2563EB;
  --secondary: #8B5CF6;     /* 보라 — 혁신, 차별화 */
  --accent: #06B6D4;        /* 청록 — 보조 강조 */
  --bg-page: #F8FAFC;
  --bg-card: #FFFFFF;
  --text-primary: #0F172A;
  --text-secondary: #475569;
  --border: #E2E8F0;
}
```

### 10.2 핀테크 / 뱅킹
```css
:root {
  --primary: #1E3A5F;      /* 네이비 — 신뢰, 보안 */
  --primary-hover: #162D4A;
  --secondary: #10B981;     /* 녹색 — 수익, 성장 */
  --accent: #F59E0B;        /* 금색 — 프리미엄 */
  --bg-page: #F9FAFB;
  --bg-card: #FFFFFF;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --border: #E5E7EB;
  --negative: #EF4444;      /* 손실/하락 */
  --positive: #10B981;      /* 이익/상승 */
}
```

### 10.3 헬스케어 / 메디컬
```css
:root {
  --primary: #0EA5E9;      /* 하늘파랑 — 청결, 신뢰 */
  --primary-hover: #0284C7;
  --secondary: #10B981;     /* 녹색 — 건강 */
  --accent: #8B5CF6;        /* 보라 — 전문성 */
  --bg-page: #F0F9FF;
  --bg-card: #FFFFFF;
  --text-primary: #0C4A6E;
  --text-secondary: #64748B;
  --border: #E0F2FE;
}
```

### 10.4 이커머스
```css
:root {
  --primary: #111827;      /* 검정 — 세련, 고급 */
  --primary-hover: #1F2937;
  --secondary: #F97316;     /* 주황 — CTA, 세일 */
  --accent: #EF4444;        /* 빨강 — 할인, 긴급 */
  --bg-page: #FFFFFF;
  --bg-card: #F9FAFB;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --border: #E5E7EB;
  --sale: #EF4444;
  --new: #3B82F6;
}
```

### 10.5 교육 / LMS
```css
:root {
  --primary: #4F46E5;      /* 인디고 — 학습, 집중 */
  --primary-hover: #4338CA;
  --secondary: #10B981;     /* 녹색 — 진행, 완료 */
  --accent: #F59E0B;        /* 노랑 — 주의, 보상 */
  --bg-page: #F5F3FF;
  --bg-card: #FFFFFF;
  --text-primary: #1E1B4B;
  --text-secondary: #6B7280;
  --border: #E9E5FF;
  --progress: #10B981;
  --badge: #F59E0B;
}
```

### 10.6 푸드 / 배달
```css
:root {
  --primary: #EF4444;      /* 빨강 — 식욕, 열정 */
  --primary-hover: #DC2626;
  --secondary: #F97316;     /* 주황 — 따뜻함 */
  --accent: #EAB308;        /* 노랑 — 밝음 */
  --bg-page: #FFFBEB;
  --bg-card: #FFFFFF;
  --text-primary: #1C1917;
  --text-secondary: #78716C;
  --border: #FDE68A;
}
```

### 10.7 소셜 / 커뮤니티
```css
:root {
  --primary: #8B5CF6;      /* 보라 — 창의, 커뮤니티 */
  --primary-hover: #7C3AED;
  --secondary: #EC4899;     /* 핑크 — 좋아요, 감성 */
  --accent: #06B6D4;        /* 청록 — 소통 */
  --bg-page: #FAFAFA;
  --bg-card: #FFFFFF;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --border: #E5E7EB;
}
```

### 10.8 미디어 / 콘텐츠
```css
:root {
  --primary: #DC2626;      /* 빨강 — 긴급, 주목 */
  --primary-hover: #B91C1C;
  --secondary: #1F2937;     /* 어둡 — 무게감 */
  --accent: #FBBF24;        /* 금색 — 프리미엄 */
  --bg-page: #FFFFFF;
  --bg-card: #F9FAFB;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --border: #E5E7EB;
}
```

### 10.9 여행 / 예약
```css
:root {
  --primary: #0891B2;      /* 청록 — 바다, 여행 */
  --primary-hover: #0E7490;
  --secondary: #F97316;     /* 주황 — 따뜻함, 일몰 */
  --accent: #10B981;        /* 녹색 — 자연 */
  --bg-page: #ECFEFF;
  --bg-card: #FFFFFF;
  --text-primary: #164E63;
  --text-secondary: #6B7280;
  --border: #CFFAFE;
}
```

### 10.10 부동산
```css
:root {
  --primary: #1D4ED8;      /* 진파랑 — 신뢰 */
  --primary-hover: #1E40AF;
  --secondary: #059669;     /* 녹색 — 자연, 안정 */
  --accent: #D97706;        /* 갈금색 — 가치 */
  --bg-page: #F9FAFB;
  --bg-card: #FFFFFF;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --border: #E5E7EB;
}
```

### 10.11 CRM / 어드민
```css
:root {
  --primary: #4F46E5;      /* 인디고 — 전문, 체계 */
  --primary-hover: #4338CA;
  --secondary: #0891B2;     /* 청록 — 정보 */
  --accent: #F59E0B;        /* 노랑 — 경고, 주의 */
  --bg-page: #F1F5F9;
  --bg-card: #FFFFFF;
  --text-primary: #0F172A;
  --text-secondary: #475569;
  --border: #E2E8F0;
}
```

### 10.12 프로젝트 관리
```css
:root {
  --primary: #6366F1;      /* 보라-파랑 — 협업 */
  --primary-hover: #4F46E5;
  --secondary: #14B8A6;     /* 청록 — 진행 */
  --accent: #F43F5E;        /* 로즈 — 긴급 */
  --bg-page: #F8FAFC;
  --bg-card: #FFFFFF;
  --text-primary: #1E1B4B;
  --text-secondary: #64748B;
  --border: #E2E8F0;
  --status-todo: #6B7280;
  --status-progress: #3B82F6;
  --status-review: #F59E0B;
  --status-done: #10B981;
}
```

### 10.13 분석 / BI
```css
:root {
  --primary: #1E3A8A;      /* 짙은 파랑 — 데이터, 분석 */
  --primary-hover: #1E40AF;
  --secondary: #7C3AED;     /* 보라 — 인사이트 */
  --accent: #06B6D4;        /* 청록 — 대시보드 */
  --bg-page: #F1F5F9;
  --bg-card: #FFFFFF;
  --text-primary: #0F172A;
  --text-secondary: #64748B;
  --border: #E2E8F0;
  /* 차트 색상 팔레트 */
  --chart-1: #3B82F6;
  --chart-2: #8B5CF6;
  --chart-3: #EC4899;
  --chart-4: #F59E0B;
  --chart-5: #10B981;
  --chart-6: #06B6D4;
  --chart-7: #F97316;
  --chart-8: #6366F1;
}
```

### 10.14 IoT / 모니터링
```css
:root {
  --primary: #06B6D4;      /* 청록 — 테크, 실시간 */
  --primary-hover: #0891B2;
  --secondary: #10B981;     /* 녹색 — 정상 */
  --accent: #EF4444;        /* 빨강 — 알림 */
  --bg-page: #0F172A;       /* 다크 기본 */
  --bg-card: #1E293B;
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --border: #334155;
  --status-ok: #10B981;
  --status-warn: #F59E0B;
  --status-critical: #EF4444;
  --status-offline: #6B7280;
}
```

### 10.15 럭셔리 / 프리미엄
```css
:root {
  --primary: #111827;      /* 검정 — 고급 */
  --primary-hover: #1F2937;
  --secondary: #D4AF37;     /* 금색 — 프리미엄 */
  --accent: #7C3AED;        /* 보라 — 럭셔리 */
  --bg-page: #FAFAF9;
  --bg-card: #FFFFFF;
  --text-primary: #111827;
  --text-secondary: #57534E;
  --border: #D6D3D1;
}
```

### 10.16 어린이 / 키즈
```css
:root {
  --primary: #3B82F6;      /* 밝은 파랑 */
  --secondary: #F97316;     /* 주황 */
  --accent: #10B981;        /* 녹색 */
  --highlight: #EAB308;     /* 노랑 */
  --fun: #EC4899;           /* 핑크 */
  --bg-page: #FFF7ED;
  --bg-card: #FFFFFF;
  --text-primary: #1F2937;
  --text-secondary: #6B7280;
  --border: #FDE68A;
}
```

### 10.17 웰니스 / 명상
```css
:root {
  --primary: #7C3AED;      /* 보라 — 영적, 평온 */
  --primary-hover: #6D28D9;
  --secondary: #14B8A6;     /* 청록 — 치유 */
  --accent: #F472B6;        /* 핑크 — 사랑 */
  --bg-page: #FAF5FF;
  --bg-card: #FFFFFF;
  --text-primary: #3B0764;
  --text-secondary: #6B7280;
  --border: #EDE9FE;
}
```

### 10.18 스포츠 / 피트니스
```css
:root {
  --primary: #EF4444;      /* 빨강 — 에너지, 열정 */
  --primary-hover: #DC2626;
  --secondary: #111827;     /* 검정 — 강인 */
  --accent: #F59E0B;        /* 노랑 — 활력 */
  --bg-page: #FFFFFF;
  --bg-card: #F9FAFB;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --border: #E5E7EB;
}
```

### 10.19 법률 / 법무
```css
:root {
  --primary: #1E3A5F;      /* 짙은 네이비 — 권위 */
  --primary-hover: #162D4A;
  --secondary: #7F1D1D;     /* 짙은 빨강 — 격식 */
  --accent: #D4AF37;        /* 금색 — 격조 */
  --bg-page: #FAFAF9;
  --bg-card: #FFFFFF;
  --text-primary: #1C1917;
  --text-secondary: #57534E;
  --border: #D6D3D1;
}
```

### 10.20 게임
```css
:root {
  --primary: #7C3AED;      /* 보라 — 판타지 */
  --primary-hover: #6D28D9;
  --secondary: #06B6D4;     /* 청록 — 미래적 */
  --accent: #F59E0B;        /* 금색 — 보상 */
  --highlight: #EF4444;     /* 빨강 — 체력/위험 */
  --bg-page: #0F172A;       /* 다크 기본 */
  --bg-card: #1E293B;
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --border: #334155;
}
```

---

## 11. CSS 변수 템플릿 (통합)

```css
:root {
  /* === Primary === */
  --primary-50: #EFF6FF;
  --primary-100: #DBEAFE;
  --primary-200: #BFDBFE;
  --primary-300: #93C5FD;
  --primary-400: #60A5FA;
  --primary-500: #3B82F6;
  --primary-600: #2563EB;
  --primary-700: #1D4ED8;
  --primary-800: #1E40AF;
  --primary-900: #1E3A8A;

  /* === Secondary === */
  --secondary-50: #F5F3FF;
  --secondary-100: #EDE9FE;
  --secondary-200: #DDD6FE;
  --secondary-300: #C4B5FD;
  --secondary-400: #A78BFA;
  --secondary-500: #8B5CF6;
  --secondary-600: #7C3AED;
  --secondary-700: #6D28D9;
  --secondary-800: #5B21B6;
  --secondary-900: #4C1D95;

  /* === Neutral === */
  --neutral-50: #F8FAFC;
  --neutral-100: #F1F5F9;
  --neutral-200: #E2E8F0;
  --neutral-300: #CBD5E1;
  --neutral-400: #94A3B8;
  --neutral-500: #64748B;
  --neutral-600: #475569;
  --neutral-700: #334155;
  --neutral-800: #1E293B;
  --neutral-900: #0F172A;

  /* === Semantic === */
  --success: #10B981;
  --warning: #F59E0B;
  --error: #EF4444;
  --info: #3B82F6;

  /* === Surface === */
  --bg-page: var(--neutral-50);
  --bg-card: #FFFFFF;
  --bg-card-hover: var(--neutral-50);
  --text-primary: var(--neutral-900);
  --text-secondary: var(--neutral-600);
  --text-tertiary: var(--neutral-500);
  --text-disabled: var(--neutral-400);
  --border-default: var(--neutral-200);
  --border-hover: var(--neutral-300);
  --ring-focus: var(--primary-500);
}
```
