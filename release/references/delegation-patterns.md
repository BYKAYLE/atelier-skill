# Delegation Patterns — release

## Agent 호출 규칙
모든 Agent: `subagent_type="general-purpose"`. Model: opus(3+파일,아키텍처) / sonnet(단일기능) / haiku(비개발,단순).

## Base Template
```
You are a task executor under release.
## Step 1: Load Skill → Call Skill("{skill_name}")
## Step 2: Execute → {task_description}
## Success Criteria → {criteria_list}
## Playbook Procedures → {playbook_procedures_if_any}
## Constraints → {constraints_if_any}
## When Complete → Report: 변경 파일, 검증 결과(명령어+exit code), 미해결 이슈, 요약 2-3줄
```

## Retry Template (Retry 1)
Base + 추가: `## Previous Attempt Failed: {error_message}, {gate_name}. Fix the error — do NOT start over.`

## Retry Template (Retry 2 — 진단 우선)
Base + 추가: `## Previous Failures: {error1}, {error2}. DIAGNOSE root cause BEFORE fixing.`

## Replacement Template (스킬 교체)
Base + 추가: `## Previous skill ({previous_skill}) failed twice. Context: {error_summary}. Take a DIFFERENT approach.`

## Pipeline Step Template
Base + 추가:
```
Step {N}/{total}. Project: {path}.
Previous artifacts: {artifact_paths}.
All output under {project_path}/. Do NOT exceed your scope.
추가 보고: 다음 Step에 전달할 핵심 정보.
```

## Non-Dev Template
Base와 동일. 단 `No build/test/lint gates. Focus on deliverable quality.`
보고: 산출물 목록(경로), 완성도 자체평가(1-5).

## Absorption-Enhanced Template
Base + 추가:
```
Project Context: Goal={goal}, Deliverable={deliverable}, Scale={scale}, Quality={criteria}.
Autonomous Decision Authority: {decisions}. Risk Areas: {risks}.
```

## 병렬 에이전트 규칙
- 겹치지 않는 파일 범위 명시. 공유 리소스 읽기 전용. 완료 후 교차 정합성 검증.

## 다중 스킬 순차 위임
각 스킬 별도 Agent (컨텍스트 격리). 산출물 파일로 전달. QG 개별 실행. 실패 시 해당 스킬만 재시도.
