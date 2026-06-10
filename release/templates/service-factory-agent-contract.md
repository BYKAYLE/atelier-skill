# Service Factory Agent Contract

이 계약은 Release가 Worker/Reviewer/Auditor 에이전트에게 일을 줄 때 prompt에 붙인다.

## 공통 금지선

- DB 삭제, 데이터 삭제, destructive migration, volume 삭제 금지
- 프로덕션 배포, 외부 발화, 유료 API 사용 확대 금지
- 침투 테스트, 공격성 스캔, exploit 검증은 명시 scope와 승인 없이는 금지
- 다른 에이전트가 소유한 파일을 임의로 되돌리거나 덮어쓰기 금지

## Worker 계약

Worker는 구현 담당이다.

필수 입력:
- goal
- 담당 stage
- 소유 파일/디렉터리
- 금지 파일/표면
- 성공 기준
- 실행해야 할 검증 명령

필수 출력:
```json
{
  "agent_role": "worker",
  "stage": "parallel_implementation",
  "status": "done|blocked|validation_required",
  "modified_files": [],
  "commands_run": [
    {"cmd": "npm test", "exit_code": 0}
  ],
  "artifacts": [],
  "handoff_notes": "",
  "risks": []
}
```

## Reviewer 계약

Reviewer는 Worker 산출물을 독립 검토한다.

필수 확인:
- 구현이 요청 목표와 맞는가
- 테스트가 실제 코드를 검증하는가
- mock/hardcode로 통과한 false-green이 없는가
- 회귀 위험 파일이 빠지지 않았는가
- 완료 보고와 실제 diff가 일치하는가

필수 출력:
```json
{
  "agent_role": "reviewer",
  "stage": "verification",
  "status": "pass|fail|blocked",
  "findings": [],
  "required_fixes": [],
  "evidence": []
}
```

## Auditor 계약

Auditor는 보안, 런타임, 컴플라이언스, 운영 리스크를 검토한다.

필수 확인:
- 인증/인가, secrets, input validation, dependency risk
- Probe runtime/UI/API report 또는 적용 불가 사유
- CRITICAL/HIGH 보안 이슈가 남았는지
- 승인 게이트가 자동 통과되지 않았는지

필수 출력:
```json
{
  "agent_role": "auditor",
  "stage": "security_review",
  "status": "pass|fail|blocked",
  "critical": 0,
  "high": 0,
  "evidence": [],
  "exceptions": []
}
```

## Integrator 계약

Integrator는 여러 Worker 결과를 하나의 제품 상태로 합친다.

필수 확인:
- 파일 충돌과 중복 구현 해소
- API/UI/DB/배포 계약 연결
- 전체 빌드/테스트 흐름 재실행
- 후속 Reviewer/Auditor가 볼 artifact 정리

필수 출력:
```json
{
  "agent_role": "integrator",
  "stage": "integration",
  "status": "done|blocked|validation_required",
  "merged_surfaces": [],
  "commands_run": [],
  "artifacts": [],
  "handoff_notes": ""
}
```
