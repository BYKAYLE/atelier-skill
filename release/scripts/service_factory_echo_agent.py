#!/usr/bin/env python3
"""Small command-backend smoke helper for Service Factory tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a Service Factory result.json")
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--agent-type", required=True)
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "done",
        "modified_files": [],
        "commands_run": [],
        "artifacts": [],
        "findings_or_risks": [],
        "next_step": f"{args.request_id} completed by {args.agent_type}",
    }
    (artifact_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
