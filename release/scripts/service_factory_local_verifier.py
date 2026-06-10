#!/usr/bin/env python3
"""Local no-cost verifier for Service Factory command backend smoke runs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def run_command(argv: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(argv, cwd=str(cwd), text=True, capture_output=True, check=False)
    return {
        "argv": argv,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def semantic_failures(command_results: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for result in command_results:
        argv = [str(item) for item in result.get("argv", [])]
        if "assess" not in argv or result.get("returncode") != 0:
            continue
        try:
            assessment = json.loads(str(result.get("stdout") or "{}"))
        except json.JSONDecodeError:
            failures.append("assess output was not valid JSON")
            continue
        if assessment.get("primary_blocker") and assessment.get("verdict") == "pilot_ready":
            failures.append("readiness verdict is pilot_ready while primary_blocker is still present")
        if not any(
            item.get("id") == "mandatory_verification_chain"
            for item in assessment.get("capabilities", [])
            if isinstance(item, dict)
        ):
            failures.append("readiness assessment is missing mandatory_verification_chain capability")
    return failures


def handoff_failures(project: Path) -> list[str]:
    handoff_path = project / "SOT" / "service-factory" / "handoff-latest.md"
    if not handoff_path.exists():
        return ["handoff-latest.md is missing"]
    text = handoff_path.read_text(encoding="utf-8")
    match = re.search(r"## Handoff Contract\s+```json\s+(.*?)\s+```", text, re.DOTALL)
    if not match:
        return ["handoff-latest.md is missing the Handoff Contract JSON block"]
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return ["handoff-latest.md Handoff Contract block is not valid JSON"]
    required_fields = [
        "factory_id",
        "request_id",
        "run_id",
        "stage",
        "current_owner",
        "successor_role",
        "status",
        "backend",
        "last_command",
        "last_artifact",
        "failure_category",
        "blocked_reason",
        "next_step",
        "owned_paths",
        "pending_artifacts",
        "approval_gate_snapshot",
        "mandatory_requests_remaining",
        "retry_count",
        "respawn_eligible",
        "lease_owner",
        "lease_expires_at",
        "resume_command",
        "completion_claim_guard",
    ]
    missing = [field for field in required_fields if field not in payload]
    failures: list[str] = []
    if missing:
        failures.append(f"handoff contract missing required fields: {', '.join(missing)}")
    if not isinstance(payload.get("approval_gate_snapshot"), list):
        failures.append("handoff approval_gate_snapshot must be a list")
    if not isinstance(payload.get("mandatory_requests_remaining"), list):
        failures.append("handoff mandatory_requests_remaining must be a list")
    if not payload.get("resume_command"):
        failures.append("handoff resume_command is empty")
    guard = payload.get("completion_claim_guard")
    if not isinstance(guard, dict):
        failures.append("handoff completion_claim_guard must be an object")
    else:
        if guard.get("probe_required") is not True:
            failures.append("handoff completion_claim_guard.probe_required must be true")
        if payload.get("status") == "completed" and guard.get("completion_claim_allowed") is not True:
            failures.append("handoff claims completion without completion_claim_allowed=true")
    return failures


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run a local Service Factory verifier and write result.json")
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--agent-type", required=True)
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args(argv[1:])

    artifact_dir = Path(args.artifact_dir).expanduser()
    project = Path(args.project).expanduser()
    state_file = Path(args.state_file).expanduser()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    service_factory = Path(__file__).resolve().parent / "service_factory.py"

    commands = [
        [sys.executable, str(service_factory), "validate", "--state", str(state_file), "--pretty"],
        [sys.executable, str(service_factory), "status", "--state", str(state_file), "--pretty"],
        [sys.executable, str(service_factory), "assess", "--state", str(state_file), "--write-report", "--pretty"],
    ]
    command_results = [run_command(command, project) for command in commands]
    report_path = artifact_dir / "local-verifier-report.md"
    report = [
        "# Service Factory Local Verifier Report",
        "",
        f"generated_at: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"request_id: {args.request_id}",
        f"agent_type: {args.agent_type}",
        f"state_file: {state_file}",
        "",
        "## Commands",
    ]
    for result in command_results:
        report.append("")
        report.append(f"- command: `{' '.join(result['argv'])}`")
        report.append(f"  - returncode: {result['returncode']}")
        if result["stderr"]:
            report.append(f"  - stderr: `{result['stderr'][:500]}`")
    failures = [result for result in command_results if result["returncode"] != 0]
    semantic_issues = semantic_failures(command_results) + handoff_failures(project)
    report.extend(
        [
            "",
            "## Judgment",
            "PASS" if not failures and not semantic_issues else "VALIDATION REQUIRED",
        ]
    )
    if semantic_issues:
        report.extend(["", "## Semantic Issues"])
        report.extend(f"- {issue}" for issue in semantic_issues)
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    result_path = artifact_dir / "result.json"
    payload = {
        "status": "done" if not failures and not semantic_issues else "validation_required",
        "modified_files": [],
        "commands_run": command_results,
        "artifacts": [str(report_path)],
        "findings_or_risks": [
            "Local verifier proves command backend can execute a managed no-cost verification cycle.",
            "It does not replace LLM subagent spawning; it is runtime evidence for managed command execution.",
            *semantic_issues,
        ],
        "failure_category": None if not failures and not semantic_issues else "test_failed",
        "next_step": "continue with independent reviewer, security, runtime probe, deployment readiness, and final audit",
    }
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(result_path), "status": payload["status"]}, ensure_ascii=False))
    return 0 if not failures and not semantic_issues else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
