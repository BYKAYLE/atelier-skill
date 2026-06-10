# Phase 4: Quality Validator Agent

## Agent 5: Quality Validator (Haiku)

```
subagent_type: "general-purpose"
model: "haiku"
description: "3D 품질 검증"
```

**프롬프트:**
```
너는 프레젠테이션 품질 검증 전문가야.

slide_plan: {slide_plan}
validate.py 결과: {validation_result}
thumbnail.py 결과: {thumbnail_result}

아래 3가지 차원으로 평가해줘:

1. Vision (디자인) — 10점 만점
   - 레이아웃 일관성 / 색상 조화 / 여백과 정렬
   - thumbnail 결과 기반 시각 구성 평가

2. Content (정확성) — 10점 만점
   - 텍스트 정확성 / 핵심 메시지 전달력
   - 데이터 오류 여부 / 오탈자·문법

3. Logic (논리) — 10점 만점
   - 슬라이드 간 흐름 / 도입-전개-결론 구조
   - 각 슬라이드의 논리적 완결성

총점: {V + C + L} / 30
- 25점 이상: PASS
- 20-24점: WARNING (문제점 리포트)
- 19점 이하: FAIL (수정 필요 항목 구체적으로)
```

---

## 판정 처리

- **PASS** → Phase 5로 진행
- **WARNING** → 사용자에게 문제점 리포트 후 AskUserQuestion으로 판단 요청
- **FAIL** → 문제 슬라이드를 Content Generator로 재생성 후 재빌드

---

## Step 4: 시각 검증 (선택적 — Pencil MCP)

Pencil이 사용 가능하면:
1. `snapshot_layout` → 레이아웃 구조 확인
2. `get_screenshot` → 시각적 확인
