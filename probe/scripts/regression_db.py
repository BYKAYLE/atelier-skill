"""Cross-run regression fingerprint database.

Stores findings across runs at `~/.claude/skills/probe/regressions.json`
keyed by target origin. Each finding has a stable fingerprint (url route +
kind + normalised message) so the same bug reappearing in a later run is
flagged "recurrence" and previously-seen-but-now-absent bugs become "closed".

Schema:
    {
      "https://myapp.com": {
        "754a91526fb1": {
          "kind": "axe_critical",
          "route": "/",
          "message": "Form elements must have labels (6 nodes)",
          "first_seen": "2026-04-21T02:04:26",
          "last_seen":  "2026-04-21T15:00:00",
          "run_count":  4,
          "status":     "open"   // open | closed
        },
        ...
      }
    }
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DB_PATH = Path.home() / ".claude" / "skills" / "probe" / "regressions.json"


def _origin(url: str) -> str:
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        return url
    return f"{p.scheme}://{p.netloc}"


def _load() -> dict[str, Any]:
    if not DB_PATH.exists():
        return {}
    try:
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(db: dict[str, Any]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def tag_and_persist(target: str, findings: list[Any]) -> dict[str, Any]:
    """Compare this run's findings against prior state for the same origin.

    Mutates each finding's `details['regression_status']` to one of:
        "new"         — never seen before
        "recurrence"  — previously seen (still open or newly re-opened)

    Finally persists updated state. Returns a summary dict.
    """
    origin = _origin(target)
    now = datetime.now().isoformat(timespec="seconds")

    db = _load()
    bucket = db.get(origin, {})

    seen_this_run: set[str] = set()
    new_count = 0
    recur_count = 0

    for f in findings:
        fp = f.fingerprint
        if not fp:
            continue
        seen_this_run.add(fp)
        route = urlparse(f.url).path or "/"
        entry = bucket.get(fp)
        if entry is None:
            bucket[fp] = {
                "kind": f.kind,
                "route": route,
                "message": f.message[:300],
                "first_seen": now,
                "last_seen": now,
                "run_count": 1,
                "status": "open",
            }
            f.details.setdefault("regression_status", "new")
            new_count += 1
        else:
            entry["last_seen"] = now
            entry["run_count"] = int(entry.get("run_count", 0)) + 1
            previously_closed = entry.get("status") == "closed"
            entry["status"] = "open"
            f.details.setdefault(
                "regression_status",
                "recurrence" if previously_closed else "recurrence",
            )
            recur_count += 1

    # Anything in bucket not seen this run and currently "open" becomes closed
    closed_now: list[dict[str, Any]] = []
    for fp, entry in list(bucket.items()):
        if fp in seen_this_run:
            continue
        if entry.get("status") == "open":
            entry["status"] = "closed"
            entry["closed_at"] = now
            closed_now.append({"fingerprint": fp, **entry})

    db[origin] = bucket
    _save(db)

    return {
        "origin": origin,
        "new": new_count,
        "recurrence": recur_count,
        "closed_this_run": len(closed_now),
        "closed_items": closed_now[:20],  # cap for report
        "db_path": str(DB_PATH),
    }
