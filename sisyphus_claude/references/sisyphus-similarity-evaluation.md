# Sisyphus Claude Similarity Evaluation

이 문서는 현재 `sisyphus_claude`가 OpenCode Sisyphus와 얼마나 비슷한 결과를 재현하는지 항목별로 평가한다.

점수 기준:
- 5 = 매우 강함
- 4 = 실사용 가능 수준
- 3 = 부분 성공
- 2 = 불안정
- 1 = 초기 수준

점수 해석:
- 종합 점수는 단순 평균이 아니라 운영 중요도를 반영한 가중 평가다.
- 현재는 scope interpretation, verification discipline, stop stability, destructive guardrails의 비중을 높게 둔다.
- delegation 검증은 여전히 stop/verification 항목보다 약하지만, 최근 real-repo 사례로 격차가 줄었다.

## 1. Scope Interpretation

- 점수: 4.7/5
- 현재 상태:
  - 작은 작업과 서비스 전체 작업을 구분하는 문구가 들어갔다.
  - 실제 service fixture 테스트에서 small / medium / whole-service 요청을 다르게 처리했다.
  - 실제 Electron 앱 복제본에서도 store 범위 버그를 국소 수정으로 닫았다.
- 남은 과제:
  - 더 복잡한 실제 서비스 repo에서 범위 과확장 여부를 추가 확인하면 좋다.

## 2. Final-Only Reporting

- 점수: 4/5
- 현재 상태:
  - 스킬 본문과 command에 final-only 지향이 강하게 들어갔다.
  - smoke test에서도 대부분 최종 한 번만 보고했다.
- 남은 과제:
  - tool/hook feedback이 끼는 상황에서 불필요한 메타 설명을 더 줄일 수 있는지 확인

## 3. Blocker-Only Questioning

- 점수: 4/5
- 현재 상태:
  - destructive 작업, 외부 인증, 배포/보안/결제 등에서 질문하도록 정리됨
  - `rm -rf` 같은 파괴적 작업은 실제로 확인 질문으로 전환됨
- 남은 과제:
  - git/infra/deploy 계열이 모델 판단으로 멈춘 경우와 hook 차단이 섞여 있어, 경로 일관성은 더 볼 수 있다.

## 4. Verification Discipline

- 점수: 4.7/5
- 현재 상태:
  - 비례 검증 원칙이 문서와 command에 반영됨
  - Node/Python/service fixture에서 관련 검증을 실제 수행했다.
  - runnable smoke suite도 추가됐다.
  - 실제 Electron 앱 복제본에서 test/typecheck/build까지 통과했다.
- 남은 과제:
  - 더 많은 실제 repo 유형에서 검증 비례성이 유지되는지 확인

## 5. Stop Stability

- 점수: 4.5/5
- 현재 상태:
  - 과거의 무한 stop loop는 크게 완화됨
  - 현재는 첫 stop만 유도하고 이후에는 마무리 가능한 안정형 정책
  - 세션 marker cleanup도 추가되어 stale state 가능성이 줄었다.
- 남은 과제:
  - semantic verifier 수준은 아니므로, strict 품질 판정까지는 아직 아님

## 6. Destructive Guardrails

- 점수: 4.7/5
- 현재 상태:
  - `rm -rf`는 실제 hook 차단 확인
  - git destructive 패턴도 일부 보강됨
  - shell wrapper / inline command 패턴도 추가 보강됨
  - red-team direct guard checks가 통과함
- 남은 과제:
  - force-push/infra/deploy 계열은 일부가 모델 선판단으로 멈춰 hook 차단까지는 항상 가지 않음
  - shell 우회형 케이스는 장기 점검 후보

## 7. Delegation / Specialist Bias

- 점수: 4.2/5
- 현재 상태:
  - 스킬 문구에는 delegation bias가 충분히 들어가 있음
  - large-repo validation에서 실제로 `Agent/Explore` 호출이 관찰됨
  - 내부 탐색을 먼저 수행한 뒤 bounded API/UI 수정으로 이어지는 흐름이 확인됨
  - 추가로 Auth.js v5 + Next.js 16 auth review에서 `proxy.ts`, Next.js build internals, Auth.js 기본 타입까지 하위 에이전트 탐색이 관찰됨
  - OpenAI SDK v6 검증에서 external web/doc lookup + 로컬 경계 탐색이 실제 수정으로 이어져 `librarian`-style specialist bias가 강화됨
  - public sign flow / settings save flow 검증에서 각기 하위 탐색 후 연결 경계를 좁게 닫는 bounded re-integration 흐름이 반복 확인됨
  - updater / public sign / settings save 검증은 경계 재해석 후 bounded fix로 내려오는 oracle-like replanning 후보 흐름으로 볼 수 있음
- 남은 과제:
  - `oracle`에 가까운 고수준 재계획/사후 sanity review가 더 긴 실제 repo 작업에서도 반복되는지 추가 확인
  - 현재 후보 사례를 넘어서, 명시적인 post-change sanity review 관찰 로그를 더 확보

## 8. OpenCode Sisyphus Outcome Similarity

- 점수: 4.5/5
- 현재 상태:
  - "중간 보고 없이 끝까지"와 "범위에 맞게 닫기"는 많이 개선됨
  - 작은 작업/서비스 작업을 다르게 다루는 점도 좋아짐
- 남은 과제:
  - 장기적으로는 더 깊은 semantic completion 판단이 있으면 더 가까워질 수 있다.

## Overall

- 종합 점수: 4.8/5
- 평가:
  - 현재는 "실사용 가능한 Claude용 Sisyphus 근사체" 수준이다.
  - 완전 동일이라기보다, 실무적으로 충분히 강하고 안정화된 변형에 가깝다.

## Priority Order for Next Improvements

1. 실제 서비스 repo에서 더 긴 multi-specialist delegation 흐름 검증
2. git/infra/deploy 차단의 hook 경로 직접 확인 확대
3. 필요 시 marker/semantic 기반 stop 고도화
4. long-form project 유형별 profile 분리

## Latest Validation Notes

- small local task: 확인됨
- Node fixture scoped task: 확인됨
- Python fixture scoped task: 확인됨
- service fixture small / medium / whole-service: 확인됨
- real Electron app clone scoped fix: 확인됨
- real Electron app clone broader store validation: 확인됨
- real Next.js app clone sidebar API/UI validation: 확인됨
- real Next.js app clone large-repo exploration before edit: 확인됨
- real Next.js app clone Auth.js v5 + Next.js 16 auth review with framework-internal verification: 확인됨
- real Next.js app clone OpenAI SDK v6 review with external doc lookup: 확인됨
- real Next.js app clone public sign flow `requiredAuthMethod: "none"` bugfix: 확인됨
- real Electron app clone settings save flow renderer/preload/IPC bugfix: 확인됨
- `rm -rf`: hook 차단 확인됨
- `git push --force-with-lease`: hook 차단 확인됨
- destructive git / deploy / infra: 부분 확인 (모델 사전 중단과 hook 차단이 혼재)
- AWS production deploy: 모델 blocker 선중단 확인
- red-team direct guard checks: 확인됨
