---
name: bykayle-slide-team
description: "Use when creating PPT presentations, slides, or pitch decks. Triggers: PPT 만들어줘, 프레젠테이션 생성, 슬라이드 만들어줘, 내 템플릿으로 PPT, 발표자료 만들어줘, slide team, PPT 에이전트"
---

# ByKayle Slide Team v2.0

> 10명의 전문가 풀 + 결정론적 스크립트의 하이브리드 구조로 고품질 프레젠테이션을 자동 생성합니다.
> 매번 전원이 투입되지 않지만, 필요한 상황에서 적재적소에 전문가가 호출됩니다.
> 에이전트가 분석·설계·생성·검증·특수 상황을, 스크립트가 결정론적 빌드를 담당합니다.
> 템플릿이 있으면 디자인 100% 보존(Path A), 없으면 python-pptx로 프로급 디자인 생성(Path B).

---

## WHEN TRIGGERED - EXECUTE IMMEDIATELY

**이 문서는 참고 문서가 아니라 실행 지시서다.**
- 이 스킬이 트리거되면 아래 워크플로우를 즉시 실행한다.
- 모든 질문은 AskUserQuestion 도구 호출로만 진행한다.
- 텍스트로 질문을 출력하면 안 된다.

---

## 핵심 원리

1. **두 갈래 경로**: 템플릿 유(Path A: XML 텍스트 교체) / 무(Path B: python-pptx 디자인 빌드)
2. **결정론적 스크립트**: 텍스트 교체·애니메이션·빌드를 프롬프트가 아닌 Python 스크립트가 수행
3. **3D 품질 평가**: Vision(디자인) + Content(정확성) + Logic(논리) 3차원 검증
4. **Pencil MCP 연동**: 디자인 영감 + 프로토타입 + 시각 검증 (선택적, 없어도 동작)

---

## 에이전트 구성 (10명 전문가 풀)

> 항상 투입되는 핵심 6명 + 필요 시 투입되는 전문가 4명.

### 항상 투입 (핵심 6명)

| # | 역할 | 모델 | Phase | 용도 |
|---|------|------|-------|------|
| 0 | **Orchestrator** | 메인 Claude | 0/3/5 | 전체 흐름 제어, 스크립트 실행 |
| 1 | **Template Analyzer** | Haiku | 1 | Path A: 템플릿 unpack + parse |
| 2 | **Content Analyzer** | Haiku | 1 | 콘텐츠 구조 분석 (병렬) |
| 3 | **Slide Planner** | Sonnet | 2 | 슬라이드별 설계도 JSON 생성 |
| 4 | **Content Generator** | Sonnet | 3 | 슬라이드 텍스트 생성 |
| 5 | **Quality Validator** | Haiku | 4 | 3D 품질 평가 + 썸네일 검증 |

### 필요 시 투입 (전문가 풀 4명)

| # | 역할 | 모델 | Phase | 투입 조건 |
|---|------|------|-------|----------|
| 6 | **Layout Selector** | Haiku | 2/3 | 복잡 템플릿(10+ 레이아웃), 특정 레이아웃 요구 시 |
| 7 | **Animation Intelligence** | Sonnet | 3 | 애니메이션 명시 요청, Morph 전환, 복잡 순서형 애니메이션 |
| 8 | **OOXML Builder** | Haiku | 3 | replace_text.py 불가한 복잡 XML 수정 (shape 추가, 테이블, 차트) |
| 9 | **Design Advisor** | Sonnet | 1/2 | Path B 디자인 방향 미지정, 디자인 피드백, 참고 이미지 분석 |

상세 역할 정의 + 프롬프트 템플릿: `references/agent-roles.md` 참조

---

## 워크플로우

### Phase 0: 입력 수집 + 경로 분기

**목표:** 사용자로부터 입력을 수집하고 Path A / Path B를 결정한다.

**EXECUTE:** AskUserQuestion 도구를 즉시 호출한다:

```json
{
  "questions": [
    {
      "question": "어떤 방식으로 PPT를 만들까요?",
      "header": "PPT 모드",
      "options": [
        {
          "label": "내 템플릿 + 콘텐츠 (추천)",
          "description": "기존 .pptx 템플릿 파일과 콘텐츠를 함께 주세요. 템플릿 디자인을 100% 보존하면서 내용을 채워드려요."
        },
        {
          "label": "템플릿만 등록",
          "description": "먼저 템플릿만 분석해두고, 나중에 콘텐츠를 넣을게요."
        },
        {
          "label": "콘텐츠만 제공",
          "description": "템플릿 없이 콘텐츠만 줄게요. 트렌디한 디자인으로 새로 만들어주세요."
        }
      ],
      "multiSelect": false
    }
  ]
}
```

**모드 선택 후, 발표 목적을 확인한다:**

```json
{
  "questions": [
    {
      "question": "어떤 목적의 발표자료인가요?",
      "header": "발표 목적",
      "options": [
        {"label": "투자자 피칭 (IR)", "description": "VC/엔젤 투자자 대상. 핵심만 임팩트 있게. 보통 10-15분."},
        {"label": "사업 제안/영업", "description": "고객/파트너 대상. 솔루션 중심. 보통 20-30분."},
        {"label": "사내 보고/회의", "description": "팀/임원 대상. 데이터 중심. 보통 15-30분."},
        {"label": "직접 알려줄게요", "description": "목적과 발표 시간을 직접 입력할게요."}
      ],
      "multiSelect": false
    }
  ]
}
```

**발표 시간별 슬라이드 수 가이드:**
- **5분 이하**: 5-7장 (엘리베이터 피치)
- **10분**: 8-10장 (IR 피칭, 데모데이)
- **15분**: 10-13장 (상세 IR, 사업 제안)
- **20-30분**: 14-18장 (사내 보고, 워크숍)
- **30분 이상**: 20장+ (세미나, 강의)

**경로 분기:**
- **템플릿 있음** → `Path A` (Phase 1-A → Phase 2 → Phase 3-A)
- **템플릿 없음** → `Path B` (Phase 1-B → Phase 2 → Phase 3-B)

---

### Phase 1: 분석

**반드시 2개 에이전트를 하나의 메시지에서 동시에 Agent 도구로 스폰한다.**

#### Path A: Agent 1 (Template Analyzer) + Agent 2 (Content Analyzer) — 병렬

See `references/phase1-agents.md` for full agent prompts and Design Advisor (Agent 9) conditions.

#### Path B: Agent 2 (Content Analyzer) + 디자인 영감 수집 — 병렬

Content Analyzer는 Path A와 동일하게 스폰한다. Agent 9 조건 및 투입 기준은 `references/phase1-agents.md` 참조.

Pencil MCP가 사용 가능하면:
1. `get_guidelines("slides")` → 레이아웃 참조 취득
2. `get_style_guide_tags` → 사용 가능한 스타일 태그 확인
3. `get_style_guide(tags)` → 스타일 가이드 취득

없으면 `references/design-principles.md`의 디자인 원칙으로 진행.

**디자인 방향 확인 (AskUserQuestion):** 다크 모던 / 라이트 미니멀 / 컬러풀 그래디언트 / 직접 지정

---

### Phase 2: 슬라이드 설계 (Agent: Slide Planner)

**목표:** 분석 결과를 바탕으로 슬라이드별 설계도 JSON(slide_plan)을 만든다.

Agent 6 (Layout Selector) 투입 조건: 레이아웃 10개 이상, 특정 레이아웃 요구, 50+ 슬라이드 복잡 템플릿.

See `references/phase2-planner.md` for full Slide Planner prompt, slide_plan JSON schema, and layout ID list.

**사용자 확인 (AskUserQuestion):** 이대로 생성 / 수정할 부분 있어요 / 전체 다시 설계

Pencil MCP Path B 프로토타입: `open_document` → `batch_design` → `get_screenshot`

---

### Phase 3: 콘텐츠 생성 + 빌드

Agent 7 (Animation Intelligence) 투입 조건: 명시적 애니메이션 요청, Morph 전환, 순서형 애니메이션, 충돌 해결.
Agent 8 (OOXML Builder) 투입 조건: shape 추가, 테이블/차트 변경, SmartArt, 슬라이드 복제 후 rID 재매핑.

See `references/phase3-build.md` for Content Generator prompt, Path A build scripts (replace_text → inject_animation → pack), and Path B build_slide.py usage.

---

### Phase 4: 검증

**목표:** 생성된 PPT를 구조적 + 3D 품질 검증한다.

#### Step 1: 구조 검증 (validate.py)

```bash
python3 {skill_root}/scripts/validate.py /tmp/output.pptx
```

5개 항목: ZIP 구조 / XML 파싱 / Relationship 참조 / Content Types / 안티패턴 탐지.
FAIL이면 오류 수정 후 Phase 3 재실행.

#### Step 2: 썸네일 생성 (thumbnail.py)

```bash
python3 {skill_root}/scripts/thumbnail.py /tmp/output.pptx --cols 4 --width 36 --height 12
```

#### Step 3: 3D 품질 평가 (Agent 5: Quality Validator)

See `references/phase4-validator.md` for full Quality Validator prompt and PASS/WARNING/FAIL handling.

---

### Phase 5: 전달 + 후처리

**목표:** 최종 .pptx를 전달하고 후처리 옵션을 제공한다.

1. 출력 파일을 Downloads 폴더로 복사
2. 파일 크기 확인 (15MB 이하 권장)
3. 최종 경로와 슬라이드 수 안내

AskUserQuestion으로 후처리 옵션 제시: 완성 / 특정 슬라이드 수정 / 발표자 노트 보강 / Claude in PPT 후처리

---

## 엣지 케이스 처리

See `references/edge-cases.md` for handling: 복잡 템플릿(50+), 콘텐츠 부족/과다, XML 파싱 실패, 애니메이션 충돌, 파일 크기 초과.

---

## AI 행동 규칙

### 반드시 지킬 것

- Phase 0에서 입력 수집 후에만 에이전트를 스폰한다
- 경로 분기를 명확히: 템플릿 있으면 Path A, 없으면 Path B
- **Path A는 스크립트로 빌드**: replace_text.py → inject_animation.py → pack.py
- **Path B는 스크립트로 빌드**: build_slide.py (slide_plan JSON 입력)
- slide_plan JSON을 반드시 중간 결과로 파일에 저장
- 색상값에 "#" 넣지 않는다 (OOXML은 "FF0000" 형식)
- 모든 질문은 AskUserQuestion 도구로만 한다
- Phase 4 검증을 생략하지 않는다
- 슬라이드당 핵심 메시지는 1개만
- 같은 레이아웃 2번 연속 사용 금지

### 절대 하지 말 것

- 사용자 확인 없이 원본 템플릿 파일 수정
- Path A에서 python-pptx로 처음부터 새로 만들기 (템플릿이 있으면 XML 교체)
- 에이전트 프롬프트로 OOXML XML을 직접 생성하게 시키기 (스크립트를 사용)
- 슬라이드당 4개 이상 애니메이션
- 장식용 애니메이션 (의미 없는 회전, 바운스 등)
- Phase 4 검증 스킵
- slide_plan 없이 빌드 시작

---

## Pencil MCP 연동 (선택적)

| Phase | 도구 | 용도 |
|-------|------|------|
| 1 (Path B) | `get_guidelines("slides")` | 레이아웃 참조 취득 |
| 1 (Path B) | `get_style_guide_tags` + `get_style_guide` | 스타일 영감 (컬러/무드) |
| 2 (Path B) | `batch_design` | 슬라이드 프로토타입 생성 |
| 2 (Path B) | `get_screenshot` | 프로토타입 시각 확인 |
| 4 | `snapshot_layout` | 생성 결과 레이아웃 검증 |

**경계**: Pencil은 "디자인 참조 + 시각 검증" 전용. .pen → .pptx 변환 불가. Pencil 없어도 스킬은 완전히 동작한다.

---

## References

- **`references/agent-roles.md`** — 10개 에이전트 역할 정의 + 프롬프트 템플릿
- **`references/phase1-agents.md`** — Phase 1 에이전트 프롬프트 (Template Analyzer, Content Analyzer, Design Advisor)
- **`references/phase2-planner.md`** — Slide Planner 프롬프트 + slide_plan JSON 스키마 + Layout Selector 조건
- **`references/phase3-build.md`** — Content Generator 프롬프트 + Path A/B 빌드 스크립트 + 20개 레이아웃 목록
- **`references/phase4-validator.md`** — Quality Validator 프롬프트 + 판정 처리 + Pencil 시각 검증
- **`references/edge-cases.md`** — 엣지 케이스 6종 처리 방법
- **`references/design-principles.md`** — 슬라이드 디자인 원칙과 안티패턴
- **`references/template-schema.md`** — 템플릿 분석 출력 스키마 + 텍스트 교체 규칙
- **`references/animation-rules.md`** — 애니메이션 규칙과 OOXML presetID 매핑

## Scripts

- **`scripts/unpack.py`** — .pptx → ZIP 해제 (슬라이드 XML 추출)
- **`scripts/pack.py`** — 수정된 XML → .pptx 패키징
- **`scripts/parse_template.py`** — 슬라이드 레이아웃/placeholder 분석
- **`scripts/replace_text.py`** — Path A 텍스트 교체 엔진 (placeholder 서식 보존)
- **`scripts/inject_animation.py`** — 애니메이션 XML 자동 주입 (기존 보존)
- **`scripts/build_slide.py`** — Path B python-pptx 디자인 빌더 (20개 레이아웃)
- **`scripts/thumbnail.py`** — 슬라이드 ASCII 썸네일 그리드 생성 (시각 검증)
- **`scripts/validate.py`** — 최종 .pptx 무결성 검증 (5항목)
