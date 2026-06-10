# Sisyphus Claude Release Summary

`sisyphus_claude`는 Claude 환경에서 OpenCode Sisyphus에 가까운 결과물을 만들기 위해 설계된 launch-readiness 오케스트레이터다.

## Current Position

- 상태: 실사용 가능
- 기본 프로파일: `Balanced`
- 핵심 목표: 요청 범위를 출시 가능 수준으로 닫되, 관련 없는 polish로 무한 확장하지 않기

## Strongest Verified Behaviors

- scope-sensitive completion
- final-only reporting 성향
- proportionate verification
- destructive bash guard
- real-repo bounded fix 성향
- specialist-heavy 탐색 후 재통합

## Best Evidence

- Next.js clone OpenAI SDK v6 검증: external doc lookup + local route mapping + bounded fix
- Next.js clone public sign flow 검증: page/API/schema 경계 버그를 국소 수정으로 종료
- Electron clone settings save 검증: renderer store / preload / IPC validation 경계를 함께 닫음
- direct guard checks + smoke suite 반복 통과

## Recommended Usage

- 서비스/기능을 중간 보고 없이 끝까지 닫고 싶을 때
- 여러 레이어를 확인해야 하지만 결과는 bounded fix로 끝내야 할 때
- 출시 직전 품질 정리, 설정 경계 정리, 런타임 연결 문제를 다룰 때

## When Not To Use

- 단순 정보 질문
- 짧은 단건 수정인데 중간 상호작용이 더 중요한 경우
- 사용자가 단계별 reasoning 공유를 원할 때

## Remaining Gaps

- 매우 큰 실제 서비스 repo에서 반복적인 multi-specialist orchestration
- model preemption과 hook direct block 경계의 추가 문서화
- semantic stop judge 수준의 종료 판정

## Operator Recommendation

- 기본은 `/sisyphus_claude`
- 고위험 변경은 `/sisyphus_claude_strict`
- 작은 로컬 작업은 `/sisyphus_claude_lightweight`

단, 위 명령은 이 repo에 패키징된 것만으로 활성화되지 않는다. 실제 사용 전에는 active Claude home에 설치해야 한다.
