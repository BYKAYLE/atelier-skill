# Sisyphus Claude Known Limitations

## 1. Hook vs Model Boundary

- 일부 위험 요청은 hook이 막기 전에 모델이 먼저 중단한다.
- 따라서 모든 차단이 항상 "hook direct block"으로 관찰되지는 않는다.

## 2. Stop Policy

- 현재 stop 정책은 balanced 안정형이다.
- semantic 품질 판정기처럼 깊게 판단하지는 않는다.

## 3. Red-Team Ceiling

- 아주 복잡한 우회 (`base64` 다단계 decode, 복합 heredoc chain, 다중 프로세스 우회)는 장기 hardening 대상이다.

## 4. Environment Dependency

- repo clone의 의존성/도구 상태가 baseline 검증에 영향을 줄 수 있다.
- 일부 repo는 postinstall, system dependency, auth, signing 설정 때문에 검증 비용이 커질 수 있다.

## 5. Delegation Verification Gap

- real-repo delegation 사례는 이제 여러 건 확보됐지만, 매우 큰 서비스 repo에서 반복적인 multi-specialist orchestration을 충분히 검증한 단계는 아직 아니다.
