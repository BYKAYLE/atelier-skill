# Sisyphus Claude Project-Type Guide

## Node Project

- 기본 기대:
  - `package.json` 스크립트 우선 활용
  - 관련 `check`, `test`, `build` 중 범위에 맞는 것만 선택
- 작은 작업:
  - 관련 파일 + 관련 스크립트만 확인
- 전체 작업:
  - 핵심 스크립트와 사용자 흐름까지 폭넓게 점검

## Python Project

- 기본 기대:
  - 환경에 있는 테스트 경로를 현실적으로 선택
  - `pytest`가 없으면 `unittest` 같은 대체 경로 고려
- 작은 작업:
  - import 경로, 실행 경로, 관련 테스트만 확인
- 전체 작업:
  - 런타임, 설정, 테스트 체계, 실패 상태까지 넓게 점검

## Fullstack / Multi-Module Project

- 기본 기대:
  - 요청이 국소면 관련 모듈만 닫는다.
  - 요청이 서비스 전체면 모듈 간 경계까지 본다.
- 작은 작업:
  - web 수정이면 api까지 자동 확장하지 않는다.
- 전체 작업:
  - 핵심 모듈 간 흐름과 검증을 함께 본다.

## Electron / Desktop App Project

- 기본 기대:
  - renderer 수정이면 관련 store/component/test를 우선 본다.
  - preload/shared/main 계약을 함부로 넓히지 않는다.
  - 검증은 `test`, `typecheck`, `build` 중 영향 범위에 맞춰 선택한다.
- 작은 작업:
  - 국소 store 버그면 해당 store와 테스트만 우선 수정
  - 관련 검증까지만 하고 main/preload 전역 리팩터링으로 번지지 않는다.
- 전체 작업:
  - main/preload/renderer/shared 계약과 빌드 흐름까지 넓게 본다.

## Static / Content-Oriented Project

- 기본 기대:
  - 콘텐츠, 링크, 렌더 결과, 빌드 유무를 비례적으로 확인
- 작은 작업:
  - 파일 결과 직접 확인이 충분할 수 있다.

## Common Rule

- 프로젝트 타입과 무관하게, 검증은 항상 요청 범위와 변경 크기에 비례시킨다.
