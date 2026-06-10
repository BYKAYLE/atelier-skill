#!/usr/bin/env python3
"""Stella bridge for Release Service Factory.

This wrapper keeps Stella's final-goal work tied to the Release Service
Factory state machine without deleting data or silently spending on model calls.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path.home() / ".claude" / "skills"
RELEASE_FACTORY = ROOT / "release" / "scripts" / "service_factory.py"


def state_path(project: Path) -> Path:
    return project / "SOT" / "service-factory-state.json"


def run_factory(args: list[str]) -> dict[str, Any]:
    cmd = ["python3", str(RELEASE_FACTORY), *args]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    payload: dict[str, Any] = {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }
    if proc.stdout.strip():
        try:
            payload["json"] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload["json"] = None
    return payload


def ensure_release_state(project: Path, goal: str, mode: str) -> dict[str, Any]:
    current_state = state_path(project)
    if not current_state.exists():
        return run_factory(["init", "--project", str(project), "--goal", goal, "--mode", mode])

    validation = run_factory(["validate", "--project", str(project), "--pretty"])
    if validation.get("returncode") == 0:
        return {
            "command": ["skip-init"],
            "returncode": 0,
            "stdout": f"valid state already exists: {current_state}",
            "stderr": "",
        }

    try:
        existing = json.loads(current_state.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        existing = {}
    schema = existing.get("schema_version") if isinstance(existing, dict) else None
    if schema == "atelier.stella-factory.v1":
        backup = current_state.with_name(
            f"{current_state.stem}.legacy-{datetime.now().strftime('%Y%m%d-%H%M%S')}{current_state.suffix}"
        )
        current_state.replace(backup)
        init = run_factory(["init", "--project", str(project), "--goal", goal, "--mode", mode])
        init["legacy_backup"] = str(backup)
        return init

    validation["returncode"] = validation.get("returncode") or 2
    validation["stderr"] = (
        (validation.get("stderr") or "")
        + f"\nexisting state is invalid and not a trusted Atelier bootstrap schema: {current_state}"
    ).strip()
    return validation


def print_result(result: dict[str, Any], pretty: bool) -> int:
    print(json.dumps(result, ensure_ascii=False, indent=2 if pretty else None))
    failures = [step for step in result.get("steps", []) if step.get("returncode", 0) != 0]
    return 1 if failures else 0


def command_bootstrap(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser()
    project.mkdir(parents=True, exist_ok=True)
    (project / "SOT").mkdir(parents=True, exist_ok=True)
    current_state = state_path(project)

    steps: list[dict[str, Any]] = []
    init_step = ensure_release_state(project, args.goal, args.mode)
    steps.append(init_step)
    if init_step.get("returncode") != 0:
        result = {
            "bridge": "stella_service_factory",
            "action": "bootstrap",
            "project": str(project),
            "state": str(current_state),
            "goal": args.goal,
            "steps": steps,
        }
        return print_result(result, args.pretty)

    steps.append(run_factory(["plan", "--project", str(project), "--pretty"]))
    if not args.no_dispatch:
        steps.append(run_factory(["dispatch", "--project", str(project), "--max-requests", str(args.max_requests), "--pretty"]))
    steps.append(run_factory(["validate", "--project", str(project), "--pretty"]))
    steps.append(run_factory(["review-report", "--project", str(project), "--pretty"]))
    steps.append(run_factory(["assess", "--project", str(project), "--write-report", "--pretty"]))

    result = {
        "bridge": "stella_service_factory",
        "action": "bootstrap",
        "project": str(project),
        "state": str(current_state),
        "goal": args.goal,
        "next_action": "spawn Codex subagents from dispatch files, then run collect",
        "steps": steps,
    }
    return print_result(result, args.pretty)


def command_status(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser()
    steps = [
        run_factory(["status", "--project", str(project), "--pretty"]),
        run_factory(["validate", "--project", str(project), "--pretty"]),
        run_factory(["review-report", "--project", str(project), "--pretty"]),
        run_factory(["assess", "--project", str(project), "--write-report", "--pretty"]),
    ]
    result = {
        "bridge": "stella_service_factory",
        "action": "status",
        "project": str(project),
        "state": str(state_path(project)),
        "steps": steps,
    }
    return print_result(result, args.pretty)


def command_dispatch(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser()
    steps = [
        run_factory(["dispatch", "--project", str(project), "--max-requests", str(args.max_requests), "--pretty"]),
        run_factory(["validate", "--project", str(project), "--pretty"]),
        run_factory(["review-report", "--project", str(project), "--pretty"]),
        run_factory(["assess", "--project", str(project), "--write-report", "--pretty"]),
    ]
    result = {
        "bridge": "stella_service_factory",
        "action": "dispatch",
        "project": str(project),
        "state": str(state_path(project)),
        "next_action": "spawn Codex subagents from dispatch files, then run collect",
        "steps": steps,
    }
    return print_result(result, args.pretty)


def command_collect(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser()
    collect_args = ["collect", "--project", str(project), "--pretty"]
    if args.request:
        collect_args.extend(["--request", args.request])
    if args.run_id:
        collect_args.extend(["--run-id", args.run_id])
    if args.include_repo_gates:
        collect_args.append("--include-repo-gates")
    steps = [
        run_factory(collect_args),
        run_factory(["validate", "--project", str(project), "--pretty"]),
        run_factory(["review-report", "--project", str(project), "--pretty"]),
        run_factory(["assess", "--project", str(project), "--write-report", "--pretty"]),
    ]
    result = {
        "bridge": "stella_service_factory",
        "action": "collect",
        "project": str(project),
        "state": str(state_path(project)),
        "steps": steps,
    }
    return print_result(result, args.pretty)


def command_autopilot(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser()
    project.mkdir(parents=True, exist_ok=True)
    (project / "SOT").mkdir(parents=True, exist_ok=True)
    current_state = state_path(project)

    steps: list[dict[str, Any]] = []
    init_step = ensure_release_state(project, args.goal, args.mode)
    steps.append(init_step)
    if init_step.get("returncode") != 0:
        result = {
            "bridge": "stella_service_factory",
            "action": "autopilot",
            "project": str(project),
            "state": str(current_state),
            "goal": args.goal,
            "steps": steps,
        }
        return print_result(result, args.pretty)
    steps.append(run_factory(["plan", "--project", str(project), "--pretty"]))
    steps.append(
        run_factory(
            [
                "autopilot",
                "--project",
                str(project),
                "--goal",
                args.goal,
                "--mode",
                args.mode,
                "--max-cycles",
                str(args.max_cycles),
                "--max-requests",
                str(args.max_requests),
                "--timeout-seconds",
                str(args.timeout_seconds),
                "--pretty",
            ]
        )
    )
    steps.append(run_factory(["validate", "--project", str(project), "--pretty"]))
    steps.append(run_factory(["review-report", "--project", str(project), "--pretty"]))
    steps.append(run_factory(["recovery-report", "--project", str(project), "--pretty"]))
    steps.append(run_factory(["assess", "--project", str(project), "--write-report", "--pretty"]))

    result = {
        "bridge": "stella_service_factory",
        "action": "autopilot",
        "project": str(project),
        "state": str(current_state),
        "goal": args.goal,
        "steps": steps,
    }
    return print_result(result, args.pretty)


def command_resolve_validation(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser()
    resolve_args = ["resolve-validation", "--project", str(project), "--request", args.request, "--pretty"]
    for evidence in args.evidence:
        resolve_args.extend(["--evidence", evidence])
    if args.note:
        resolve_args.extend(["--note", args.note])
    if args.force:
        resolve_args.append("--force")
    steps = [
        run_factory(resolve_args),
        run_factory(["validate", "--project", str(project), "--pretty"]),
        run_factory(["review-report", "--project", str(project), "--pretty"]),
        run_factory(["assess", "--project", str(project), "--write-report", "--pretty"]),
    ]
    result = {
        "bridge": "stella_service_factory",
        "action": "resolve-validation",
        "project": str(project),
        "state": str(state_path(project)),
        "steps": steps,
    }
    return print_result(result, args.pretty)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stella bridge for Release Service Factory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap", help="init/plan/dispatch/assess a Service Factory project")
    bootstrap.add_argument("--project", required=True)
    bootstrap.add_argument("--goal", required=True)
    bootstrap.add_argument("--mode", default="local-staging", choices=["repo-only", "local-staging", "production-candidate"])
    bootstrap.add_argument("--max-requests", type=int, default=3)
    bootstrap.add_argument("--no-dispatch", action="store_true")
    bootstrap.add_argument("--pretty", action="store_true")
    bootstrap.set_defaults(func=command_bootstrap)

    status = subparsers.add_parser("status", help="show status/validate/assess")
    status.add_argument("--project", required=True)
    status.add_argument("--pretty", action="store_true")
    status.set_defaults(func=command_status)

    dispatch = subparsers.add_parser("dispatch", help="create next dispatch packets")
    dispatch.add_argument("--project", required=True)
    dispatch.add_argument("--max-requests", type=int, default=3)
    dispatch.add_argument("--pretty", action="store_true")
    dispatch.set_defaults(func=command_dispatch)

    collect = subparsers.add_parser("collect", help="collect result.json artifacts")
    collect.add_argument("--project", required=True)
    collect.add_argument("--request")
    collect.add_argument("--run-id")
    collect.add_argument("--include-repo-gates", action="store_true")
    collect.add_argument("--pretty", action="store_true")
    collect.set_defaults(func=command_collect)

    autopilot = subparsers.add_parser("autopilot", help="run managed Service Factory cycles until pilot_ready or a concrete blocker")
    autopilot.add_argument("--project", required=True)
    autopilot.add_argument("--goal", required=True)
    autopilot.add_argument("--mode", default="local-staging", choices=["repo-only", "local-staging", "production-candidate"])
    autopilot.add_argument("--max-cycles", type=int, default=12)
    autopilot.add_argument("--max-requests", type=int, default=1)
    autopilot.add_argument("--timeout-seconds", type=int, default=900)
    autopilot.add_argument("--pretty", action="store_true")
    autopilot.set_defaults(func=command_autopilot)

    resolve_validation = subparsers.add_parser("resolve-validation", help="resolve validation_required request with evidence")
    resolve_validation.add_argument("--project", required=True)
    resolve_validation.add_argument("--request", required=True)
    resolve_validation.add_argument("--evidence", action="append", required=True)
    resolve_validation.add_argument("--note")
    resolve_validation.add_argument("--force", action="store_true")
    resolve_validation.add_argument("--pretty", action="store_true")
    resolve_validation.set_defaults(func=command_resolve_validation)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
