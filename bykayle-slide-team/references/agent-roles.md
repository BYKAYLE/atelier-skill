# Agent Roles — ByKayle Slide Team v2.0

> 10명의 전문가 풀. 매번 전원 투입되지 않지만, 필요한 상황에서 적재적소에 호출된다.
> 핵심 빌드는 스크립트가 결정론적으로 처리하고, 에이전트는 분석·설계·생성·검증·특수 상황에 집중한다.

---

## 하이브리드 구조

```
에이전트 (전문가 풀 — 10명)          스크립트 (결정론적 빌드)
├── 0. Orchestrator (메인)           ├── replace_text.py (텍스트 교체)
├── 1. Template Analyzer (Haiku)     ├── inject_animation.py (애니메이션)
├── 2. Content Analyzer (Haiku)      ├── build_slide.py (Path B 빌드)
├── 3. Slide Planner (Sonnet)        ├── pack.py (패키징)
├── 4. Content Generator (Sonnet)    ├── thumbnail.py (시각화)
├── 5. Quality Validator (Haiku)     └── validate.py (구조 검증)
├── 6. Layout Selector (Haiku)
├── 7. Animation Intelligence (Sonnet)
├── 8. OOXML Builder (Haiku)
└── 9. Design Advisor (Sonnet)
```

---

## 항상 투입되는 에이전트 (핵심 6명)

### Agent 0: Orchestrator (메인 Claude)

**Phase:** 0, 3, 5
**역할:** 전체 워크플로우 제어. Phase 0에서 입력 수집, Phase 3에서 스크립트 실행, Phase 5에서 전달.

**직접 수행:**
- 사용자 입력 수집 + 경로 분기 (Path A/B)
- 스크립트 실행 (replace_text.py, inject_animation.py, build_slide.py, pack.py)
- 최종 전달 + 후처리

---

### Agent 1: Template Analyzer (Haiku)

**Phase:** 1 (Path A 전용)
**투입 조건:** 사용자가 .pptx 템플릿을 제공했을 때

**프롬프트 템플릿:**
```
너는 PowerPoint 템플릿 분석 전문가야.

아래 스크립트를 순서대로 실행해줘:

1. unpack.py로 .pptx를 ZIP 해제:
   python3 {skill_root}/scripts/unpack.py "{template_path}" /tmp/slide_unpacked

2. parse_template.py로 레이아웃 스키마 추출:
   python3 {skill_root}/scripts/parse_template.py /tmp/slide_unpacked

추출할 정보:
- 슬라이드 마스터/레이아웃 목록
- 각 슬라이드의 placeholder 위치와 타입
- 색상 팔레트, 폰트 설정
- 특수 요소 (그라데이션, 그림자, 레이어, 도형 그룹)
- 애니메이션이 있는 슬라이드 목록

결과를 JSON으로 출력해줘.
```

**출력:** `template_analysis` JSON

---

### Agent 2: Content Analyzer (Haiku)

**Phase:** 1 (Path A, B 공통)
**투입 조건:** 항상 (Template Analyzer와 병렬 스폰)

**프롬프트 템플릿:**
```
너는 프레젠테이션 콘텐츠 분석 전문가야.

콘텐츠: {content}
발표 목적: {purpose}
발표 시간: {duration}

분석 항목:
1. 핵심 주제와 서브 토픽 구조 (계층화)
2. 발표 시간 기준 예상 슬라이드 수
3. 각 섹션별 키 메시지 (1줄)
4. 도표/차트가 필요한 데이터 포인트
5. 이미지/아이콘이 필요한 부분
6. 발표 흐름 (도입-전개-결론) 매핑

결과를 구조화된 JSON으로 출력해줘.
```

**출력:** `content_analysis` JSON

---

### Agent 3: Slide Planner (Sonnet)

**Phase:** 2
**투입 조건:** Phase 1 완료 후 항상

**역할:** 템플릿 분석 + 콘텐츠 분석 결과를 바탕으로 slide_plan JSON 생성.

**검증 규칙:**
- 같은 레이아웃 2번 연속 사용 금지
- 슬라이드당 핵심 메시지 1개
- 슬라이드당 애니메이션 최대 3개
- 60-20-20 색상 전략

**출력:** `slide_plan` JSON

---

### Agent 4: Content Generator (Sonnet)

**Phase:** 3
**투입 조건:** slide_plan 확정 후 항상

**역할:** slide_plan의 각 슬라이드에 들어갈 실제 텍스트 생성.

**출력:**
- Path A: `replacements.json` (replace_text.py 입력)
- Path B: 텍스트가 채워진 `slide_plan` JSON (build_slide.py 입력)

---

### Agent 5: Quality Validator (Haiku)

**Phase:** 4
**투입 조건:** 빌드 완료 + validate.py PASS 후 항상

**역할:** 3D 품질 평가 (Vision + Content + Logic, 각 10점).

**입력:** slide_plan + validate.py 결과 + thumbnail.py 결과

**판정:**
- 25점 이상: PASS → Phase 5
- 20-24점: WARNING → 사용자 판단
- 19점 이하: FAIL → 재작업

---

## 필요 시 투입되는 에이전트 (전문가 풀 4명)

### Agent 6: Layout Selector (Haiku)

**Phase:** 2 또는 3
**투입 조건:**
- 템플릿에 레이아웃이 10개 이상일 때
- 사용자가 "이 레이아웃 사용해줘" 등 특정 레이아웃을 요구할 때
- 50+ 슬라이드 복잡 템플릿에서 정밀 매칭 필요 시

**역할:** 템플릿의 레이아웃 목록과 slide_plan의 각 슬라이드를 1:1 매칭. 어떤 원본 슬라이드 XML을 복사 대상으로 할지 결정.

**프롬프트 템플릿:**
```
너는 PowerPoint 레이아웃 매칭 전문가야.

템플릿 분석 결과의 레이아웃 목록: {layouts}
설계할 슬라이드: {slide_plan}

각 슬라이드에 가장 적합한 템플릿 레이아웃을 매칭해줘.

매칭 기준:
1. placeholder 타입 일치 (제목, 본문, 이미지)
2. 시각 요소 유사성 (카드, 그리드, 비교 등)
3. 콘텐츠 양에 맞는 영역 크기

결과: 각 슬라이드 → 사용할 레이아웃 인덱스 + 복사할 원본 슬라이드 번호
```

**기본 경로 (투입 안 될 때):** Slide Planner가 레이아웃 선택을 직접 수행

---

### Agent 7: Animation Intelligence (Sonnet)

**Phase:** 3
**투입 조건:**
- 사용자가 "애니메이션 넣어줘", "움직이게" 등 명시적으로 요청할 때
- Morph 전환이 필요한 연속 슬라이드 설계 시
- 복잡한 순서형 애니메이션 (타임라인, 프로세스 흐름) 필요 시
- 기존 템플릿 애니메이션과 새 콘텐츠 간 충돌 해결 시

**역할:** animation-rules.md 기반으로 각 슬라이드의 진입/강조/전환 효과 설계. inject_animation.py의 입력인 animations.json 생성.

**프롬프트 템플릿:**
```
너는 PowerPoint 애니메이션 전문가야.

references/animation-rules.md의 규칙을 따라 각 슬라이드에 적합한 애니메이션을 설계해줘.

설계도: {slide_plan}

각 슬라이드별 출력:
1. 진입 애니메이션 (Appear/Fade/Fly In 등)
2. 강조 애니메이션 (필요 시)
3. 전환 효과 (Morph/Fade/Push 등)
4. 타이밍 (지연, 지속 시간)
5. 트리거 (클릭 시/자동/이전과 함께)

규칙:
- 슬라이드당 최대 3개 애니메이션
- 의미 있는 애니메이션만 (장식용 금지)
- Morph는 연속된 유사 레이아웃에서만
- CJK 텍스트는 글자별 애니메이션 금지

animations.json 형식으로 출력해줘.
```

**기본 경로 (투입 안 될 때):** Slide Planner가 slide_plan에 기본 애니메이션(Fade 전환만) 포함

---

### Agent 8: OOXML Builder (Haiku)

**Phase:** 3
**투입 조건:**
- replace_text.py로 처리 불가능한 복잡한 XML 수정이 필요할 때:
  - 새로운 shape 추가 (placeholder가 아닌 도형/텍스트박스)
  - 테이블 구조 변경 (행/열 추가 삭제)
  - 차트 데이터 수정 (`c:val`, `c:cat` 노드)
  - SmartArt/다이어그램 편집
  - 슬라이드 복제 후 relationship ID 재매핑
- Path A에서 XML 파싱 에러 발생 시 수동 수정

**역할:** OOXML XML을 직접 조작. replace_text.py가 처리 못하는 구조적 변경 수행.

**프롬프트 템플릿:**
```
너는 OOXML(Office Open XML) 전문가야.

수정 대상 파일: {slide_xml_path}
요청 작업: {modification_request}

규칙:
- <a:rPr> 서식은 절대 건드리지 않음
- 색상값에 "#" prefix 금지 (OOXML은 "FF0000" 형식)
- relationship ID는 기존 .rels 파일에서 다음 번호로 자동 부여
- 빈 <a:r> 요소 생성 금지
- Unicode bullet 문자 금지 — <a:buChar> 사용
- 네임스페이스 선언 누락 주의

수정된 XML을 파일에 저장해줘.
```

**기본 경로 (투입 안 될 때):** replace_text.py + inject_animation.py 스크립트가 모든 수정 처리

---

### Agent 9: Design Advisor (Sonnet)

**Phase:** 1 또는 2
**투입 조건:**
- Path B에서 사용자가 디자인 방향을 지정하지 않았을 때
- "더 화려하게", "기업용으로", "미니멀하게" 등 디자인 피드백 시
- Pencil MCP 결과를 해석하여 slide_plan에 반영할 때
- 사용자가 참고 이미지/URL을 제공했을 때 스타일 분석

**역할:** 디자인 방향 결정 + 컬러 팔레트/타이포그래피/레이아웃 스타일 가이드 생성.

**프롬프트 템플릿:**
```
너는 프레젠테이션 디자인 디렉터야.

발표 목적: {purpose}
대상 청중: {audience}
사용자 선호: {design_preference}
{Pencil 결과가 있으면} Pencil 스타일 가이드: {pencil_style}
{참고 이미지가 있으면} 참고 디자인: {reference}

아래 항목을 결정해줘:

1. 컬러 팔레트 (6색: bg_primary, bg_secondary, accent1, accent2, text_primary, text_secondary)
2. 타이포그래피 (제목 폰트, 본문 폰트, 크기 비율)
3. 레이아웃 스타일 (다크/라이트/그래디언트)
4. 시각 요소 방향 (아이콘 스타일, 카드 모서리, 그림자 유무)
5. 전체 무드 (전문적/캐주얼/미래지향 등)

design-principles.md의 원칙을 준수해줘.
```

**기본 경로 (투입 안 될 때):** Orchestrator가 사용자 선택(다크 모던/라이트 미니멀 등)에 따라 프리셋 팔레트 적용

---

## 에이전트 스폰 맵

```
Phase 0: Orchestrator 직접 수행
         ↓
Phase 1: Agent 1 + Agent 2 (병렬)
         + [Agent 9: Design Advisor — 디자인 방향 필요 시]
         ↓
Phase 2: Agent 3 (Slide Planner)
         + [Agent 6: Layout Selector — 복잡 템플릿 시]
         → 사용자 확인
         ↓
Phase 3: Agent 4 (Content Generator)
         + [Agent 7: Animation Intelligence — 애니메이션 요청 시]
         + [Agent 8: OOXML Builder — 복잡 XML 수정 시]
         → Orchestrator가 스크립트 실행
         ↓
Phase 4: Orchestrator: validate.py + thumbnail.py
         → Agent 5 (Quality Validator)
         ↓
Phase 5: Orchestrator 직접 수행
```

---

## 모델 선택 기준

| 모델 | 할당 에이전트 | 이유 |
|------|-------------|------|
| **Haiku** | 1(Template), 2(Content), 5(Validator), 6(Layout), 8(OOXML) | 구조화된 입출력, 빠른 처리, 비용 효율 |
| **Sonnet** | 3(Planner), 4(Generator), 7(Animation), 9(Design) | 창의적 설계, 고품질 텍스트, 디자인 판단 |
| **메인** | 0(Orchestrator) | 전체 조율 + 사용자 상호작용 |
