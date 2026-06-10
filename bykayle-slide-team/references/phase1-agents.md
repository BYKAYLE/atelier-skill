# Phase 1 Agent Prompts

## Agent 1: Template Analyzer (Path A)

```
subagent_type: "general-purpose"
model: "haiku"
description: "템플릿 구조 분석"
```

**프롬프트:**
```
너는 PowerPoint 템플릿 분석 전문가야.

아래 스크립트를 순서대로 실행해줘:

1. unpack.py로 .pptx를 ZIP 해제:
   python3 {skill_root}/scripts/unpack.py "{template_path}" /tmp/slide_unpacked

2. parse_template.py로 레이아웃 스키마 추출:
   python3 {skill_root}/scripts/parse_template.py /tmp/slide_unpacked

추출할 정보:
- 슬라이드 마스터/레이아웃 목록
- 각 슬라이드의 placeholder 위치와 타입 (제목, 본문, 이미지, 차트)
- 색상 팔레트 (theme/theme1.xml에서)
- 폰트 설정
- 특수 요소 (그라데이션, 그림자, 레이어 구조, 도형 그룹)
- 애니메이션이 있는 슬라이드 목록

결과를 JSON으로 출력해줘.
```

---

## Agent 2: Content Analyzer (Path A & B)

```
subagent_type: "general-purpose"
model: "haiku"
description: "콘텐츠 구조 분석"
```

**프롬프트:**
```
너는 프레젠테이션 콘텐츠 분석 전문가야.

사용자가 제공한 콘텐츠를 분석해줘:

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

---

## Agent 9: Design Advisor (Path B, 조건부)

투입 조건:
- 사용자가 디자인 방향을 명시하지 않았을 때
- 참고 이미지/URL을 제공했을 때 (스타일 분석 필요)
- "더 화려하게", "기업용으로", "미니멀하게" 등 디자인 피드백이 있을 때
- Pencil MCP 결과를 해석하여 slide_plan에 반영할 때

미투입 시: Orchestrator가 사용자 선택(다크 모던/라이트 미니멀 등)에 따라 프리셋 팔레트 적용.
