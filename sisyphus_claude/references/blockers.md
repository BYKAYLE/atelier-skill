# Sisyphus Claude Blockers

이 문서는 사용자에게 질문할 수 있는 예외 상황만 정리한다.

## 질문 가능한 경우

### 1. Destructive Action
- 데이터 삭제
- 대규모 파일 제거
- 되돌리기 어려운 마이그레이션

### 2. External Credentials or Real-Service Access
- 실서비스 로그인 필요
- 외부 계정 인증 필요
- API key, secret, account id 필요

### 3. High-Risk Irreversible Domains
- 결제 실제 연동
- 보안 posture 변경
- 배포 또는 프로덕션 설정 변경

### 4. Missing Critical Information That Repo Cannot Answer
- 필수 환경변수 이름/값 없음
- 외부 시스템 endpoint 미상
- 두 개 이상의 합리적 해석이 있고 결과가 크게 달라짐

## 질문하면 안 되는 경우

- 사소한 구현 선택
- naming, formatting, small structure choice
- repo를 읽으면 알 수 있는 패턴
- 안전한 기본값이 있는 경우
- 단순 진행 상황 공유 욕구

## 질문 형식

질문이 필요하면 짧고 정확하게 묻는다.

1. 왜 막혔는지
2. 무엇이 필요한지
3. 기본 추천안이 무엇인지

그 외 설명은 길게 하지 않는다.

## 질문 예시

### 파괴적 작업
- `이 작업은 기존 파일을 되돌릴 수 없이 지웁니다. 현재 범위에서는 파괴적 작업이라 확인이 필요합니다. 제 추천은 먼저 백업 없이 진행하지 않는 것입니다. 그대로 진행할까요?`

### 외부 인증 필요
- `계속 진행하려면 실제 서비스 로그인 정보가 필요합니다. repo만으로는 진행할 수 없습니다. 가능하면 테스트 계정 사용을 추천합니다. 계정 정보를 제공할 수 있나요?`

### 배포/보안/결제 결정
- `이 단계는 실제 배포/보안 posture에 영향을 줍니다. 되돌리기 어려워 확인이 필요합니다. 제 추천은 로컬/스테이징 검증 후 진행입니다. 그대로 반영할까요?`
