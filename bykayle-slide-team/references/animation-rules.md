# Animation Rules — ByKayle Slide Team

> 애니메이션 규칙, OOXML 타이밍 XML 매핑, 전환 효과 가이드

---

## 1. 애니메이션 원칙

### 1.1 "Less is More"

- 슬라이드당 **최대 3개** 애니메이션
- 의미 있는 애니메이션만 (정보 전달을 돕는 것)
- 장식용 애니메이션 **금지** (불필요한 회전, 바운스, 스파이럴 등)

### 1.2 목적별 애니메이션

| 목적 | 적합한 효과 | 부적합한 효과 |
|------|-------------|---------------|
| 순서 강조 | Appear, Fade | Fly, Bounce |
| 데이터 공개 | Wipe (방향), Fade | Spin, Swivel |
| 비교 전환 | Morph | Random, Checkerboard |
| 핵심 강조 | Pulse, Color Change | Teeter, Float |
| 프로세스 흐름 | Fly In (좌→우) | Random Bars |

### 1.3 타이밍 규칙

| 요소 | 지속 시간 | 지연 |
|------|-----------|------|
| 제목 진입 | 500ms | 0ms |
| 불릿 포인트 | 300ms | 200ms (이전 뒤) |
| 이미지/차트 | 700ms | 300ms (이전 뒤) |
| 강조 효과 | 500ms | 해당 없음 |
| 전환 효과 | 700ms | 해당 없음 |

---

## 2. 슬라이드 타입별 애니메이션 가이드

### 2.1 제목 슬라이드

```
제목: Fade In (500ms, 자동)
부제목: Fade In (300ms, 제목 후 500ms)
로고: 없음 (항상 표시)
```

### 2.2 콘텐츠 슬라이드 (불릿)

```
제목: Appear (즉시)
불릿 1: Fade In (300ms, 클릭 시)
불릿 2: Fade In (300ms, 클릭 시)
불릿 3: Fade In (300ms, 클릭 시)
이미지: Fade In (700ms, 마지막 불릿 후)
```

### 2.3 데이터 슬라이드

```
제목: Appear (즉시)
차트: Wipe Bottom-to-Top (1000ms, 클릭 시)
데이터 레이블: Fade In (300ms, 차트 후)
```

### 2.4 비교 슬라이드

```
제목: Appear (즉시)
왼쪽 열: Fly In Left (500ms, 클릭 시)
오른쪽 열: Fly In Right (500ms, 왼쪽 후)
```

### 2.5 결론 슬라이드

```
핵심 메시지: Fade In (700ms, 자동)
CTA: Pulse (500ms, 핵심 메시지 후 1000ms)
```

---

## 3. 전환 효과 (Slide Transition)

### 3.1 권장 전환

| 전환 | 적합한 상황 | 지속 시간 |
|------|-------------|-----------|
| Fade | 일반적인 전환 (기본값) | 700ms |
| Push | 순서가 있는 정보 | 500ms |
| Morph | 유사 레이아웃 연속 | 1000ms |
| None | 빠른 발표, 데이터 중심 | 0ms |

### 3.2 금지 전환

- Checkerboard, Blinds, Random Bars — 프로페셔널하지 않음
- Vortex, Shred, Switch — 과도한 시각 효과
- Comb, Newsflash — 주의 산만

### 3.3 Morph 전환 사용 조건

Morph는 연속된 슬라이드가 **동일 오브젝트**를 공유할 때만 사용:
- 같은 도형이 위치/크기만 변경
- 같은 이미지가 확대/축소
- 같은 텍스트가 이동

**조건 미충족 시 Fade로 대체**

---

## 4. OOXML 애니메이션 XML 구조

### 4.1 기본 구조

```xml
<p:timing>
  <p:tnLst>
    <p:par>                              <!-- 최상위 시퀀스 -->
      <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
        <p:childTnLst>
          <p:seq concurrent="1" nextAc="seek">
            <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
              <p:childTnLst>

                <!-- 클릭 1: 제목 Fade In -->
                <p:par>
                  <p:cTn id="3" fill="hold">
                    <p:stCondLst>
                      <p:cond delay="0"/>
                    </p:stCondLst>
                    <p:childTnLst>
                      <p:par>
                        <p:cTn id="4" fill="hold">
                          <p:stCondLst>
                            <p:cond delay="0"/>
                          </p:stCondLst>
                          <p:childTnLst>
                            <p:par>
                              <p:cTn id="5" presetID="10" presetClass="entr"
                                     presetSubtype="0" fill="hold">
                                <p:stCondLst>
                                  <p:cond delay="0"/>
                                </p:stCondLst>
                                <p:childTnLst>
                                  <!-- 효과 정의 -->
                                </p:childTnLst>
                              </p:cTn>
                            </p:par>
                          </p:childTnLst>
                        </p:cTn>
                      </p:par>
                    </p:childTnLst>
                  </p:cTn>
                </p:par>

              </p:childTnLst>
            </p:cTn>
          </p:seq>
        </p:childTnLst>
      </p:cTn>
    </p:par>
  </p:tnLst>
</p:timing>
```

### 4.2 presetID 매핑 (Entrance 효과)

| presetID | 효과 이름 | presetSubtype | 설명 |
|----------|-----------|---------------|------|
| 1 | Appear | 0 | 즉시 표시 |
| 2 | Fly In | 4=Bottom, 8=Left, 2=Right, 1=Top | 방향에서 날아옴 |
| 10 | Fade | 0 | 서서히 나타남 |
| 12 | Grow & Turn | 0 | 커지면서 회전 |
| 16 | Random Bars | 0=Horizontal, 1=Vertical | 랜덤 바 |
| 22 | Wipe | 4=Bottom, 8=Left, 2=Right, 1=Top | 방향으로 닦기 |
| 31 | Wheel | 1,2,3,4,8 (스포크 수) | 바퀴 모양 |
| 53 | Zoom | 16=InCenter, 32=InBottom | 확대 |

### 4.3 presetClass 값

| 값 | 의미 |
|----|------|
| `entr` | Entrance (진입) |
| `emph` | Emphasis (강조) |
| `exit` | Exit (퇴장) |
| `path` | Motion Path (경로) |

### 4.4 트리거 조건

```xml
<!-- 클릭 시 (기본) -->
<p:stCondLst>
  <p:cond delay="0"/>
</p:stCondLst>

<!-- 이전 효과와 함께 -->
<p:stCondLst>
  <p:cond delay="0" evt="begin" tn="이전cTn의id"/>
</p:stCondLst>

<!-- 이전 효과 후 -->
<p:stCondLst>
  <p:cond delay="0" evt="end" tn="이전cTn의id"/>
</p:stCondLst>

<!-- 지연 후 자동 시작 -->
<p:stCondLst>
  <p:cond delay="500"/>  <!-- 밀리초 -->
</p:stCondLst>
```

### 4.5 효과 대상 지정

```xml
<!-- 도형 전체 -->
<p:tgtEl>
  <p:spTgt spid="3"/>    <!-- shape ID -->
</p:tgtEl>

<!-- 텍스트 단락별 -->
<p:tgtEl>
  <p:spTgt spid="3">
    <p:txEl>
      <p:pRg st="0" end="0"/>  <!-- 0번째 단락 -->
    </p:txEl>
  </p:spTgt>
</p:tgtEl>
```

---

## 5. 전환 효과 XML

### 5.1 슬라이드 전환 위치

```xml
<p:sld>
  <!-- 전환 효과는 <p:cSld> 전에 위치 -->
  <p:transition spd="med" advClick="1">
    <p:fade/>                          <!-- Fade 전환 -->
  </p:transition>
  <p:cSld>
    ...
  </p:cSld>
</p:sld>
```

### 5.2 전환 타입 XML

```xml
<!-- Fade -->
<p:transition spd="med"><p:fade/></p:transition>

<!-- Push (왼쪽으로) -->
<p:transition spd="med"><p:push dir="l"/></p:transition>

<!-- Wipe (아래서 위로) -->
<p:transition spd="med"><p:wipe dir="u"/></p:transition>

<!-- Morph (Office 2019+) -->
<p:transition spd="slow" xmlns:p16="http://schemas.microsoft.com/office/powerpoint/2015/main">
  <p16:morph option="byObject"/>
</p:transition>
```

### 5.3 속도 값

| spd 값 | 대략적 시간 |
|--------|-------------|
| `slow` | 1000ms |
| `med` | 700ms |
| `fast` | 300ms |

---

## 6. 기존 애니메이션 보존 규칙

### 6.1 원본 슬라이드에 `<p:timing>`이 이미 있는 경우

1. **기존 `<p:timing>` 전체를 보존**한다
2. 새 애니메이션은 **추가하지 않는다** (충돌 방지)
3. 사용자가 명시적으로 요청한 경우에만 수정

### 6.2 원본에 애니메이션이 없는 경우

1. 설계도에 따라 새 `<p:timing>` 블록 생성
2. id 번호는 1부터 순차적으로 부여
3. shape id (`spid`)는 해당 슬라이드의 실제 shape id와 일치해야 함

### 6.3 충돌 감지

아래 경우 사용자에게 AskUserQuestion으로 확인:
- 원본 애니메이션이 있는 슬라이드에 새 콘텐츠 추가
- 원본 애니메이션의 대상 shape가 삭제/교체된 경우
- Morph 전환 사용 시 앞뒤 슬라이드 오브젝트 불일치

---

## 7. CJK 애니메이션 특별 규칙

| 규칙 | 이유 |
|------|------|
| 글자별 애니메이션 금지 | CJK 글자는 개별 렌더링 비용이 높고 가독성 저하 |
| 단어/문장 단위만 허용 | `<p:txEl><p:pRg>` 사용 |
| Typewriter 효과 금지 | CJK에서 부자연스러움 |
| 세로쓰기 애니메이션 주의 | 세로 텍스트는 Fly In Left/Right만 사용 |
