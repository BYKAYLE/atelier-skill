# Phase 3: Content Generator & Build Scripts

## Agent 4: Content Generator (Sonnet)

```
subagent_type: "general-purpose"
model: "sonnet"
description: "슬라이드 텍스트 생성"
```

**프롬프트:**
```
너는 프레젠테이션 카피라이터야.

slide_plan: {slide_plan}
원본 콘텐츠: {content}

각 슬라이드의 텍스트를 작성해줘:
- 제목: 간결하고 임팩트 있게 (10자 이내 권장)
- 본문: 핵심만 (불릿당 2줄 이내)
- 발표자 노트: 발표자가 실제로 말할 내용 (구어체)

{Path A인 경우}
replacements.json 형식으로 출력 (replace_text.py 입력용):
- placeholder idx 매핑 또는 textbox name 매핑

{Path B인 경우}
slide_plan의 title, subtitle, body 필드를 직접 채워서 반환.

언어: 원본 콘텐츠와 동일한 언어 사용
톤: 발표 목적에 맞게 (IR→임팩트, 사내보고→객관적, 제안→설득력)
```

---

## Agent 7: Animation Intelligence (조건부)

투입 조건:
- 사용자가 "애니메이션 넣어줘", "움직이게" 등 명시적으로 요청할 때
- Morph 전환이 필요한 연속 슬라이드 설계 시
- 복잡한 순서형 애니메이션 (타임라인, 프로세스 흐름) 필요 시
- 기존 템플릿 애니메이션과 새 콘텐츠 간 충돌 해결 시

미투입 시: Slide Planner가 slide_plan에 기본 애니메이션(Fade 전환만) 포함.

---

## Agent 8: OOXML Builder (조건부)

투입 조건 (replace_text.py 불가한 경우):
- 새로운 shape 추가 (placeholder가 아닌 도형/텍스트박스)
- 테이블 구조 변경 (행/열 추가 삭제)
- 차트 데이터 수정 (`c:val`, `c:cat` 노드)
- SmartArt/다이어그램 편집
- 슬라이드 복제 후 relationship ID 재매핑
- Path A에서 XML 파싱 에러 발생 시 수동 수정

미투입 시: replace_text.py + inject_animation.py 스크립트가 모든 수정 처리.

---

## Path A: 템플릿 기반 빌드 스크립트

### Step 1: 텍스트 교체

```bash
# replacements.json 형식:
# {
#   "slide1.xml": {
#     "placeholders": {
#       "0": {"text": "새 제목"},
#       "1": {"text": ["불릿 1", "불릿 2"]}
#     },
#     "textboxes": {
#       "TextBox 1": {"text": "텍스트박스 교체"}
#     }
#   }
# }

python3 {skill_root}/scripts/replace_text.py \
  --dir /tmp/slide_unpacked \
  --replacements /tmp/replacements.json
```

### Step 2: 애니메이션 주입

```bash
# animations.json 형식:
# {
#   "slide1.xml": {
#     "entrance": [
#       {"target_shape": "제목", "effect": "fade", "delay_ms": 0, "duration_ms": 500}
#     ],
#     "transition": {"type": "fade", "speed": "med"}
#   }
# }

python3 {skill_root}/scripts/inject_animation.py \
  --dir /tmp/slide_unpacked \
  --animations /tmp/animations.json
```

### Step 3: 패키징

```bash
python3 {skill_root}/scripts/pack.py \
  /tmp/slide_unpacked \
  /tmp/output.pptx
```

---

## Path B: python-pptx 디자인 빌드

```bash
# slide_plan.json을 /tmp에 저장 후 실행
python3 {skill_root}/scripts/build_slide.py \
  --plan /tmp/slide_plan.json \
  --output /tmp/output.pptx
```

### build_slide.py 20개 레이아웃 목록

- `cover` — 표지 (그라데이션 배경 + 글로우 서클)
- `key_statement` — 핵심 메시지 (큰 텍스트 중앙)
- `three_cards` — 3열 카드 (특징/서비스 소개)
- `two_column` — 2열 레이아웃 (비교/설명)
- `three_layers` — 3행 레이어 (프로세스/단계)
- `pipeline` — 파이프라인 (화살표 흐름)
- `split_detail` — 좌우 분할 (이미지+텍스트)
- `execution` — 실행 전략 (타임라인)
- `revenue` — 수익 모델 (KPI 카드)
- `partners` — 파트너/팀 (로고/프로필 그리드)
- `closing` — 마무리 (CTA + 연락처)
- `single_kpi` — 단일 KPI 강조
- `two_kpis` — 2개 KPI
- `three_kpis` — 3개 KPI
- `section_break` — 섹션 구분 페이지
- `comparison` — 비교표
- `quote` — 인용문
- `icon_row` — 아이콘 행 (기능 나열)
- `data_table` — 데이터 테이블
- `image_placeholder` — 이미지 자리 표시
