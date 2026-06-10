# Sisyphus Claude Profiles

이 문서는 `sisyphus_claude`를 어떤 강도로 운영할지에 대한 실전 가이드를 정리한다.

## 1. Balanced (기본 권장)

- 대상: 대부분의 실제 작업
- 특징:
  - 범위를 요청 경계에 맞춰 닫는다.
  - `Stop`은 첫 종료 시도만 검증 유도
  - 파괴적 작업은 계속 확인 필요
- 추천 상황:
  - 일반 개발 작업
  - 국소 수정 + 관련 검증
  - 서비스 범위 작업이지만 무한 루프는 피하고 싶을 때
  - external doc lookup이나 internal exploration이 필요하지만 수정은 bounded fix로 닫히는 작업

## 2. Strict

- 대상: 고위험 변경, 큰 출시 전 점검, 민감한 리팩터링
- 특징:
  - 더 많은 검증 증거 요구
  - 종료 전에 검증 누락을 더 보수적으로 본다.
  - 필요하면 별도 sanity review까지 포함
- 추천 상황:
  - 배포 전 최종 점검
  - 인증/권한/설정/런타임 경계 수정
  - 여러 모듈이 함께 바뀌는 경우
  - hook block / blocker question / model preemption을 더 엄밀히 구분해야 하는 고위험 요청

## 3. Lightweight

- 대상: 작은 파일 작업, 문구 수정, 단순 생성/국소 수정
- 특징:
  - 범위 확장 금지
  - 직접 검증 위주
  - 관련 없는 빌드/테스트 억지 실행 금지
- 추천 상황:
  - 단일 파일 생성
  - 텍스트/문구 수정
  - 국소 설정 변경
  - repo boundary를 거의 넘지 않는 직접 수정

## 4. Stop Policy Interpretation

- Balanced: 첫 stop에서 검증 유도 후 정상 종료 가능
- Strict: 더 강한 검증 근거가 필요할 수 있음
- Lightweight: 파일 존재/내용 확인 같은 직접 검증이면 충분할 수 있음

현재 로컬 구현은 **Balanced**에 가장 가깝다.

## 4.5 Validation-Backed Examples

- Balanced:
  - BizAutomate OpenAI SDK v6 review
  - BizAutomate public sign flow bugfix
  - ByDrive settings save flow bugfix
- Strict:
  - destructive/deploy guard classification review
  - auth/runtime boundary 재점검
- Lightweight:
  - fixture marker 변경
  - 단일 파일 생성/문구 수정

## 5. Command Mapping

- 기본: `/sisyphus_claude` -> Balanced
- 엄격 운영: `/sisyphus_claude_strict`
- 국소 작업: `/sisyphus_claude_lightweight`
- 명시적 기본 호출: `/sisyphus_claude_balanced`

위 매핑은 command files가 active Claude home에 설치되었을 때의 동작 기준이다.
패키징된 repo 상태만으로는 활성 명령이 보장되지 않으며, 설치 절차는 repo 루트의 `INSTALL.md`를 따른다.
