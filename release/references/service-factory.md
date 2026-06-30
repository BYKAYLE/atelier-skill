# Service Factory Mode — Google-style Multi-Agent Delivery

사용자이 "서비스를 최종 제품까지 만들어"라고 요청했을 때 Stella가 최상위 지휘자로 목표와 에이전트 토폴로지를 정하고, Release가 실행 컨트롤러/게이트 관리자로 여러 전문 에이전트를 움직여 제품 수준까지 밀고 가는 표준 모드다.

참고 사례: Google Antigravity 2.0의 OS 빌드 사례는 Sentinel, Orchestrator, Explorer, Worker, Reviewer, Critic, Auditor 같은 역할 분리와 다수 subagent를 사용했다. 이 문서는 그 방식을 Atelier 로컬 환경의 Stella/Release/Probe/security-router 구조에 맞춘다.

## 핵심 원칙

1. **Stella가 command_owner다.** 목표 해석, 우선순위, 금지선, 에이전트 생성 기준, 최종 완료 판단은 Stella가 가진다.
2. **Release는 실행 컨트롤러다.** 직접 코딩만 하지 않고 state ledger, dispatch/collect, file lease, gate, handoff, readiness evidence를 관리한다.
3. **온톨로지가 기준이고 칸반은 투영판이다.** 칸반 카드 이동만으로 완료를 판단하지 않는다.
4. **한 에이전트가 만든 것을 같은 에이전트가 최종 승인하지 않는다.** Worker와 Reviewer/Auditor를 분리한다.
5. **완료 조건은 산출물이 아니라 검증 증거다.** 빌드, 테스트, 타입체크, Probe, 보안 리뷰, 배포 smoke가 있어야 한다.
6. **상태는 파일로 남긴다.** `SOT/service-factory-state.json`이 재개, 교차 검토, 비용 통제의 기준이다.
7. **사용자 승인 게이트는 자동 통과하지 않는다.** DB/데이터 삭제, 프로덕션 배포, 유료 API 예산 초과, 외부 발화, 공격성 보안 테스트는 명시 승인 전까지 pending이다.

## Intake Contract — 4항목 완결성 게이트 (260603 신설)

사용자가 스텔라팩토리를 자연어 한 덩어리로 요청하면 goal 외 항목이 비어 downstream 게이트에서 막연히 멈춘다. 그래서 **시작 시점에 4항목 완결성을 강제**한다.

| 항목 | key | 의미 |
|------|-----|------|
| 목표 | `goal` | 무엇을 만드는가 |
| 금지선 | `forbidden` | 절대 하면 안 되는 것/영역 |
| 완료기준 | `definition_of_done` | 무엇이 충족되면 done 인가 |
| 승인 위임 범위 | `approval_delegation` | 어디까지 사람 확인 없이 자율 허용인가 |

### 역할 분리 (중요)
- **스크립트(`service_factory_intake_contract.py`)는 결정적 게이트다.** "4항목이 채워졌는가"만 본다. 자연어 의미·품질은 판단하지 않는다 (빈값/placeholder만 거른다).
- **오케스트레이터(Stella/Release = LLM)가 자연어를 해석한다.** 사용자의 자연어 요청을 4항목으로 분해하고, **비어 있는 항목만** 사용자에게 되묻고, 답을 `intake --set`으로 채운다.

이 분리 덕분에 오케스트레이터가 깜빡 묻지 않아도 `plan`/`run`/`dispatch`/`dispatch-workflow`가 exit 3으로 막아 준다.

### 표준 흐름
```bash
# 1. 자연어 요청을 4항목으로 분해해 가능한 만큼 init 에 넘긴다
python3 service_factory.py init --project <p> --goal "<목표>" \
  [--forbidden "<금지선>"] [--dod "<완료기준>"] [--approval-delegation "<위임범위>"]
# 출력의 intake_complete / missing_fields / clarification_questions 확인

# 2. missing 이 있으면 → 오케스트레이터가 clarification_questions 를 사용자에게 묻는다
#    (AskUserQuestion). 채워진 항목은 다시 묻지 않는다.

# 3. 사용자 답을 채운다 (항목당 1회)
python3 service_factory.py intake --project <p> --set forbidden --value "<답변>"
python3 service_factory.py intake --project <p> --set definition_of_done --value "<답변>"
python3 service_factory.py intake --project <p> --set approval_delegation --value "<답변>"

# 4. intake_complete=true 가 되면 plan/run 이 정상 진행
python3 service_factory.py plan --project <p>
```

`intake --project <p>` (인자 없이)는 현재 4항목 상태와 남은 질문을 보여준다. 4항목이 미충족이면 `plan/run/dispatch/dispatch-workflow`는 `intake_clarification_required`(exit 3)로 차단하고 `clarification_questions`를 출력한다. 긴급 우회는 `--allow-incomplete-intake`(권장하지 않음).

주의: `approval_delegation`은 "무인 허용 경계"를 표현할 뿐, 영구 안전 게이트(db_data_deletion/production_deploy/paid_api_budget/external_communication/offensive_security)는 이 값과 무관하게 항상 사람 승인을 요구한다.

## 왜 에이전트가 많이 필요한가

| 이유 | 설명 | 없을 때 생기는 문제 |
|------|------|---------------------|
| 범위 분할 | 제품/아키텍처/프론트/백엔드/인프라/보안/QA는 서로 다른 사고 모드다. | 한 에이전트가 큰 맥락을 잃고 얕은 구현으로 끝낸다. |
| 병렬 처리 | 독립 표면을 동시에 진행해 벽시계를 줄인다. | 모든 일을 순차 처리해 긴 작업이 중간에 끊긴다. |
| 독립 검수 | 만든 에이전트와 검수 에이전트를 분리한다. | 자기검토로 false-green이 난다. |
| 전문성 | 보안, 성능, DB, 배포는 별도 기준이 필요하다. | 일반 개발 관점으로 위험을 놓친다. |
| 재개성 | 작업 상태와 산출물을 파일로 넘겨 후속 에이전트가 이어받는다. | 컨텍스트 한계 뒤에 이전 판단을 반복한다. |
| 실패 격리 | 실패한 Worker를 교체해도 전체 파이프라인은 유지된다. | 하나가 막히면 전체가 멈춘다. |

## Atelier 역할 매핑

| Google식 역할 | 로컬 역할 | 책임 |
|---------------|-----------|------|
| Sentinel/Commander | Stella | 사용자 요청 해석, 목적/우선순위/금지선 판단, AgentTopology 생성, 최종 완료/반려 |
| Runtime Controller | Release | Service Factory 상태 원장, 에이전트 배치 실행, dispatch/collect, 게이트 통과 관리 |
| Explorer | code-mapper, search-specialist, docs-researcher, NightLab 협조 | 코드/문서/시장/기술 탐색 |
| Planner | product-manager, architect-reviewer, business-analyst | PRD, 아키텍처, 수용 기준 |
| Worker | frontend/backend/fullstack/devops/data 등 | 실제 구현 |
| Integrator | Release 또는 지정 Worker | 병합, 충돌 정리, end-to-end 연결 |
| Reviewer | reviewer, code-reviewer, qa-expert | 구현 정확성, 회귀, 테스트 범위 검토 |
| Critic | risk-manager, chaos-engineer, performance-engineer | 실패 모드, 비용, 복원력, false-green 공격 |
| Auditor | Probe, security-router, security-auditor, compliance-auditor | 독립 런타임 검수와 보안/컴플라이언스 검토 |

## 상태 머신

`SOT/service-factory-state.json`의 stage state는 기존 completion-first vocabulary를 따른다.

```
queued -> in_progress -> validation_required -> done
                   \-> blocked
                   \-> discarded
```

Service Factory 전체 상태:

| 상태 | 의미 |
|------|------|
| `draft` | 목표와 역할을 구성 중 |
| `running` | Worker/Reviewer/Auditor가 진행 중 |
| `blocked` | 승인 게이트, 외부 의존성, 기술 불가능으로 중단 |
| `validation_required` | 구현은 있으나 독립 검증이 남음 |
| `done` | 모든 필수 게이트와 증거가 통과 |
| `interrupted` | 컨텍스트 한계나 사용자 중단으로 재개 필요 |

## 표준 스테이지

| Stage | 주역 | 완료 증거 |
|-------|------|-----------|
| intake | Stella/Release | 목표, 금지선, 성공 기준 |
| current_state | Explorer (code-mapper) | 레포·런타임·SoT 설치 baseline |
| research_intelligence | k-dense-researcher + market-researcher + knowledge-synthesizer + research-methodologist | research_dossier, evidence_map, research_qc |
| development_plan | Planner (project-manager + architect) | gap_analysis, task_packets, verification_strategy |
| product_brief | Product/BA | PRD 또는 brief, acceptance criteria |
| repo_map | Explorer | 코드맵, 실행 방법, 위험 표면 |
| architecture | Architect | 기술 선택, 경계, 데이터 흐름 |
| decomposition | Release | 작업 분할, 파일 소유권, 병렬 가능성 |
| parallel_implementation | Workers | 수정 파일, 로컬 빌드/테스트 |
| integration | Integrator | 충돌 정리, end-to-end 연결 |
| verification | QA/Reviewer/Probe | 테스트, 타입체크, Probe report |
| security_review | security-router/security agents | CRITICAL=0, HIGH=0 또는 명시 예외 |
| deployment_readiness | DevOps/SRE | staging smoke, rollback plan |
| final_audit | Release/Stella | 게이트 요약, 남은 위험, 최종 보고 |

260603 갱신: `current_state` + `research_intelligence` + `development_plan` 3 stage는 intake 직후 들어가는 진단·연구·계획 스테이지로, v0.2 부터 코드에 정의돼 있다(`stage_spec_map()` 13 stage). development_plan 의 `task_packets`는 후속 decomposition 의 입력이 된다.

## 온톨로지와 칸반 경계

| 계층 | 책임 |
|------|------|
| Stella ontology | 목표 해석, 에이전트 생성 기준, 금지선, 완료 판단 |
| State ledger | 실제 stage, agent request, result, gate, readiness의 원천 |
| Kanban projection | state ledger를 사람이 보기 쉽게 보여주는 화면 |

칸반은 실행판이지 판단 기준이 아니다. 스텔라팩토리 진행 여부, 새 에이전트 필요 여부, 완료 판단은 온톨로지와 state ledger가 결정한다.

## 동적 에이전트 추가 기준

Stella는 아래 조건 중 하나가 생기면 AgentBlueprint를 만들고, Release는 해당 blueprint를 기존 에이전트, 일회성 AgentInstance, 또는 영구 AgentManifest 후보로 실행/기록한다.

| 조건 | 추가 에이전트 |
|------|---------------|
| 수정 범위가 프론트/백엔드/인프라 등 2개 이상 표면으로 갈라짐 | 표면별 Worker |
| Worker가 2회 실패하거나 같은 오류를 반복 | 대체 Worker + Debugger |
| 인증/결제/권한/개인정보/보안 헤더가 등장 | security-auditor/security-engineer + Probe |
| DB schema, migration, query plan 변경 | database-administrator 또는 sql-pro |
| 배포, 도메인, SSL, 컨테이너, CI 변경 | deployment-engineer/devops-engineer |
| UI 산출물이 있음 | Probe + accessibility-tester 또는 browser-debugger |
| 성능/SLO/장애복구가 성공 기준에 포함 | performance-engineer 또는 sre-engineer |
| 명세가 모호하거나 사용 흐름이 큼 | product-manager/business-analyst |

## 에이전트 생성 증거 기준

| 이름 | 의미 | 생성 증거 |
|------|------|-----------|
| AgentBlueprint | 목표에 맞춘 새 전문 역할 설계 | role, specialization, input/output contract, allowed paths, done_when |
| AgentInstance | 실제 실행된 하위 에이전트 세션 또는 작업 단위 | instance id, runtime, artifact_dir, result.json |
| AgentManifest | 다음에도 재사용 가능한 영구 에이전트 정의 | `~/.codex/agents/*.toml` 또는 프로젝트 agent manifest 후보 |
| agent_request | 실행해야 할 작업 패킷 | state의 queued/in_progress/completed request |

`agent-prompts/*.md`, worktree, local worker result만으로는 새 에이전트를 만들었다고 주장하지 않는다.

## 승인 게이트

아래는 자동 실행 금지다. 상태 파일에 `pending`으로 남기고 사용자 승인이 있어야 한다.

| Gate | 자동 금지 항목 |
|------|----------------|
| `db_data_deletion` | DB 삭제, 데이터 삭제, destructive migration, volume 삭제 |
| `destructive_filesystem` | `rm -rf` 류 광범위 삭제, 시스템 디렉터리 변경 |
| `production_deploy` | 실제 사용자 트래픽에 영향 주는 prod deploy, rollback 불가 변경 |
| `paid_api_budget` | 새 유료 API 사용, 예산 초과 가능 작업 |
| `external_communication` | 고객/파트너/외부 서비스에 메시지 전송 (`git push`/`gh pr merge`/`gh release create`/Slack/Discord webhook 등 포함) |
| `offensive_security` | 침투 테스트, 공격성 스캔, exploit 검증, 광범위 스캔 |

## Anti False-Green 규칙

1. 테스트가 mock만 검증하면 완료로 보지 않는다.
2. UI는 스크린샷이나 Probe report 없이 완료로 보지 않는다.
3. API는 실제 dev/staging 서버 호출 또는 contract test 없이 완료로 보지 않는다.
4. 보안 검토는 Probe만으로 끝내지 않는다. 정적/코드 보안과 런타임 smoke를 분리한다.
5. Worker가 작성한 완료 보고는 Reviewer/Auditor의 독립 증거가 붙기 전까지 `validation_required`다.
6. "작동할 것"이라는 추정은 산출물이 아니다. 명령, exit code, report path를 기록한다.
7. `green` 선언 전 최소 4개 증거가 필요하다: 실행 명령, exit code, 산출물 경로, 독립 검증 결과.
8. 자기검토만 통과한 상태는 `self-check only`이며 `done`이 아니다.
9. 테스트를 하나도 실행하지 못한 완료 보고는 `validation_required` 또는 `blocked`다.

## 파일 Lease 규칙

다중 Worker는 파일 단위 충돌을 만들기 쉽다. Release는 stage 시작 전에 `file_leases`를 상태 파일에 남긴다.

260603 자동 seeder 신설: `command_plan` 이 `build_agent_requests` 후 `_fl_seed_file_leases_from_requests(state)` 를 호출해 각 agent_request 의 `owned_paths` 를 ledger 로 흡수한다. `request.kind` (worker/builder/explorer/planner/integrator/reviewer/critic/auditor/sentinel 등) 를 `LEASE_MODES` (read/write/review/integrate) 로 매핑한다. 같은 path 에 다중 write owner 가 감지되면 두 번째 owner 는 `mode=write_conflict` 로 표지되고, `completion_claim_guard` 가 `file_leases_write_conflict` / `file_leases_empty_during_write_stage` 를 blocker 로 발화한다 (Anti False-Green § 9규칙 정합). 분리 모듈: `release/scripts/service_factory_file_leases_seeder.py`.

| Lease | 의미 |
|-------|------|
| `read` | 읽기/분석만 허용 |
| `write` | 해당 path를 수정할 수 있는 유일한 소유자 |
| `review` | 수정하지 않고 findings만 작성 |
| `integrate` | 여러 Worker 산출물을 합치는 단일 통합자 |

규칙:

- 같은 파일 또는 디렉터리에는 동시에 `write` owner가 1명만 있어야 한다.
- Reviewer가 수정하기 시작하면 Reviewer가 아니라 Worker가 되며 새 Reviewer를 붙인다.
- 최종 병합은 단일 Integrator만 수행한다.
- 충돌이 감지되면 덮어쓰기 대신 해당 stage를 `validation_required`로 둔다.

## 비용과 확장 제한

기본 제한은 상태 파일의 `limits`에 기록한다.

| 제한 | 기본값 | 의미 |
|------|--------|------|
| `max_parallel_agents` | 3 | 동시에 달리는 실행 에이전트 수 |
| `max_child_agents` | 12 | 한 Service Factory run에서 생성할 수 있는 하위 에이전트 수 |
| `max_retries_per_stage` | 3 | 같은 stage 자동 재시도 한도 |
| `max_wall_clock_minutes` | null | 필요 시 명시하는 시간 한도 |

같은 목표에서 재시도가 3회를 넘으면 에이전트를 더 늘리지 않고 원인 분류로 전환한다. 같은 증거만 다시 읽는 루프가 2회 반복되면 중복 작업으로 보고 멈춘다.

## 중단/재개 필드

재개 가능하려면 모든 run이 아래를 남긴다.

- `current_owner`: 현재 stage 책임자
- `command_owner`: 전체 run의 최상위 지휘자. 스텔라팩토리에서는 항상 `Stella`
- `last_command`: 마지막으로 실행한 명령
- `last_artifact`: 마지막 확인 산출물
- `blocked_reason`: 막힌 이유
- `next_step`: 재개 시 첫 행동

재개 시 Stella는 command_owner와 목표를 확인하고, Release는 새 작업을 시작하기 전에 `service-factory-state.json`의 `run_log`, `resume`, `stages`를 먼저 확인한다.

## 실행 계약

1. Service Factory 시작 시:
   ```bash
   python3 ~/.claude/skills/release/scripts/service_factory.py init --project <project> --goal "<goal>" \
     [--forbidden "<금지선>"] [--dod "<완료기준>"] [--approval-delegation "<위임범위>"]
   ```
   init 결과에 `intake_complete`/`missing_fields`/`clarification_questions`가 포함된다. 미충족이면 §Intake Contract 흐름대로 사용자에게 묻고 `intake --set`으로 채운 뒤 진행한다. 미충족 상태로는 plan/run 이 exit 3 으로 막힌다.
2. Agent Runner 계획 생성:
   ```bash
   python3 ~/.claude/skills/release/scripts/service_factory.py plan --project <project>
   ```
   이 명령은 `agent_requests`, `missing_capabilities`, `execution_plan`, `watchdog`, `handoff`, `automatic_gates`를 상태 파일에 기록하고 `SOT/service-factory/agent-prompts/*.md`를 생성한다.
3. Runtime cycle 실행:
   ```bash
   python3 ~/.claude/skills/release/scripts/service_factory.py run --project <project>
   ```
   기본 `manual` backend는 agent launch artifact를 만들고 실제 subagent 실행은 차단 상태로 남긴다. 실제 CLI backend를 붙일 때는 `--backend command --agent-command-template "<argv template>"`을 사용한다.
4. Codex bridge dispatch/collect:
   ```bash
   python3 ~/.claude/skills/release/scripts/service_factory.py dispatch --project <project>
   python3 ~/.claude/skills/release/scripts/service_factory.py collect --project <project>
   python3 ~/.claude/skills/release/scripts/service_factory.py resolve-validation --project <project> --request <request-id> --evidence <review.md>
   ```
   `dispatch`는 실제 Codex subagent에게 넘길 `dispatch.md`와 `dispatch.json`을 만들고, `collect`는 subagent가 작성한 `artifact_dir/result.json`을 state로 흡수한다.

4-bis. Dynamic Workflow dispatch/collect (260602 신설, stage 단위 fan-out):
   ```bash
   python3 ~/.claude/skills/release/scripts/service_factory.py dispatch-workflow --project <project> [--stage <stage_id>] [--max-parallel N] [--max-requests M]
   # parent agent 가 Workflow 도구로 dispatch.workflow.js 를 실행 → 결과를 각 artifact_dir/result.json 으로 직렬화
   python3 ~/.claude/skills/release/scripts/service_factory.py collect --project <project>
   ```
   `dispatch-workflow`는 한 stage의 queued/in_progress request들을 모아 결정성 `parallel()` script 하나로 직조한다. parent agent는 Workflow 도구의 `scriptPath`로 그 script를 실행하기만 하면 N-way 병렬·worktree 격리·StructuredOutput schema 강제·budget 추적이 자동으로 적용된다. 결과 흡수는 기존 `collect`가 그대로 처리. **`spawn_runtime`을 채우는 권장 경로** — 외부 subprocess 없이 in-process로 동작.
5. 각 에이전트 배치 전:
   - 담당 stage
   - 소유 파일/표면
   - 성공 기준
   - 금지 작업
   - 예상 산출물 경로를 prompt에 포함한다.
6. 각 에이전트 완료 후:
   - 수정 파일
   - 실행한 검증 명령
   - 실패/차단 상태
   - 다음 에이전트가 읽을 산출물 경로를 state에 기록한다.
7. 중단/재개 또는 컨텍스트 이관 전:
   ```bash
   python3 ~/.claude/skills/release/scripts/service_factory.py handoff --project <project>
   ```
8. 사람/후속 에이전트가 볼 리뷰 표면 생성:
   ```bash
   python3 ~/.claude/skills/release/scripts/service_factory.py review-report --project <project>
   ```
9. Antigravity-like readiness 평가:
   ```bash
   python3 ~/.claude/skills/release/scripts/service_factory.py assess --project <project> --write-report
   ```
10. 최종 보고 전:
   ```bash
   python3 ~/.claude/skills/release/scripts/service_factory.py validate --project <project>
   ```

## Agent Foundry

기존 agent pool에 필요한 전문 역할이 없으면 Stella가 AgentBlueprint를 만들고, Release는 즉시 실행하지 않고 `missing_capabilities` 또는 `foundry.proposed_manifests`에 기록한다.

각 항목은 아래를 포함해야 한다.

- `agent_type`: 필요한 새 agent 이름
- `needed_for`: 필요한 stage
- `reason`: 기존 agent로 부족한 이유
- `proposed_manifest`: `~/.codex/agents/{agent_type}.toml` 후보 내용
- `suggested_action`: `create_agent_manifest`

Foundry는 자동 설치가 아니라 생성 제안 단계다. 새 agent manifest가 필요하면 `agent-installer` 또는 사용자 승인 흐름으로 분리한다.

## Runner와 Watchdog

`execution_plan`은 실제 실행자가 따라야 할 orchestration 계약이다.

| 필드 | 의미 |
|------|------|
| `agent_requests` | stage별 subagent 작업 요청과 prompt path |
| `worktree_isolation` | worktree/root와 one-writer 정책 |
| `parallel_groups` | 동시에 진행 가능한 stage 그룹과 동시 실행 한도 |
| `watchdog` | stale progress 감지 기준과 처리 |
| `handoff` | successor agent가 읽어야 할 필수 필드 |
| `automatic_gates` | project surface에서 감지한 build/test/typecheck/final validation 명령 |

`run`은 v0.3 runtime cycle이다. 현재 지원 backend:

- `manual`: launch instruction artifact를 만들고 request를 `blocked`로 남김
- `command`: `--agent-command-template`을 `argv[]`로 분해해 실행하고 stdout/stderr/tool event artifact를 남김. command가 `artifact_dir/result.json`을 쓰면 collector가 `done|blocked|validation_required|failed`를 state에 반영한다.
- `codex_bridge`: `dispatch`/`collect` 명령으로 실제 Codex subagent handoff와 result collection을 분리한다.
- `codex-exec`: `codex exec` 비대화형 CLI adapter. 모델 호출/비용이 생길 수 있으므로 `--allow-paid-agent-call` 없이는 실행하지 않고 `permission_blocked`로 기록한다.
- `dynamic_workflow` (260602 신설): Claude Code Workflow 도구의 `parallel()`/`pipeline()` fan-out으로 **stage 단위** 다중 request를 한 번에 처리. `dispatch-workflow` 명령이 `dispatch.workflow.js` + `dispatch.instructions.md`를 산출 → parent agent가 Workflow 도구로 실행 → 결과를 각 `artifact_dir/result.json`으로 직렬화 → 기존 `collect`로 흡수. `state.limits.max_parallel_agents`를 Workflow batch size로 강제, `WORKFLOW_RESULT_SCHEMA`로 StructuredOutput 강제. `service_factory_dynamic_workflow_backend.py` 분리 모듈.
- `resolve-validation`: 독립 리뷰 evidence를 요구해 `validation_required` request를 완료로 승격한다. evidence 파일이 존재할 때만 상태를 바꾼다.

보안 기본값:

- shell 실행 금지, `argv[]`만 사용
- 최소 env allowlist 사용, token/secret/cloud/SSH 관련 환경변수 제거
- DB/data deletion, destructive filesystem, production deploy, paid API expansion, external communication, offensive security 명령은 차단
- repo-controlled optional gates (`npm test`, `pytest`, `cargo test` 등)는 기본 skip, `--include-repo-gates`가 있을 때만 실행
- trusted final gate인 `service-factory-validate`는 기본 실행
- `codex-exec`는 `workspace-write`, `ask-for-approval never`, `skip-git-repo-check`로 실행되지만 Service Factory guard가 먼저 비용/위험 승인을 확인한다.

command backend smoke helper:

```bash
python3 ~/.claude/skills/release/scripts/service_factory.py run \
  --project <project> \
  --backend command \
  --agent-command-template "python3 ~/.claude/skills/release/scripts/service_factory_echo_agent.py --artifact-dir {artifact_dir} --request-id {request_id} --agent-type {agent_type}"
```

완전한 Antigravity runtime으로 가려면 다음 단계에서 이 command backend를 Codex/Antigravity/OpenHands SDK adapter로 교체하거나 병렬 spawn bridge를 붙여야 한다.

Codex bridge flow:

```bash
python3 ~/.claude/skills/release/scripts/service_factory.py dispatch --project <project> --max-requests 3
# parent Codex spawns subagents with each dispatch.md
python3 ~/.claude/skills/release/scripts/service_factory.py collect --project <project>
# if a child honestly returns validation_required, attach independent evidence
python3 ~/.claude/skills/release/scripts/service_factory.py resolve-validation --project <project> --request architecture::architect --evidence SOT/service-factory/runs/<run>/<request>/architecture-validation-review.md
```

이 흐름은 앱 내부 subagent 도구를 로컬 Python 스크립트가 직접 호출하지 못하는 제약을 우회한다. Python은 dispatch/result/gate state를 관리하고, parent Codex가 실제 subagent spawning을 담당한다.

## Antigravity-like Readiness

`assess`는 현재 구성이 Antigravity-like autonomous delivery에 얼마나 가까운지 점검한다.

평가 항목 (15 capabilities, 260603 갱신):

- `stella_command_owner` — Stella 가 command_owner 로 박혀 있는지
- `agent_topology` — blueprints / instances / kanban_role 정합
- `service_factory_state` — state 가 stages + approval gates 포함
- `state_plan_execute_contract` — current_state → development_plan → execution_verification 순서 무결
- `agent_runner_plan` — agent_requests 수와 results 수 비교
- `agent_foundry` — missing_capabilities 충족 여부
- `spawn_runtime` — execution_plan.mode 가 manual/command/codex_bridge/codex-exec/**dynamic_workflow** 중 어떤 백엔드인지 + agent_results 누적
- `worktree_isolation` — one-writer-per-owned-path 정책 활성
- `watchdog` — stale progress 감지 (15 분)
- `handoff_successor` — handoff_latest + 25 required fields
- `artifact_review_surface` — review-report.md 존재
- `automatic_gates` — service-factory-validate + results 누적
- `mandatory_verification_chain` — reviewer/critic/runtime_probe/security_auditor 결과
- `probe_required_for_completion` — probe agent result 가 verified 인지
- `recovery_proof` — recovery-report 와 recovered_requests 누적

판정 등급:
- `foundation_ready_but_not_autonomous` (score < 0.8 또는 spawn_runtime != ready)
- `pilot_ready` (score ≥ 0.8 AND spawn_runtime == ready AND primary_blocker 없음)

현재 v0.2의 기본 판정은 `foundation_ready_but_not_autonomous`다. `spawn_runtime`이 붙어 `agent_requests`를 실제 subagent/worktree 실행으로 연결해야 `pilot_ready`로 올라갈 수 있다.

260602 갱신: `dynamic_workflow` backend(`dispatch-workflow` 명령 + `service_factory_dynamic_workflow_backend.py`)가 이 빈 자리를 채운다. Claude Code Workflow 도구의 in-process `parallel()`/`pipeline()` fan-out을 stage 단위로 호출하므로 `agent_requests`가 실제 N-way 병렬 + `isolation:'worktree'` + `StructuredOutput` schema 강제로 실행된다. `assess`가 `spawn_runtime` 항목에서 이 backend가 등록된 것을 확인하면 `pilot_ready`로 승급 가능하다 (다른 항목 모두 충족 가정).

## 완료 정의

Service Factory가 `done`이 되려면 아래가 모두 충족되어야 한다.

- 모든 필수 stage가 `done`
- `validation_required` 또는 `in_progress` stage 없음
- 승인 필요 gate가 `pending`인 상태로 필요한 작업이 진행되지 않음
- 테스트/빌드/타입체크/Probe/보안 리뷰 중 적용 가능한 증거가 존재
- 남은 위험이 `known_issues`에 기록되고 출시 차단 여부가 분류됨
