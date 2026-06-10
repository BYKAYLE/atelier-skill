#!/usr/bin/env python3
"""
프로젝트 SOT 구조를 초기화하는 스크립트.
사용법: python3 init_project.py <project-name> --path <output-directory>
"""

import argparse
import os
from datetime import datetime


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {os.path.relpath(path, start=os.path.dirname(path))}")


def init_project(project_name, output_path):
    base = os.path.join(output_path, project_name)
    now = datetime.now().strftime("%Y-%m-%d")

    print(f"\n🚀 프로젝트 초기화: {project_name}")
    print(f"   경로: {base}\n")

    # SOT 구조
    create_file(os.path.join(base, "SOT", "L1-project-summary.md"), f"""# {project_name} — 프로젝트 요약

## 한줄 설명
[TODO: 이 프로젝트가 무엇인지 한 문장으로]

## 현재 상태
- Phase: Phase 0 (초기화)
- 버전: v0.1
- 마지막 작업일: {now}

## 핵심 기능 (구현 완료)
(아직 없음)

## 기술 스택
(Phase 1에서 결정)

## 파일 구조 요약
(Phase 1에서 설계)

## 미해결 이슈
(없음)

## 다음 작업 예정
- Phase 1: 기획 진행
""")

    create_file(os.path.join(base, "SOT", "changelog.md"), f"""# 변경 이력

## {now} — 프로젝트 초기화
- Phase: 0
- 내용: SOT 구조 생성, 프로젝트 시작
""")

    create_file(os.path.join(base, "SOT", "decisions.md"), """# 자율 판단 기록

이 문서에는 AI가 자율적으로 내린 판단과 그 이유를 기록한다.

(아직 없음)
""")

    create_file(os.path.join(base, "SOT", "issues.md"), """# 발견된 문제 및 미해결 이슈

(아직 없음)
""")

    # L2 features 디렉토리
    os.makedirs(os.path.join(base, "SOT", "L2-features"), exist_ok=True)
    print("  ✅ L2-features/")

    # sessions 디렉토리
    create_file(os.path.join(base, "SOT", "sessions", ".gitkeep"), "")
    print("  ✅ sessions/")

    # CLAUDE.md
    create_file(os.path.join(base, "CLAUDE.md"), f"""# {project_name} — 실행 규칙

## 코딩 규칙
- 모든 파일은 UTF-8 인코딩
- HTML/CSS/JS는 단일 파일로 통합 (별도 분리하지 않음)
- 외부 라이브러리는 CDN으로 로드
- 주석은 한국어로 작성

## 네이밍 규칙
- 파일명: kebab-case (예: user-profile.html)
- CSS 클래스: kebab-case
- JavaScript 변수/함수: camelCase

## 금지 사항
- localStorage, sessionStorage 사용 금지 (Cowork 환경 제약)
- 인라인 스타일 최소화

## 프로젝트 특수 규칙
(Phase 1 이후 추가)

## 학습된 규칙 (자기 개선 루프에서 추가됨)
(사용하면서 자동 추가됨)
""")

    # src 디렉토리
    os.makedirs(os.path.join(base, "src"), exist_ok=True)
    print("  ✅ src/")

    # output 디렉토리
    os.makedirs(os.path.join(base, "output"), exist_ok=True)
    print("  ✅ output/")

    print(f"\n✅ 프로젝트 '{project_name}' 초기화 완료!")
    print(f"   SOT 경로: {os.path.join(base, 'SOT')}")
    print(f"   규칙 파일: {os.path.join(base, 'CLAUDE.md')}")
    print(f"\n   다음 단계: Phase 1 기획 진행")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="프로젝트 SOT 구조 초기화")
    parser.add_argument("project_name", help="프로젝트 이름")
    parser.add_argument("--path", default=".", help="출력 디렉토리 (기본: 현재 경로)")
    args = parser.parse_args()

    init_project(args.project_name, args.path)
