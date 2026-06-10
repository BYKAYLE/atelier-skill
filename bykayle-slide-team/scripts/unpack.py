#!/usr/bin/env python3
"""
unpack.py — .pptx 파일을 ZIP으로 해제하여 슬라이드 XML을 추출한다.

Usage:
    python3 unpack.py <input.pptx> [output_dir]

Output:
    JSON으로 해제된 파일 목록과 경로를 stdout에 출력
"""
import sys
import os
import json
import zipfile
import shutil


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 unpack.py <input.pptx> [output_dir]"}))
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(json.dumps({"error": f"File not found: {input_path}"}))
        sys.exit(1)

    if not input_path.lower().endswith('.pptx'):
        print(json.dumps({"error": "Input file must be a .pptx file"}))
        sys.exit(1)

    # 출력 디렉토리 결정
    if len(sys.argv) >= 3:
        output_dir = sys.argv[2]
    else:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.join(os.path.dirname(input_path), f"{base_name}_unpacked")

    # 기존 디렉토리가 있으면 제거
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    try:
        with zipfile.ZipFile(input_path, 'r') as zf:
            zf.extractall(output_dir)
            file_list = zf.namelist()
    except zipfile.BadZipFile:
        print(json.dumps({"error": "Invalid or corrupted .pptx file"}))
        sys.exit(1)

    # 파일 분류
    slides = [f for f in file_list if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
    layouts = [f for f in file_list if f.startswith('ppt/slideLayouts/')]
    masters = [f for f in file_list if f.startswith('ppt/slideMasters/')]
    themes = [f for f in file_list if f.startswith('ppt/theme/')]
    media = [f for f in file_list if f.startswith('ppt/media/')]
    notes = [f for f in file_list if f.startswith('ppt/notesSlides/')]

    result = {
        "success": True,
        "output_dir": os.path.abspath(output_dir),
        "total_files": len(file_list),
        "slides": sorted(slides),
        "slide_count": len(slides),
        "layouts": sorted(layouts),
        "masters": sorted(masters),
        "themes": themes,
        "media": media,
        "notes": sorted(notes),
        "presentation_xml": "ppt/presentation.xml" if "ppt/presentation.xml" in file_list else None,
        "content_types": "[Content_Types].xml" if "[Content_Types].xml" in file_list else None
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
