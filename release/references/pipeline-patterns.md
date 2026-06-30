# Pipeline Patterns — release

## 생성 규칙
1. 모든 파이프라인은 QC 스텝으로 종료 (최소 Tier 2)
2. 개발 스텝은 Tier 1 게이트 필수 (빌드/테스트/타입/린트)
3. 모든 스텝에 fallback 지정 (registry.md 참조)
4. 병렬 스텝은 데이터 의존성 없어야 함
5. 산출물은 반드시 파일로 저장

## pipeline-state.json
```json
{ "pipeline_id": "auto-{ts}", "pattern": "{name}", "goal": "{goal}",
  "steps": [{ "step": 0, "skill": "", "purpose": "", "model": "",
    "depends_on": [], "success_criteria": [], "fallback": "",
    "agent_status": "pending|running|completed|failed", "retries": 0,
    "artifacts": [] }],
  "status": "running|completed|failed|interrupted", "resume_count": 0 }
```

## Full Service Build (development-new, 200K~400K tokens)
```
0: Market Research (notebooklm) [optional] → QG Tier 2
1: PRD (show-me-the-prd) → QG Tier 2.5 (4파일)
2a: Design (autonomous-dev S-Phase 0~1.7) → 3+ 방향, release 자율 선택
2b: Development (autonomous-dev S-Phase 2+) → QG Tier 1
3: Hardening (sisyphus_claude) → Release Loop
4: Security-Static (security-router) → CRITICAL=0, HIGH=0
5: Deploy (private-deployment-skill) → HTTP 200 + Running
6: Security-Runtime-Smoke (Probe) + Legal (오케스트레이터) [병렬]
   ※ 침투/공격성 테스트는 사용자 명시 승인 + scope 기록 시에만 pentest-router 별도 실행
```

## Service Factory Build (product-ready multi-agent delivery)
사용자이 "최종 제품까지", "Google처럼", "많은 에이전트가 개발/검증/디버깅까지"를 요청하면 Full Service Build보다 이 패턴을 우선한다.

```
0: Factory Init
   → python3 ~/.claude/skills/release/scripts/service_factory.py init --project <project> --goal "<goal>"
0.5: Runner Plan + Foundry
   → python3 ~/.claude/skills/release/scripts/service_factory.py plan --project <project>
   → agent_requests, prompts, missing_capabilities, foundry proposed manifests, watchdog, handoff, automatic_gates
1: Intake + Contract
   → Stella intent, forbidden actions, acceptance criteria, approval gates
2: Staffing + File Leases
   → Worker/Reviewer/Critic/Auditor 분리, 같은 파일 write owner 1명
3: Product Brief + Architecture + Repo Map
   → PRD/architecture/code map artifacts
4: Parallel Implementation
   → surface별 Worker. 각 Worker는 commands_run + artifacts + modified_files 보고
5: Integration
   → 단일 Integrator가 충돌 정리. 전체 build/test 재실행
6: Independent Verification
   → Reviewer + Probe. 자기검토만 있으면 validation_required
7: Critic Challenge
   → false-green, mock-only, missing rollback, edge cases 공격
8: Security + Policy Audit
   → security-router + Probe runtime security smoke. pentest는 명시 승인 시 별도
9: Deployment Readiness
   → staging smoke 또는 생략 이유, rollback plan
10: Final Audit
   → service_factory.py review-report + service_factory.py validate + evidence bundle + known issues
```

상태 파일: `{project}/SOT/service-factory-state.json`
참조: `references/service-factory.md`, `templates/service-factory-agent-contract.md`

## Feature Addition (development-existing, 50K~150K)
```
0: Codebase Analysis (sisyphus-workflow) → 변경 범위 결정
1: Implementation (sisyphus-workflow/autonomous-dev) → QG Tier 1
2: Regression Check [optional] → 전체 테스트 PASS
```

## Research → Presentation (50K~100K)
```
0: Research (notebooklm) → QG Tier 2.5
   ※ 심층 연구 필요 시 private-rd-orchestrator에 협조 요청 (peer 오케스트레이터, release 하위 아님)
1: Slides (bykayle-slide-team) → QG Tier 2.5
```

## Dev → Security (80K~200K)
```
0: Development → QG Tier 1
1: Security (security-router) → CRITICAL=0. 발견 시 Step 0에 수정 위임
```

## Design → Dev (100K~250K)
```
0: Design Guide (ui-ux-pro-max) → QG Tier 2.5
1: Implementation → QG Tier 1
```

## Security Audit (30K~80K)
```
0: Scan (security-router + Probe runtime smoke) → 보고서
   ※ pentest-router는 명시 승인된 침투 테스트 요청에서만 추가
1: Fix [CRITICAL 있을 때만] → Tier 1 + CRITICAL=0
```

## Deep Research (100K~300K)
```
※ private-rd-orchestrator은 peer 오케스트레이터 — release가 위임하지 않음. Stella 또는 사용자이 직접 호출.
※ release 파이프라인에서 연구 필요 시: notebooklm 또는 k-dense-ai 사용, 심층 R&D는 private-rd-orchestrator에 협조 요청.
0: Research (k-dense-ai/notebooklm) → QG Tier 2.5
1: Synthesis [optional] → 종합+시각화
```

## Deployment (30K~60K)
```
0: Deploy (private-deployment-skill 8Phase) → HTTP 200 + Running
```

## 동적 생성 (패턴 없을 때)
흡수 문서에서 스킬 추출 → registry.md 의존성 확인 → 순서 배치 → 독립 스텝 병렬 → QG+fallback 지정
