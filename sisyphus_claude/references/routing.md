# Sisyphus Claude Routing Reference

이 문서는 `sisyphus_claude`가 OpenCode Sisyphus에 더 가깝게 동작하도록 돕는 탐색/위임/재통합 기준을 정리한다.

## 1. Trigger -> 기본 행동

| 트리거 | 기본 행동 |
|---|---|
| 외부 라이브러리 언급 | 외부 레퍼런스 탐색 우선 |
| 2개 이상 모듈/레이어 관련 | 내부 코드베이스 탐색 우선 |
| 복잡하거나 모호한 요청 | 범위와 숨은 의도 먼저 정리 |
| 큰 계획 수립 직후 | 계획 재검토 |
| 큰 수정 완료 직후 | 고수준 sanity review 고려 |

## 1.2 Mandatory Delegation Bias

아래는 사실상 필수에 가깝다.

- 외부 라이브러리 이해가 부족하면 외부 레퍼런스 탐색을 먼저 한다.
- 2개 이상 모듈을 건드리면 내부 구조 탐색을 먼저 한다.
- 큰 계획은 누락/검증 가능성 점검 없이 바로 실행하지 않는다.
- 큰 수정 후 남은 리스크는 sanity review 후보로 본다.

## 1.5 Parallel Exploration Rules

OpenCode Sisyphus에 가깝게 가려면, 독립적인 탐색은 순차보다 병렬을 기본값으로 둔다.

### 병렬로 묶을 수 있는 것

- 여러 파일 읽기
- 내부 패턴 검색과 유사 구현 검색
- 로컬 사용 패턴 확인과 외부 공식 문서 확인
- 설정 파일 점검과 빌드/테스트 스크립트 점검
- 핵심 흐름 점검과 예외/빈 상태 점검

### 병렬 탐색 기본 규칙

1. 서로 의존하지 않는 읽기/검색은 동시에 진행한다.
2. 내부 탐색과 외부 레퍼런스 탐색이 둘 다 필요하면 같이 돌린다.
3. 탐색 결과가 충분히 모이면 즉시 우선순위를 정하고 실행으로 넘어간다.
4. 같은 정보를 반복해서 찾는 과탐색은 피한다.

### 정지 기준

- 현재 병목의 원인을 설명할 수 있을 때
- 다음 수정 방향이 명확할 때
- 새로운 정보가 거의 나오지 않을 때
- 검증 단계로 넘어가는 편이 더 가치 있을 때

## 2. Specialist Routing

### UI/UX
- 사용할 때: 화면 밀도, 정보 구조, 상태 표현, 접근성, 시각 polish
- 우선 방향: `ui-ux-pro-max`

### Security
- 사용할 때: 인증, 인가, 세션, 권한, 민감 입력, 외부 노출면
- 우선 방향: `security-router`

### Product-Scale Buildout
- 사용할 때: 기능 단위를 넘는 서비스 전반 고도화
- 우선 방향: `autonomous-dev`

### Internal Exploration
- 사용할 때: 크로스레이어 흐름, 유사 구현, 구조 탐색
- 기대 산출물: 파일 경로, 패턴, 기준 파일, 흐름 요약

### External Reference Research
- 사용할 때: 공식 문서, 모범 사례, 오픈소스 구현 예시
- 기대 산출물: 권장 패턴, 주의점, 참고 사례
- 강한 신호:
  - SDK major/minor behavior 차이
  - deprecated 옵션/파라미터 교체
  - 프레임워크 rename / internal boundary / default behavior 변경

### Escalation Review
- 사용할 때: 같은 방향의 실패 반복, 큰 수정 후 리스크 잔존, 설계 방향 불확실
- 기대 산출물: 계속 밀어도 되는지, 재계획이 필요한지, 리스크가 무엇인지
- 최근 실전형 해석:
  - 바로 수정보다 경계 재해석이 먼저면 oracle-like replanning으로 본다.
  - public flow, updater, settings save 같은 연결 경계 문제는 구조 재설명 후 bounded fix로 다시 내려와야 한다.

## 2.5 Category and Skill Selection

1. 작업 도메인을 먼저 분류한다.
2. 해당 도메인에 가장 맞는 skill 방향을 고른다.
3. 로컬 설치 스킬과 현재 목표의 교집합이 있으면 우선 사용한다.
4. 위임이 결과 품질을 실제로 올릴 때만 유지한다.

### 기본 선택표

| 작업 유형 | 우선 선택 |
|---|---|
| UI/UX, 레이아웃, 상태 표현 | `ui-ux-pro-max` |
| 보안, 인증, 권한 | `security-router` |
| 제품/서비스 단위 고도화 | `autonomous-dev` |
| 스킬 개선 | `skill-evolve` |
| 과학/연구 특화 | `k-dense-ai` |
| 현장/인프라 지원 | `it-field-support` |

## 3. Re-integration Rule

위임 결과를 받으면 그대로 최종 답으로 쓰지 않는다.

반드시 아래를 다시 판단한다.

1. 이 결과가 현재 release loop의 어느 단계에 들어가는가
2. 우선순위를 바꿀 만큼 근거가 강한가
3. 추가 검증이 필요한가
4. 최종 결과물 품질을 실제로 높이는가

### 3.1 Bounded Fix Preference

- specialist 결과가 크더라도 실제 수정은 요청 경계 안에서 가장 작은 complete fix를 우선한다.
- cross-layer 문제라도 전면 리팩터링보다 연결 불일치 한두 곳을 닫는 쪽을 기본값으로 둔다.

## 3.2 Delegation Prompt Contract

위임 프롬프트에는 가능하면 아래 6요소가 있어야 한다.

1. TASK
2. EXPECTED OUTCOME
3. REQUIRED TOOLS
4. MUST DO
5. MUST NOT DO
6. CONTEXT

## 3.5 Failure Escalation

release loop 안에서 실패가 누적되면 아래 규칙으로 escalation한다.

1. 2회 연속 같은 성격의 실패 -> deeper review 고려
2. 3회 연속 같은 부류의 실패 -> 원인 재평가 우선
3. 큰 수정 완료 후 리스크 잔존 -> sanity review 고려
4. blocker는 아니지만 방향 불확실성이 커짐 -> 계획 재검토

## 4. `sisyphus_workflow` vs `sisyphus_claude`

| 상황 | 기본 선택 |
|---|---|
| 단건 구현/수정/조사 | `sisyphus-workflow` |
| 서비스 전체 출시 수준 끌어올리기 | `sisyphus_claude` |
| 국소 문제지만 여러 차례 재계획 예상 | `sisyphus_claude` |
| 진행 중간 설명이 필요한 작업 | `sisyphus-workflow` |
| 마지막에 한 번만 보고하는 작업 | `sisyphus_claude` |

두 스킬은 독립이며 자동 호출 관계는 없다.

### 더 직관적인 구분

- `sisyphus-workflow`:
  - 일반 구현/수정/조사
  - 중간 설명이 자연스러운 작업
  - 작업 범위를 사용자가 더 자주 조정하는 흐름

- `sisyphus_claude`:
  - 끝까지 밀고 가는 자율 실행 흐름
  - 마지막에 한 번만 정리받고 싶은 작업
  - 범위를 출시 가능 수준으로 닫는 성향이 필요한 작업

### `sisyphus_claude`를 피하는 편이 나은 경우

- 중간 reasoning을 계속 공유해야 하는 협업형 작업
- 단순 정보 질문이나 짧은 설명 요청
- release-loop보다 빠른 단건 처리만 필요한 작업

### 전환 기준

- 단건 해결 -> 기본은 `sisyphus-workflow`
- 출시 수준 수렴 -> 기본은 `sisyphus_claude`
- 시작은 작았지만 목표가 서비스 전체 품질로 커짐 -> `sisyphus_claude` 관점으로 전환

## 5. Prompt Set Examples

### 작은 작업 프롬프트
- `hello.txt 파일을 만들고 hello를 써줘`
- 기대: 범위를 넓히지 않고 파일 생성 + 직접 검증 후 종료

### 중간 작업 프롬프트
- `이 기능 흐름의 fixture marker를 release marker로 바꾸고 관련 검사와 테스트가 통과하도록 해줘`
- 기대: 관련 파일만 수정하고 관련 검증만 수행

### 서비스 전체 프롬프트
- `이 서비스를 초기 출시 가능 수준까지 끌어올려줘`
- 기대: release loop를 넓게 적용하고 핵심 흐름, 설정, 실패 상태, 검증까지 폭넓게 점검
