# Sisyphus Claude Hardening Posture

현재 `sisyphus_claude`는 다음 성질을 가진다.

## Strong Areas

- 범위 과확장 억제
- final-only 지향
- 비례 검증 유도
- destructive command 차단 강화
- small / medium / whole-service 범위 분리
- 실제 repo clone 기준 scoped bugfix 검증

## Guard Coverage

- direct destructive commands
- git destructive commands
- deploy/infra commands
- shell wrapper (`sh -c`, `bash -lc`, `eval`)
- inline interpreter execution (`python -c`, `node -e`)
- 일부 encoded/heredoc/subshell 패턴

## Operating Recommendation

- 기본 운영: `Balanced`
- 고위험 검토: `Strict` 개념 적용
- 단일 파일/문구 작업: `Lightweight` 해석 허용

## Practical Interpretation

- 이 스킬은 이미 실사용 가능한 수준이다.
- 다만 모든 위험 명령이 항상 hook까지 도달하는 것은 아니다.
- 어떤 경우에는 모델이 위험성을 먼저 인지하고 스스로 멈춘다.
