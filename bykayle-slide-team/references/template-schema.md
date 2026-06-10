# Template Schema — ByKayle Slide Team

> 템플릿 분석 결과의 출력 스키마 정의

---

## 1. 전체 스키마

Template Analyzer (Phase 1-A)의 출력은 아래 JSON 스키마를 따른다.

```json
{
  "template_info": {
    "file_name": "template.pptx",
    "file_size_kb": 2048,
    "slide_count": 15,
    "unique_layout_count": 8,
    "has_animations": true,
    "has_charts": false,
    "has_smartart": false,
    "created_date": "2024-01-15",
    "modified_date": "2024-03-20"
  },

  "theme": {
    "colors": {
      "dk1": "000000",
      "lt1": "FFFFFF",
      "dk2": "44546A",
      "lt2": "E7E6E6",
      "accent1": "4472C4",
      "accent2": "ED7D31",
      "accent3": "A5A5A5",
      "accent4": "FFC000",
      "accent5": "5B9BD5",
      "accent6": "70AD47",
      "hlink": "0563C1",
      "folHlink": "954F72"
    },
    "fonts": {
      "major": {"latin": "Calibri Light", "ea": "맑은 고딕"},
      "minor": {"latin": "Calibri", "ea": "맑은 고딕"}
    },
    "background": {
      "type": "solid|gradient|image",
      "value": "FFFFFF"
    }
  },

  "slide_masters": [
    {
      "id": "master_1",
      "name": "기본 마스터",
      "background": {"type": "solid", "value": "FFFFFF"},
      "default_font": "맑은 고딕",
      "layout_count": 8
    }
  ],

  "layouts": [
    {
      "id": "layout_1",
      "name": "Title Slide",
      "type": "title",
      "master_id": "master_1",
      "placeholders": [
        {
          "idx": 0,
          "type": "ctrTitle",
          "label": "제목",
          "position": {
            "left_emu": 685800,
            "top_emu": 2286000,
            "width_emu": 7772400,
            "height_emu": 1325563
          },
          "font": {"name": "맑은 고딕", "size_pt": 44, "bold": true},
          "alignment": "center"
        },
        {
          "idx": 1,
          "type": "subTitle",
          "label": "부제목",
          "position": {
            "left_emu": 1371600,
            "top_emu": 3886200,
            "width_emu": 6400800,
            "height_emu": 1752600
          },
          "font": {"name": "맑은 고딕", "size_pt": 20, "bold": false},
          "alignment": "center"
        }
      ],
      "special_elements": []
    },
    {
      "id": "layout_2",
      "name": "Title and Content",
      "type": "content",
      "master_id": "master_1",
      "placeholders": [
        {
          "idx": 0,
          "type": "title",
          "label": "제목",
          "position": {
            "left_emu": 457200,
            "top_emu": 274638,
            "width_emu": 8229600,
            "height_emu": 1143000
          },
          "font": {"name": "맑은 고딕", "size_pt": 28, "bold": true},
          "alignment": "left"
        },
        {
          "idx": 1,
          "type": "body",
          "label": "본문",
          "position": {
            "left_emu": 457200,
            "top_emu": 1600200,
            "width_emu": 8229600,
            "height_emu": 4525963
          },
          "font": {"name": "맑은 고딕", "size_pt": 18, "bold": false},
          "alignment": "left"
        }
      ],
      "special_elements": []
    }
  ],

  "slides": [
    {
      "number": 1,
      "layout_id": "layout_1",
      "has_animation": false,
      "has_notes": false,
      "shapes": [
        {
          "id": "sp1",
          "type": "placeholder",
          "ph_type": "ctrTitle",
          "text": "기존 제목 텍스트"
        }
      ],
      "special_elements": []
    }
  ],

  "special_elements_summary": {
    "grouped_shapes": [],
    "gradients": [],
    "shadows": [],
    "effects_3d": [],
    "smartart": [],
    "charts": [],
    "tables": [],
    "media": []
  },

  "animations_summary": {
    "animated_slides": [],
    "animation_types_used": [],
    "transitions_used": []
  }
}
```

---

## 2. 단위 환산표

OOXML은 **EMU (English Metric Units)** 를 사용한다.

| 단위 | EMU 변환 |
|------|----------|
| 1 inch | 914,400 EMU |
| 1 cm | 360,000 EMU |
| 1 pt | 12,700 EMU |
| 1 px (96dpi) | 9,525 EMU |

### 표준 슬라이드 크기

| 크기 | 가로 EMU | 세로 EMU | 가로 inch |
|------|----------|----------|-----------|
| 표준 (4:3) | 9,144,000 | 6,858,000 | 10" x 7.5" |
| 와이드 (16:9) | 12,192,000 | 6,858,000 | 13.33" x 7.5" |
| 와이드 (16:10) | 12,192,000 | 7,620,000 | 13.33" x 8.33" |

---

## 3. Placeholder 타입 매핑

| OOXML type 속성 | 한국어 | 용도 |
|-----------------|--------|------|
| `ctrTitle` | 중앙 제목 | 제목 슬라이드 메인 텍스트 |
| `subTitle` | 부제목 | 제목 슬라이드 보조 텍스트 |
| `title` | 제목 | 일반 슬라이드 제목 |
| `body` | 본문 | 텍스트 콘텐츠 영역 |
| `pic` | 이미지 | 이미지 placeholder |
| `chart` | 차트 | 차트 삽입 영역 |
| `tbl` | 표 | 테이블 삽입 영역 |
| `dt` | 날짜 | 날짜 자동 표시 |
| `ftr` | 바닥글 | 하단 텍스트 |
| `sldNum` | 번호 | 슬라이드 번호 |
| `clipArt` | 클립아트 | 이미지/아이콘 영역 |
| `media` | 미디어 | 동영상/오디오 |
| `dgm` | 다이어그램 | SmartArt |

---

## 4. XML 경로 구조

.pptx 파일을 ZIP으로 풀면 아래 구조:

```
template_unpacked/
├── [Content_Types].xml
├── _rels/
│   └── .rels
├── docProps/
│   ├── app.xml
│   ├── core.xml
│   └── thumbnail.jpeg
└── ppt/
    ├── presentation.xml          # 프레젠테이션 메타데이터
    ├── presProps.xml              # 프레젠테이션 속성
    ├── tableStyles.xml
    ├── viewProps.xml
    ├── _rels/
    │   └── presentation.xml.rels  # 슬라이드/마스터 참조
    ├── theme/
    │   └── theme1.xml             # 색상/폰트/효과 테마
    ├── slideMasters/
    │   ├── slideMaster1.xml       # 마스터 슬라이드
    │   └── _rels/
    │       └── slideMaster1.xml.rels
    ├── slideLayouts/
    │   ├── slideLayout1.xml       # 레이아웃 정의
    │   ├── slideLayout2.xml
    │   └── _rels/
    ├── slides/
    │   ├── slide1.xml             # 개별 슬라이드
    │   ├── slide2.xml
    │   └── _rels/
    │       ├── slide1.xml.rels    # 슬라이드별 참조 (이미지 등)
    │       └── slide2.xml.rels
    ├── notesSlides/               # 발표자 노트
    │   └── notesSlide1.xml
    └── media/                     # 이미지/동영상
        ├── image1.png
        └── image2.jpg
```

---

## 5. 핵심 XML 네임스페이스

```xml
xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
```

| prefix | 용도 |
|--------|------|
| `a:` | DrawingML — 도형, 텍스트, 색상, 효과 |
| `p:` | PresentationML — 슬라이드, 애니메이션, 전환 |
| `r:` | Relationships — 파일 간 참조 |
| `c:` | ChartML — 차트 |
| `dgm:` | DiagramML — SmartArt |

---

## 6. 텍스트 교체 대상 XML 구조

### 단순 텍스트 placeholder

```xml
<p:sp>
  <p:nvSpPr>
    <p:nvPr>
      <p:ph type="title" idx="0"/>    <!-- ← placeholder 식별 -->
    </p:nvPr>
  </p:nvSpPr>
  <p:txBody>
    <a:p>
      <a:r>
        <a:rPr lang="ko-KR" dirty="0"/>
        <a:t>교체할 텍스트</a:t>        <!-- ← 여기만 교체 -->
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
```

### 교체 규칙

1. `<a:t>` 태그의 텍스트만 교체
2. `<a:rPr>` (서식)은 **절대 건드리지 않음**
3. 여러 `<a:r>` 요소로 분할된 텍스트는 **첫 번째 `<a:r>`에 통합**, 나머지 `<a:r>` 삭제
4. 빈 `<a:r>` 요소를 만들지 않음
5. `lang` 속성은 콘텐츠 언어에 맞게 설정 (ko-KR, en-US 등)
