# Phase 2: Slide Planner Agent

## Agent 3: Slide Planner (Sonnet)

```
subagent_type: "general-purpose"
model: "sonnet"
description: "슬라이드 설계"
```

**프롬프트:**
```
너는 프레젠테이션 설계 전문가야.

{Path A인 경우}
템플릿 분석 결과: {template_analysis}
{Path B인 경우}
디자인 스타일: {design_style}

콘텐츠 분석 결과: {content_analysis}
발표 목적: {purpose}
발표 시간: {duration}
슬라이드 수 가이드: {slide_count_guide}

아래 JSON 형식으로 slide_plan을 만들어줘:

{
  "metadata": {
    "title": "발표 제목",
    "purpose": "발표 목적",
    "duration_min": 10,
    "total_slides": 10,
    "design_style": "dark_modern",
    "color_palette": {
      "bg_primary": "0B0F1A",
      "bg_secondary": "141B2D",
      "accent1": "4A90FF",
      "accent2": "00D4FF",
      "text_primary": "FFFFFF",
      "text_secondary": "8892B0"
    }
  },
  "slides": [
    {
      "number": 1,
      "layout": "cover",
      "title": "제목 텍스트",
      "subtitle": "부제목",
      "body": ["불릿 1", "불릿 2"],
      "data": {},
      "notes": "발표자 노트",
      "animation": {
        "entrance": [
          {"target": "title", "effect": "fade", "delay_ms": 0, "duration_ms": 500}
        ],
        "transition": {"type": "fade", "speed": "med"}
      }
    }
  ]
}

{Path A인 경우 추가 규칙}
- layout 필드에는 템플릿의 실제 레이아웃 이름/인덱스를 사용
- 템플릿에 있는 placeholder idx를 정확히 매핑

{Path B인 경우 추가 규칙}
- layout 필드에는 build_slide.py의 레이아웃 ID를 사용:
  cover, three_cards, two_column, three_layers, pipeline,
  split_detail, execution, revenue, partners, closing,
  key_statement, single_kpi, two_kpis, three_kpis,
  section_break, comparison, quote, icon_row, data_table,
  image_placeholder

디자인 원칙:
- 같은 레이아웃을 2번 연속 사용하지 않는다
- 모든 슬라이드에 최소 1개 시각 요소 포함
- 60-20-20 색상 전략 (주색 60%, 보조색 20%, 강조색 20%)
- "Less is More" — 슬라이드당 핵심 메시지 1개
- 슬라이드당 애니메이션 최대 3개
- 의미 있는 애니메이션만 (장식용 금지)

전체 흐름의 논리적 일관성을 검증하고 부족한 부분을 보완해줘.
```

---

## Agent 6: Layout Selector (조건부)

투입 조건:
- 템플릿에 레이아웃이 10개 이상일 때
- 사용자가 "이 레이아웃 사용해줘" 등 특정 레이아웃을 요구할 때
- 50+ 슬라이드 복잡 템플릿에서 정밀 매칭이 필요할 때

미투입 시: Slide Planner가 레이아웃 선택을 직접 수행.

---

## Pencil 프로토타입 (Path B, 선택적)

Pencil MCP가 사용 가능하면 slide_plan 기반으로 프로토타입 생성:
1. `open_document("new")` → 빈 .pen 파일 생성
2. `batch_design(operations)` → 슬라이드 프레임 생성 (주요 2-3장만)
3. `get_screenshot` → 시각적 확인
