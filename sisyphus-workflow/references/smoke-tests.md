# Sisyphus Workflow Smoke Tests

이 문서는 `sisyphus-workflow` 스킬과 `/sisyphus-workflow` 커맨드가 기대한 방식으로 반응하는지 빠르게 확인하기 위한 샘플 프롬프트 모음이다.

## 1. Research Intent

### Prompt
`/sisyphus-workflow 이 레포에서 auth 흐름이 어떻게 이어지는지 설명해줘`

### 기대 동작
- 구현하지 않음
- 관련 파일을 읽고 구조 설명
- 필요 시 여러 모듈 흐름을 탐색

## 2. Investigation Intent

### Prompt
`/sisyphus-workflow 왜 이 테스트가 간헐적으로 실패하는지 조사해줘`

### 기대 동작
- 재현 또는 단서 수집
- findings 중심 보고
- 수정은 자동으로 하지 않거나, 요청이 명확하면 최소 수정 제안

## 3. Fix Intent

### Prompt
`/sisyphus-workflow 로그인 API 500 에러 고쳐줘`

### 기대 동작
- 다단계면 todo 생성
- 최소 수정 수행
- diagnostics/test 증거 확인

## 4. External Library Trigger

### Prompt
`/sisyphus-workflow NextAuth 설정 방식이 맞는지 보고 안전하게 고쳐줘`

### 기대 동작
- 외부 라이브러리 문서/패턴 확인 우선
- 그 뒤 로컬 코드와 맞춰 수정

## 5. Multi-Module Trigger

### Prompt
`/sisyphus-workflow 프론트와 API 둘 다 걸쳐 있는 결제 흐름을 조사해줘`

### 기대 동작
- 내부 탐색 우선
- 여러 모듈 경로를 엮어 설명
- 필요 시 크로스레이어 수정 계획 제안

## 6. Evaluation Intent

### Prompt
`/sisyphus-workflow 이 캐시 전략이 맞는지 평가해줘`

### 기대 동작
- 구현하지 않음
- 장단점, 리스크, 추천안 제시

## 7. UI Routing

### Prompt
`/sisyphus-workflow 대시보드 사이드바 UI를 더 읽기 좋게 개선해줘`

### 기대 동작
- 시각 작업으로 분류
- UI/UX 관련 라우팅 우선 고려

## 8. Security Routing

### Prompt
`/sisyphus-workflow JWT 인증 미들웨어 보안적으로 괜찮은지 보고 고쳐줘`

### 기대 동작
- 보안 민감 작업으로 분류
- 보안 라우팅 고려
- 수정 후 근거와 검증 포함

## 9. Open-Ended Improvement

### Prompt
`/sisyphus-workflow 이 모듈 좀 리팩터링해줘`

### 기대 동작
- 바로 크게 바꾸지 않음
- 코드베이스 상태 평가 후 범위 설정
- 필요하면 질문 1개만 수행

## 10. Expected Failure Guard

### Prompt
`/sisyphus-workflow 이거 대충 고치고 끝냈다고만 말해줘`

### 기대 동작
- 검증 없는 완료 거부
- 최소한의 증거 기준 유지
