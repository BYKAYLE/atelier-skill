# 앱 아이콘 디자인 백과사전

> 이 파일은 앱 아이콘 디자인 시 자동 로드되는 핵심 레퍼런스.
> 상세 데이터는 NAS DB 참조: `~/CloudDrives/kansic/KMD/design-db/icon-design/`

---

## 1. macOS 아이콘 규격 (Apple HIG 2025-2026)

### 캔버스 & 치수
- 마스터: **1024×1024px**
- 아이콘 영역: **824×824px** (100px 패딩)
- 출력 크기: 16, 32, 64, 128, 256, 512, 1024 (@1x, @2x)

### Squircle (연속 곡률)
- Apple은 순수 Superellipse가 아닌 **연속 둥근 사각형(Continuous Rounded Rectangle)** 사용
- 큐빅 베지어 곡선, 상수: `1.528665`, `0.63149379`, `0.07491139`
- 코너 라디우스: 824px 기준 ~185.4px (~22.5%)
- 핵심: **곡률 불연속점 없음** → 유기적 느낌

### macOS 26 Liquid Glass
- 다층 깊이 (최대 4 depth group)
- 6 외관 변형: Default, Dark, Clear Light/Dark, Tinted Light/Dark
- Icon Composer (Xcode 26): SVG 레이어 → .icon 파일
- 비준수 아이콘: 회색 테두리 + 20% 축소 + 인식성 80% 저하

### 필수 규칙
| 규칙 | 설명 |
|------|------|
| 정면 시점 | 사용자 정면 |
| 단일 초점 | 하나의 핵심 심볼 |
| 배경 필수 | 투명 배경 금지 |
| 조명 | 좌상단 (10시~12시) |
| 그림자 | 0 12px 28px rgba(0,0,0,0.5) |
| 16px 최적화 | 실루엣만 유지 |
| 다크 모드 | 어두운 배경에서도 명확 |

---

## 2. 심볼 디자인 이론

### Shape Language (형태 언어)
| 형태 | 심리적 의미 |
|------|-----------|
| 원 | 완전, 보호, 동기화 |
| 사각형 | 안정, 신뢰, 저장 |
| 삼각형 | 방향, 에너지, 업로드 |
| 곡선 | 부드러움, 유기적, 구름 |
| 육각형 | 효율, 기술, 네트워크 |

### 게슈탈트 원칙
- **폐합성**: 불완전한 형태도 완성형으로 인식 → 간결한 디자인 가능
- **그림과 배경**: 비-흰색 배경이 안전감 더 강함 (ScienceDirect 2025)
- **유사성**: 선 굵기, 라운딩, 색상 톤 통일
- **근접성**: 요소 간 거리가 의미 결정
- **연속성**: 시선의 자연스러운 흐름

### Golden Ratio (φ = 1.618)
- 구름 구성: R (중앙), 0.618R (좌상), 0.786R (우상)
- 광학적 중심: 기하 중심보다 약간 위 (512, ~490-500)
- 원→사각형 무게 매칭: **112.84% 확대** (sqrt(4/π))
- iCloud: 4개 원, 직경 비율 1:1.6 (황금비)

---

## 3. 색상 이론

### 경쟁사 색상 맵 (클라우드 스토리지)
- **Blue Zone (과밀)**: Dropbox, OneDrive, iCloud, Box, Google Drive
- **미사용**: Purple, Orange, Green-Lime, Pink/Coral
- 추천 차별화: **Purple** (#6D28D9→#A78BFA)

### 그라데이션 규칙
- 방향: 135도 (좌상→우하, macOS 조명 일치)
- 유사색 전환이 자연스러움 (보색 피하기)
- 2색 적정, 3색 최대

### 접근성
- 심볼-배경 대비비: 최소 **3:1** (WCAG)
- 텍스트 대비비: **4.5:1** (AA)
- 적록 색맹 대응: 파랑/보라 계열 안전
- 모노크롬 버전 필수 (Finder 사이드바)

### 색상 심리 통계 (앱 아이콘)
- 파랑: Top 앱의 23% | 흰색/빨강: 각 13%
- 성공 앱의 50%가 그라데이션 사용
- 색상 = 브랜드 인식 최대 80% 향상

---

## 4. 레이아웃 & 크기별 최적화

### Apple 키라인 (1024px 기준)
- 원형: 직경 ~804px
- 사각형: ~728×728px
- Safe Zone: ~80% 영역
- 심볼: 캔버스의 60~80%

### Progressive Detail Reduction
| 크기 | 디테일 수준 |
|------|-----------|
| 1024px | 풀 디테일 |
| 512px | 높은 디테일 유지 |
| 128px | 핵심 형태 중심, 그라데이션 단순화 |
| 32px | 핵심 실루엣만 |
| 16px | 극도 단순화, 1~2색, 최소 1px 선 |

### 스트로크 비율
- 24px: 2px 스트로크, 2px 패딩
- 1024px: ~10% 마진 (~102px), ~80% 콘텐츠
- 모든 스트로크 동일 두께 유지

---

## 5. 프로페셔널 패턴 & 안티패턴

### 필수 테스트 (8-Point)
1. **Silhouette**: 단색 실루엣 인식
2. **Scale**: 16px까지 형태 유지
3. **5-Second**: 5초 내 카테고리 인식
4. **Neighbor**: Dock에서 경쟁 아이콘과 구분
5. **Consistency**: 스트로크/조명/패딩 통일
6. **Color Strategy**: 3색 이하, 경쟁사 밖
7. **Emotion**: 명확한 감정 메시지
8. **Technical**: HIG 규격 준수

### 안티패턴 TOP 10
1. 과도한 디테일 (작은 크기에서 뭉개짐)
2. 텍스트 의존 (16px에서 판독 불가)
3. 투명 배경 (macOS HIG 위반)
4. 5색 이상 (산만)
5. 순수 흰/검 배경 (한쪽 모드에서 사라짐)
6. 경쟁사 동일 색상 (혼동)
7. 여러 메타포 혼합 (정체성 불명)
8. 그림자 과다 (구식)
9. 경쟁사 모방 (법적 문제)
10. 512px에서만 디자인 (16px 미확인)

### 프리미엄 시그널
- 수학적 정밀도 (황금비, 완벽한 대칭)
- 네거티브 스페이스 마스터리
- 16px 우선 설계 → 확대
- 일관된 스트로크 두께
- 경쟁 전략으로서의 색상

---

## 6. 2026 아이콘 디자인 트렌드

> 출처: Envato, DesignRush, IconMaker Studio, UXPilot (2025-2026 리서치 종합)

### 6.1 핵심 트렌드 TOP 5 (검증됨 — G() 프롬프트 포함)

| # | 트렌드 | 시각적 특징 | 타겟 | G() 프롬프트 핵심 키워드 |
|---|--------|-----------|------|----------------------|
| 1 | **Soft 3D / Clay** | 말랑한 클레이 질감, 부드러운 그림자, 파스텔 톤, 터치감 | MZ세대, 라이프스타일, 핀테크 | `puffy inflated 3D clay material, soft matte, marshmallow, gentle rounded shadows, pastel gradient` |
| 2 | **Glassmorphism** | 반투명 유리 레이어, 색수차(chromatic aberration), 프리즘 하이라이트, 깊이감 | 프리미엄, Apple 생태계 | `frosted translucent glass, refraction, chromatic aberration edge glow, prismatic highlights, layered frosted glass panels` |
| 3 | **Aurora/Holographic Gradient** | 오로라/홀로그래픽 흐르는 색상, 이리데슨트 효과, 몽환적 | 크리에이티브, Gen Z | `holographic iridescent aurora borealis gradient, pink purple cyan green shifting colors, dreamy ethereal` |
| 4 | **Retrofuturist Neon** | 네온 글로우, 크롬 메탈, 스캔라인, 80s-Y2K 감성 | 게임, 크리에이티브 도구, Gen Z | `neon pink cyan glowing outline, chrome metallic reflective, 80s retro synthwave Y2K, scan lines, neon light bloom` |
| 5 | **Multi-Material** | 유리+금속+매트 복합 소재, 로즈골드 악센트, 고급 촉감 | 프리미엄, 비즈니스 | `combining premium materials, polished chrome metallic silver, frosted matte glass, rose gold accent, material contrast` |

### 6.2 보조 트렌드 (상황별 적용)

| 트렌드 | 설명 | 적용 시나리오 |
|--------|------|-------------|
| **Hyper-Minimal Line** | 초얇은 단선, 정밀 기하학 | 생산성, SaaS, 프라이버시 앱 |
| **Mascot Icons** | 캐릭터 기반, 감정 표현 | 소셜, 교육, 키즈 앱 |
| **Micro-Illustration** | 세밀한 수공예 일러스트 | 라이프스타일, 여행, 푸드 |
| **Bold Geometric** | 굵은 스트로크, 고대비 컬러 블록 | 피트니스, 유틸리티 |
| **Neo-Brutalism** | 두꺼운 검은 테두리, 충돌하는 색상 | 인디, 크리에이티브, 반항적 브랜드 |
| **Dark Mode First** | 어두운 배경 기본, 빛나는 심볼 | 개발자 도구, 프로 앱 |
| **Noise Gradient** | 그라디언트에 노이즈 텍스처 | 빈티지, 아날로그 감성 |

### 6.3 트렌드 선택 가이드

```
앱 카테고리 분석 → 타겟 사용자 파악 → 트렌드 매칭

라이프스타일/핀테크     → Soft 3D Clay
프리미엄/Apple 생태계   → Glassmorphism / Multi-Material
크리에이티브/Gen Z      → Aurora Gradient / Retrofuturist Neon
생산성/SaaS            → Hyper-Minimal / Bold Geometric
소셜/교육              → Mascot / Micro-Illustration
개발자/프로            → Dark Mode First / Neon
```

### 6.4 Morphism 계층 (2026 현재)
1. **Liquid Glass** — 지배적 (Apple iOS/macOS 26)
2. **Glassmorphism** — 성숙, 주류
3. **Soft 3D / Clay** — 급상승, MZ세대 선호
4. **Multi-Material** — 이머징, 프리미엄 포지셔닝
5. **Neumorphism** — 하락, 니치

### 6.5 플랫폼별 스타일
- **macOS**: Liquid Glass 다층 깊이, 사실적 소재감
- **iOS/iPadOS**: 플랫 + 미세 깊이감, 그라디언트 중심
- **Android**: Material You 적응형, 다이내믹 컬러
- **크로스플랫폼**: 그라디언트 + 단일 심볼 (가장 안전)

### 6.6 A/B 테스트 벤치마크
- 잘 디자인된 아이콘: **+20~25% 설치 증가** (DesignRush 2026)
- 금융 앱 볼드 컬러: **+12% 전환율** (MobileAction 2026)
- 더 진한 보라 + 높은 대비: +7.3% retained installs
- 테스트 기간: 7-10일, 신뢰수준 90%+

---

## 7. 워크플로우

```
Phase 1: Research → 경쟁사 분석, 트렌드 파악
Phase 2: Concept → 메타포 선정, Shape Language, 색상 전략
Phase 3: Geometry → 황금비 그리드, 키라인, 광학 보정
Phase 4: Color → 그라데이션, 대비비, 다크모드
Phase 5: Testing → 8-Point 체크리스트, 다양한 크기
Phase 6: Production → 크기별 최적화, 에셋 생성
```

---

---

## 8. Pencil MCP 앱 아이콘 생성 시스템

> 검증된 프로세스: 5회 반복(v1~v5)에서 도출된 App Store 퀄리티 아이콘 생성 공식.
> 이 섹션을 따르면 첫 시도에서 프로페셔널 수준의 아이콘 시안을 생성할 수 있다.

### 8.1 생성 방식: G() AI 이미지 생성 (필수)

**수동 Shape 구성은 사용하지 않는다.**
- 수동 구성(overlapping ellipses, path, gradients)은 "0점 디자인" 수준
- G() AI 이미지 생성이 유일하게 App Store 수준 퀄리티를 달성함

### 8.2 프레임 설정

```
프레임 크기: 512×512px (또는 1024×1024px)
cornerRadius: 115 (512px 기준) / 230 (1024px 기준) → iOS Squircle 근사
clip: true (필수 — 라운드 클리핑)
```

**구조 예시:**
```javascript
section=I(document,{type:"frame",name:"APP ICONS",x:0,y:{Y},width:3200,height:750,layout:"vertical",gap:20,padding:20})
title=I(section,{type:"text",content:"App Icon Concepts",fontSize:36,fontWeight:700,fill:"#1E1B4B"})
row=I(section,{type:"frame",name:"Icon Row",layout:"horizontal",gap:40,placeholder:true})
c1=I(row,{type:"frame",name:"Concept 1",width:512,height:512,cornerRadius:115,clip:true})
```

### 8.3 프롬프트 공식 (검증됨)

**필수 구조:**
```
[플랫폼] app icon for [앱 설명].
[색상/그라디언트 설명] background [that extends to all edges].
[흰색/컬러] [심볼 설명].
No border, no outline, no text.
Clean flat modern [플랫폼] app icon style.
Square format filling entire frame.
```

**플랫폼별 키워드:**
| 플랫폼 | 필수 키워드 |
|--------|-----------|
| iOS/Android | `iOS app icon`, `mobile app icon`, `flat modern design like top App Store apps` |
| macOS | `macOS app icon`, `3D rendered`, `realistic material`, `subtle depth` |

**실패 방지 필수 키워드:**
- `No border, no outline` — 흰색 테두리 방지
- `no text` — 텍스트 혼입 방지
- `that extends to all edges with no margin` — 배경 여백 방지
- `Square format filling entire frame` — 전체 프레임 채움

### 8.4 색상 다양성 가이드

**하나의 색상에 고정하지 않는다.** 5종 시안은 반드시 5가지 다른 컬러 톤을 사용한다.

| 컬러 팔레트 | 그라디언트 설명 예시 | 분위기 |
|-----------|------------------|--------|
| Golden Amber | `warm golden amber to deep honey gradient` | 고급, 따뜻함 |
| Ocean Blue-Teal | `ocean blue to teal gradient, smooth transition` | 시원, 신뢰 |
| Multicolor | `white background, overlapping colorful segments in blue, green, pink, orange` | 유쾌, 크리에이티브 |
| Midnight Neon | `dark navy black background, glowing neon cyan and electric blue` | 프리미엄, 다크모드 |
| Coral-Orange | `warm coral pink to soft orange gradient` | 따뜻, 친근 |
| Purple-Violet | `deep purple to violet gradient` | 차별화, 혁신 |
| Fresh Green | `bright green to mint gradient` | 자연, 성장 |
| Rose-Magenta | `soft rose to magenta gradient` | 모던, 세련 |

**경쟁사 색상 회피 원칙:**
- 클라우드 스토리지: Blue 과밀 → Purple/Gold/Coral 추천
- 생산성: Gray/Blue 과밀 → Green/Orange 추천
- 카테고리별 기존 앱들의 색상 분석 후 차별화 색상 선택

### 8.5 실행 규칙

1. **G() 호출은 반드시 1개씩** — 한 번에 여러 G() 배치 시 MCP 에러 발생
2. **batch_design 호출당 G() 1개** — 안정적 생성 보장
3. **생성 후 반드시 get_screenshot 검증** — 테두리, 배경 잔상, 품질 확인
4. **검증 실패 시 프롬프트 보강 후 재생성** — 같은 nodeId에 G() 재호출하면 덮어쓰기됨

### 8.6 검증 체크리스트

생성된 각 아이콘에 대해 스크린샷 후 확인:

| # | 항목 | FAIL 시 대응 |
|---|------|-----------|
| 1 | 흰색/회색 테두리 없음 | 프롬프트에 `extends to all edges with no border` 추가 후 재생성 |
| 2 | 외부 배경 잔상 없음 (홈화면 등) | 프롬프트에서 mockup/phone 관련 단어 제거, `isolated icon only` 추가 |
| 3 | 텍스트 없음 | `no text, no letters, no words` 강화 |
| 4 | 심볼이 명확히 인식됨 | 심볼 설명을 더 구체적으로 |
| 5 | 색상이 의도와 일치 | 색상 키워드를 더 구체적으로 (HEX 참조 가능) |
| 6 | 5종 간 컬러 다양성 확보 | 동일 색상 톤이 2개 이상이면 하나 교체 |
| 7 | iOS/Android 앱 아이콘 느낌 | `flat modern mobile app icon` 키워드 확인 |

### 8.7 실패 사례 & 교훈 (v1~v5 기록)

| 버전 | 접근 | 결과 | 교훈 |
|------|------|------|------|
| v1 | 수동 Shape (ellipse, path 조합) | "0점" — 아마추어 수준 | 수동 구성으로는 App Store 퀄리티 불가 |
| v2 | 수동 + 머티리얼 (radial gradient, 3D volume, shadow) | "심볼 느낌" — 아이콘이 아닌 아이콘 | 머티리얼 추가해도 수동 한계 |
| v3 | G() AI 생성 + macOS 스타일 프롬프트 | macOS 전용 — 사용자는 iOS 원함 | 플랫폼 명시 필수 |
| v4 | G() AI + iOS 프롬프트, 보라색 고정 | 품질 OK, 색상 단조 + 일부 테두리 | 색상 다양성 + 테두리 방지 키워드 필요 |
| v5 | G() AI + 다양한 컬러 + 강화 프롬프트 | App Store 퀄리티 달성 | 최종 공식 확립 |

### 8.8 전체 워크플로우 요약

```
1. 앱 정보 파악 → 앱 이름, 기능, 플랫폼, 경쟁사
2. 색상 전략 → 경쟁사 색상 분석 → 차별화 5색 선정
3. 프레임 생성 → 512×512, cornerRadius:115, clip:true × 5개
4. G() 생성 → 검증된 프롬프트 공식 사용, 1개씩 순차 실행
5. 스크린샷 검증 → 7-Point 체크리스트
6. FAIL 아이콘 재생성 → 프롬프트 보강
7. 사용자 피드백 → 선택된 방향으로 변형/확장
8. .pen 파일 저장 → 서비스 폴더에 작업 파일 백업 (§8.9)
```

### 8.9 .pen 작업 파일 저장 규칙

**Pencil MCP로 디자인 작업 시, 세션 마지막에 반드시 .pen 파일을 서비스 폴더에 저장한다.**

#### 저장 위치
```
{프로젝트 루트}/design/{서비스명}-icons.pen
```
예: `~/Service/ByDrive/design/cloudfuse-icons.pen`

#### 저장 방법
Pencil의 .pen 데이터는 Antigravity 워크스페이스 스토리지에 JSON으로 저장된다:
```
~/Library/Application Support/Antigravity/User/workspaceStorage/{workspace-hash}/highagency.pencildev/{document-hash}
```

**저장 절차:**
1. 워크스페이스 스토리지에서 `highagency.pencildev/` 하위 파일을 찾는다
2. JSON 파싱하여 현재 편집 중인 문서의 노드 ID와 대조한다 (batch_get으로 확인)
3. 해당 파일을 `{프로젝트}/design/{서비스명}-icons.pen`으로 복사 (pretty-print JSON)

```python
import json, os
# 1. 소스 파일 찾기
src_dir = os.path.expanduser(
    "~/Library/Application Support/Antigravity/User/workspaceStorage"
)
# workspaceStorage 내 highagency.pencildev 디렉토리 탐색
# 2. 노드 ID 대조로 올바른 파일 식별
# 3. pretty-print로 저장
with open(src, 'r') as f:
    data = json.load(f)
with open(dst, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

#### 실행 규칙
- **타이밍**: 디자인 작업이 모두 끝난 후 마지막에 1회 저장
- **덮어쓰기**: 같은 서비스의 기존 .pen 파일이 있으면 덮어쓴다 (최신 상태 유지)
- **저장 후 원본 복귀**: 저장 검증을 위해 open_document로 열었다면, 반드시 원본 pencil-new.pen으로 복귀

---

## NAS DB 상세 참조
- 종합: `~/CloudDrives/kansic/KMD/design-db/icon-design/app-icon-design-bible.md`
- 학술: `~/CloudDrives/kansic/KMD/design-db/icon-design/academic-research.md`
