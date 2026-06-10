#!/usr/bin/env python3
"""orch-scanner: 오케스트레이터 스킬 구조 스캔 + 갭 리포트 생성

Usage:
    python3 orch-scanner.py <skill_path>
    python3 orch-scanner.py ~/.claude/skills/release/

Output: JSON gap-report to stdout
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path


def scan_skill_md(skill_path: Path) -> dict:
    """SKILL.md를 파싱하여 Phase 정보와 참조 파일 목록을 추출한다."""
    skill_md = skill_path / "SKILL.md"
    result = {
        "exists": skill_md.exists(),
        "phases": [],
        "referenced_files": [],
        "line_count": 0,
        "has_frontmatter": False,
        "has_self_improvement": False,
        "has_quality_gates": False,
    }

    if not skill_md.exists():
        return result

    content = skill_md.read_text(encoding="utf-8")
    lines = content.split("\n")
    result["line_count"] = len(lines)

    # Frontmatter check
    if content.startswith("---"):
        result["has_frontmatter"] = True

    # Phase extraction - match "Phase N", "Phase A", "Step N" patterns
    phase_pattern = re.compile(
        r"#{2,4}\s+(?:Phase\s+(\w+)|Step\s+(\d+))\s*[—:]\s*(.*)",
        re.IGNORECASE,
    )
    for line in lines:
        m = phase_pattern.match(line.strip())
        if m:
            phase_id = m.group(1) or m.group(2)
            phase_name = m.group(3).strip()
            result["phases"].append({"id": phase_id, "name": phase_name})

    # Referenced files extraction (exclude template placeholders like {timestamp})
    ref_pattern = re.compile(r"`(?:references|SOT|scripts)/([^`]+)`")
    for match in ref_pattern.finditer(content):
        ref_path = match.group(0).strip("`")
        # Skip template placeholders
        if "{" in ref_path and "}" in ref_path:
            continue
        result["referenced_files"].append(ref_path)

    # Self-improvement check
    si_keywords = ["self-improve", "자가 개선", "자가 성장", "self-growth", "자가성장"]
    result["has_self_improvement"] = any(kw in content.lower() for kw in si_keywords)

    # Quality gates check
    qg_keywords = ["quality gate", "품질 게이트", "qc", "quality check"]
    result["has_quality_gates"] = any(kw in content.lower() for kw in qg_keywords)

    return result


def scan_references(skill_path: Path) -> dict:
    """references/ 디렉토리를 스캔한다."""
    refs_dir = skill_path / "references"
    result = {
        "exists": refs_dir.exists(),
        "files": [],
        "total_size_kb": 0,
    }

    if not refs_dir.exists():
        return result

    for f in sorted(refs_dir.rglob("*")):
        if f.is_file():
            size_kb = round(f.stat().st_size / 1024, 1)
            result["files"].append({"name": str(f.relative_to(refs_dir)), "size_kb": size_kb})
            result["total_size_kb"] += size_kb

    result["total_size_kb"] = round(result["total_size_kb"], 1)
    return result


def scan_sot(skill_path: Path) -> dict:
    """SOT/ 디렉토리를 스캔하여 활성도를 평가한다."""
    sot_dir = skill_path / "SOT"
    result = {
        "exists": sot_dir.exists(),
        "files": [],
        "empty_files": [],
        "empty_dirs": [],
        "session_count": 0,
        "last_modified": None,
        "meta_rules_stats": None,
        "performance_stats": None,
    }

    if not sot_dir.exists():
        return result

    for f in sorted(sot_dir.rglob("*")):
        if f.is_file():
            size_kb = round(f.stat().st_size / 1024, 1)
            mtime = datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            rel_path = str(f.relative_to(sot_dir))
            result["files"].append({"name": rel_path, "size_kb": size_kb, "modified": mtime})

            if size_kb == 0:
                result["empty_files"].append(rel_path)

            # Track last modified
            if result["last_modified"] is None or mtime > result["last_modified"]:
                result["last_modified"] = mtime

    # Empty directories
    for d in sorted(sot_dir.rglob("*")):
        if d.is_dir() and not any(d.iterdir()):
            result["empty_dirs"].append(str(d.relative_to(sot_dir)))

    # Session count
    sessions_dir = sot_dir / "sessions"
    if sessions_dir.exists():
        result["session_count"] = len([f for f in sessions_dir.iterdir() if f.is_file()])

    # Meta-rules analysis
    meta_rules = sot_dir / "meta-rules.md"
    if meta_rules.exists():
        content = meta_rules.read_text(encoding="utf-8")
        # Match MR-NNN patterns in table rows
        rules = re.findall(r"MR-\d{3}", content)
        # Deduplicate (same rule may appear multiple times)
        unique_rules = list(set(rules))
        # Check for self-detected origin markers
        self_detected = len(re.findall(r"자가\s*감지|self.detect|자동\s*감지|자가\s*발견", content, re.IGNORECASE))
        usage_zero = len(re.findall(r"Usage:\s*0", content))
        # Check source distribution: "사용자 피드백" vs "자가 감지"
        user_feedback_count = len(re.findall(r"사용자\s*(?:피드백|교정|지적)|User\s*feedback", content, re.IGNORECASE))
        result["meta_rules_stats"] = {
            "total_rules": len(unique_rules),
            "self_detected": self_detected,
            "user_feedback_based": user_feedback_count,
            "usage_zero_count": usage_zero,
        }

    # Performance analysis
    performance = sot_dir / "performance.md"
    if performance.exists():
        content = performance.read_text(encoding="utf-8")
        total_match = re.search(r"total_sessions:\s*(\d+)", content)
        last_analysis_match = re.search(r"last_analysis_at:\s*(\d+)", content)
        result["performance_stats"] = {
            "total_sessions": int(total_match.group(1)) if total_match else 0,
            "last_analysis_at": int(last_analysis_match.group(1)) if last_analysis_match else 0,
        }

    return result


def scan_scripts(skill_path: Path) -> dict:
    """scripts/ 디렉토리를 스캔한다."""
    scripts_dir = skill_path / "scripts"
    result = {"exists": scripts_dir.exists(), "files": []}

    if not scripts_dir.exists():
        return result

    for f in sorted(scripts_dir.rglob("*")):
        if f.is_file():
            result["files"].append(str(f.relative_to(scripts_dir)))

    return result


def check_cross_references(skill_md_data: dict, refs_data: dict, sot_data: dict, skill_path: Path) -> list:
    """SKILL.md에서 참조하는 파일이 실제로 존재하는지 검증한다."""
    missing = []
    ref_files = {f["name"] for f in refs_data.get("files", [])}
    sot_files = {f["name"] for f in sot_data.get("files", [])}

    seen = set()
    for ref in skill_md_data.get("referenced_files", []):
        if ref in seen:
            continue
        seen.add(ref)

        # Check if the actual path exists (file or directory)
        actual_path = skill_path / ref
        if actual_path.exists():
            continue

        # For directory-style references (ending with /), check directory
        if ref.endswith("/"):
            dir_path = skill_path / ref.rstrip("/")
            if dir_path.exists() and dir_path.is_dir():
                continue

        # Check as relative path within references/ or SOT/
        if ref.startswith("references/"):
            check_name = ref.replace("references/", "")
            if check_name not in ref_files:
                missing.append(ref)
        elif ref.startswith("SOT/"):
            check_name = ref.replace("SOT/", "")
            if check_name not in sot_files:
                # Also check if it's a directory
                sot_dir_path = skill_path / "SOT" / check_name.rstrip("/")
                if not sot_dir_path.exists():
                    missing.append(ref)

    return missing


def generate_gaps(skill_path: Path, skill_md: dict, refs: dict, sot: dict, scripts: dict, missing_refs: list) -> list:
    """갭 목록을 생성한다."""
    gaps = []
    gap_id = 0

    def add_gap(severity, category, title, evidence, location):
        nonlocal gap_id
        gap_id += 1
        gaps.append({
            "id": f"GAP-{gap_id:03d}",
            "severity": severity,
            "category": category,
            "title": title,
            "evidence": evidence,
            "location": location,
        })

    # 1. SKILL.md missing
    if not skill_md["exists"]:
        add_gap("CRITICAL", "structure", "SKILL.md 없음", "SKILL.md 파일이 존재하지 않음", str(skill_path))
        return gaps

    # 2. No frontmatter
    if not skill_md["has_frontmatter"]:
        add_gap("HIGH", "structure", "Frontmatter 누락", "SKILL.md에 ---frontmatter--- 없음", "SKILL.md")

    # 3. No phases defined
    if len(skill_md["phases"]) == 0:
        add_gap("HIGH", "structure", "Phase 정의 없음", "SKILL.md에 Phase/Step 정의가 없음", "SKILL.md")

    # 4. No references directory
    if not refs["exists"]:
        add_gap("MEDIUM", "structure", "references/ 디렉토리 없음", "참조 문서 디렉토리 미생성", str(skill_path))

    # 5. No SOT directory
    if not sot["exists"]:
        add_gap("HIGH", "structure", "SOT/ 디렉토리 없음", "SOT 디렉토리 미생성", str(skill_path))

    # 6. Empty SOT files
    for f in sot.get("empty_files", []):
        add_gap("MEDIUM", "sot-health", f"빈 SOT 파일: {f}", "파일 크기 0KB — 초기화만 되고 데이터 없음", f"SOT/{f}")

    # 7. Empty SOT directories
    for d in sot.get("empty_dirs", []):
        add_gap("HIGH", "sot-health", f"빈 SOT 디렉토리: {d}", "디렉토리는 있으나 파일이 하나도 없음", f"SOT/{d}")

    # 8. Missing cross-references
    for ref in missing_refs:
        add_gap("HIGH", "cross-reference", f"참조 파일 누락: {ref}", "SKILL.md에서 참조하지만 실제 파일 없음", ref)

    # 9. Self-improvement not designed
    if not skill_md["has_self_improvement"]:
        add_gap("MEDIUM", "self-growth", "자가 성장 설계 없음", "SKILL.md에 자가 개선/성장 관련 Phase 없음", "SKILL.md")

    # 10. Meta-rules: all from user feedback
    if sot.get("meta_rules_stats"):
        stats = sot["meta_rules_stats"]
        if stats["total_rules"] > 0 and stats["self_detected"] == 0:
            add_gap(
                "CRITICAL",
                "self-growth",
                "자가 감지 규칙 0건",
                f"{stats['total_rules']}개 meta-rules 중 자가 감지 0건 — 전부 사용자 피드백 기반",
                "SOT/meta-rules.md",
            )

    # 11. Meta-rules: high usage:0 ratio
    if sot.get("meta_rules_stats"):
        stats = sot["meta_rules_stats"]
        if stats["total_rules"] > 5 and stats["usage_zero_count"] > stats["total_rules"] * 0.7:
            add_gap(
                "HIGH",
                "self-growth",
                "Meta-rules Usage 추적 미작동",
                f"{stats['total_rules']}개 중 {stats['usage_zero_count']}개가 Usage:0",
                "SOT/meta-rules.md",
            )

    # 12. Session count vs performance mismatch
    if sot.get("performance_stats") and sot["session_count"] > 0:
        perf = sot["performance_stats"]
        if perf["total_sessions"] > 0 and sot["session_count"] < perf["total_sessions"] * 0.5:
            add_gap(
                "HIGH",
                "record-keeping",
                "세션 로그 누락",
                f"performance.md 기록 {perf['total_sessions']}세션 vs 실제 로그 {sot['session_count']}개",
                "SOT/sessions/",
            )

    # 13. Analysis overdue
    if sot.get("performance_stats"):
        perf = sot["performance_stats"]
        if perf["total_sessions"] - perf["last_analysis_at"] >= 5:
            add_gap(
                "MEDIUM",
                "self-growth",
                "전체 분석 지연",
                f"마지막 분석: {perf['last_analysis_at']}세션, 현재: {perf['total_sessions']}세션 — 5세션 주기 초과",
                "SOT/performance.md",
            )

    # 14. Quality gates not defined
    if not skill_md["has_quality_gates"]:
        add_gap("MEDIUM", "quality", "품질 게이트 미설계", "SKILL.md에 QC/품질 게이트 관련 내용 없음", "SKILL.md")

    return gaps


def calculate_health_score(gaps: list) -> int:
    """갭 기반 건강도 점수 계산 (100점 만점)."""
    score = 100
    for gap in gaps:
        if gap["severity"] == "CRITICAL":
            score -= 15
        elif gap["severity"] == "HIGH":
            score -= 10
        elif gap["severity"] == "MEDIUM":
            score -= 5
    return max(0, score)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 orch-scanner.py <skill_path>"}), file=sys.stderr)
        sys.exit(1)

    skill_path = Path(os.path.expanduser(sys.argv[1])).resolve()

    if not skill_path.exists():
        print(json.dumps({"error": f"Path not found: {skill_path}"}), file=sys.stderr)
        sys.exit(1)

    # Scan all components
    skill_md_data = scan_skill_md(skill_path)
    refs_data = scan_references(skill_path)
    sot_data = scan_sot(skill_path)
    scripts_data = scan_scripts(skill_path)
    missing_refs = check_cross_references(skill_md_data, refs_data, sot_data, skill_path)

    # Generate gaps
    gaps = generate_gaps(skill_path, skill_md_data, refs_data, sot_data, scripts_data, missing_refs)

    # Calculate health score
    health_score = calculate_health_score(gaps)

    # Severity counts
    severity_counts = {"critical": 0, "high": 0, "medium": 0}
    for gap in gaps:
        key = gap["severity"].lower()
        if key in severity_counts:
            severity_counts[key] += 1

    # Build report
    report = {
        "mode": "diagnose",
        "target": str(skill_path),
        "scan_time": datetime.now().isoformat(),
        "summary": {
            "total_gaps": len(gaps),
            **severity_counts,
        },
        "health_score": health_score,
        "structure": {
            "skill_md": {
                "exists": skill_md_data["exists"],
                "line_count": skill_md_data["line_count"],
                "phase_count": len(skill_md_data["phases"]),
                "phases": skill_md_data["phases"],
                "has_frontmatter": skill_md_data["has_frontmatter"],
                "has_self_improvement": skill_md_data["has_self_improvement"],
                "has_quality_gates": skill_md_data["has_quality_gates"],
            },
            "references": {
                "exists": refs_data["exists"],
                "file_count": len(refs_data.get("files", [])),
                "total_size_kb": refs_data.get("total_size_kb", 0),
            },
            "sot": {
                "exists": sot_data["exists"],
                "file_count": len(sot_data.get("files", [])),
                "session_count": sot_data.get("session_count", 0),
                "empty_files": sot_data.get("empty_files", []),
                "empty_dirs": sot_data.get("empty_dirs", []),
                "meta_rules_stats": sot_data.get("meta_rules_stats"),
                "performance_stats": sot_data.get("performance_stats"),
            },
            "scripts": {
                "exists": scripts_data["exists"],
                "file_count": len(scripts_data.get("files", [])),
            },
        },
        "gaps": gaps,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
