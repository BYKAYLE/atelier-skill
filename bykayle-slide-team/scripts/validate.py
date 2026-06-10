#!/usr/bin/env python3
"""
validate.py — 생성된 .pptx 파일의 무결성을 검증한다.

Usage:
    python3 validate.py <file.pptx>

Output:
    JSON으로 검증 결과를 stdout에 출력
"""
import sys
import os
import json
import zipfile
import xml.etree.ElementTree as ET


NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
}


def validate_zip_structure(pptx_path):
    """ZIP 구조 검증"""
    errors = []
    warnings = []

    try:
        with zipfile.ZipFile(pptx_path, 'r') as zf:
            file_list = zf.namelist()

            # 필수 파일 확인
            required_files = [
                '[Content_Types].xml',
                '_rels/.rels',
                'ppt/presentation.xml',
            ]
            for rf in required_files:
                if rf not in file_list:
                    errors.append(f"Missing required file: {rf}")

            # 슬라이드 존재 확인
            slides = [f for f in file_list if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
            if not slides:
                errors.append("No slides found in ppt/slides/")

            # 테마 확인
            themes = [f for f in file_list if f.startswith('ppt/theme/')]
            if not themes:
                warnings.append("No theme file found")

            # 손상된 파일 확인
            bad_files = zf.testzip()
            if bad_files:
                errors.append(f"Corrupted file in archive: {bad_files}")

            return {
                "valid": len(errors) == 0,
                "file_count": len(file_list),
                "slide_count": len(slides),
                "errors": errors,
                "warnings": warnings
            }

    except zipfile.BadZipFile:
        return {
            "valid": False,
            "errors": ["File is not a valid ZIP/PPTX archive"],
            "warnings": []
        }


def validate_xml_wellformedness(pptx_path):
    """모든 XML 파일의 문법적 올바름을 검증"""
    errors = []

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        xml_files = [f for f in zf.namelist() if f.endswith('.xml') or f.endswith('.rels')]
        for xml_file in xml_files:
            try:
                content = zf.read(xml_file)
                ET.fromstring(content)
            except ET.ParseError as e:
                errors.append(f"XML parse error in {xml_file}: {str(e)}")

    return {
        "valid": len(errors) == 0,
        "xml_files_checked": len(xml_files) if 'xml_files' in dir() else 0,
        "errors": errors
    }


def validate_relationships(pptx_path):
    """relationship 참조 무결성 검증"""
    errors = []
    warnings = []

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        file_list = set(zf.namelist())

        # .rels 파일들에서 참조 확인
        rels_files = [f for f in file_list if f.endswith('.rels')]
        for rels_file in rels_files:
            try:
                content = zf.read(rels_file)
                root = ET.fromstring(content)

                rels_dir = os.path.dirname(rels_file)
                # _rels 폴더의 상위가 기준 디렉토리
                if rels_dir.endswith('_rels'):
                    base_dir = os.path.dirname(rels_dir)
                else:
                    base_dir = rels_dir

                for rel in root.findall('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                    target = rel.get('Target', '')
                    rel_type = rel.get('Type', '')

                    # 외부 URL은 스킵
                    if target.startswith('http://') or target.startswith('https://'):
                        continue
                    if rel.get('TargetMode') == 'External':
                        continue

                    # 상대 경로를 절대 경로로 변환
                    if target.startswith('/'):
                        resolved = target[1:]  # 루트 기준
                    else:
                        resolved = os.path.normpath(os.path.join(base_dir, target))
                        resolved = resolved.replace('\\', '/')

                    if resolved not in file_list:
                        # 일부 관계는 선택적일 수 있음
                        if 'thumbnail' in rel_type.lower() or 'extended-properties' in rel_type.lower():
                            warnings.append(f"Optional target missing: {resolved} (from {rels_file})")
                        else:
                            errors.append(f"Broken relationship: {resolved} (from {rels_file})")

            except ET.ParseError:
                errors.append(f"Cannot parse relationship file: {rels_file}")

    return {
        "valid": len(errors) == 0,
        "rels_checked": len(rels_files) if 'rels_files' in dir() else 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_content_types(pptx_path):
    """[Content_Types].xml 검증"""
    errors = []

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        if '[Content_Types].xml' not in zf.namelist():
            return {"valid": False, "errors": ["[Content_Types].xml not found"]}

        content = zf.read('[Content_Types].xml')
        try:
            root = ET.fromstring(content)

            # 슬라이드에 대한 Override 확인
            overrides = {}
            for override in root.findall('{http://schemas.openxmlformats.org/package/2006/content-types}Override'):
                part_name = override.get('PartName', '')
                content_type = override.get('ContentType', '')
                overrides[part_name] = content_type

            # 모든 슬라이드에 대한 Content-Type 확인
            slides = [f for f in zf.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
            for slide in slides:
                part_name = '/' + slide
                if part_name not in overrides:
                    errors.append(f"Missing Content-Type for {slide}")

        except ET.ParseError as e:
            errors.append(f"Cannot parse [Content_Types].xml: {str(e)}")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def validate_anti_patterns(pptx_path):
    """OOXML 안티패턴 검사"""
    warnings = []

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        slide_files = [f for f in zf.namelist()
                       if f.startswith('ppt/slides/slide') and f.endswith('.xml')]

        for sf in slide_files:
            content = zf.read(sf).decode('utf-8', errors='replace')

            # 안티패턴 1: 색상에 # prefix
            if '"#' in content and ('srgbClr' in content or 'solidFill' in content):
                # 더 정확한 검사
                import re
                hash_colors = re.findall(r'val="(#[0-9A-Fa-f]{6})"', content)
                if hash_colors:
                    warnings.append(f"{sf}: Color values with '#' prefix found: {hash_colors[:3]}")

            # 안티패턴 2: 빈 <a:r> 요소
            if '<a:r/>' in content or '<a:r></a:r>' in content:
                warnings.append(f"{sf}: Empty <a:r> elements found")

            # 안티패턴 3: Unicode bullet (실제 문자 대신 <a:buChar> 사용해야 함)
            try:
                root = ET.fromstring(content.encode('utf-8'))
                for t_elem in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
                    if t_elem.text and t_elem.text.strip().startswith('•'):
                        warnings.append(f"{sf}: Unicode bullet '•' in text — use <a:buChar> instead")
                        break
            except ET.ParseError:
                pass

    return {
        "clean": len(warnings) == 0,
        "warnings": warnings
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 validate.py <file.pptx>"}))
        sys.exit(1)

    pptx_path = sys.argv[1]
    if not os.path.exists(pptx_path):
        print(json.dumps({"error": f"File not found: {pptx_path}"}))
        sys.exit(1)

    results = {
        "file": os.path.abspath(pptx_path),
        "file_size_kb": round(os.path.getsize(pptx_path) / 1024, 1),
        "checks": {}
    }

    # 1. ZIP 구조 검증
    results["checks"]["zip_structure"] = validate_zip_structure(pptx_path)

    # ZIP이 유효하지 않으면 나머지 검사 중단
    if not results["checks"]["zip_structure"]["valid"]:
        results["overall"] = "FAIL"
        results["summary"] = "File is not a valid PPTX archive"
        print(json.dumps(results, indent=2, ensure_ascii=False))
        sys.exit(1)

    # 2. XML 문법 검증
    results["checks"]["xml_wellformedness"] = validate_xml_wellformedness(pptx_path)

    # 3. Relationship 참조 검증
    results["checks"]["relationships"] = validate_relationships(pptx_path)

    # 4. Content-Type 검증
    results["checks"]["content_types"] = validate_content_types(pptx_path)

    # 5. 안티패턴 검사
    results["checks"]["anti_patterns"] = validate_anti_patterns(pptx_path)

    # 종합 판정
    all_valid = all(
        check.get("valid", check.get("clean", True))
        for check in results["checks"].values()
    )

    total_errors = sum(
        len(check.get("errors", []))
        for check in results["checks"].values()
    )

    total_warnings = sum(
        len(check.get("warnings", []))
        for check in results["checks"].values()
    )

    if all_valid and total_warnings == 0:
        results["overall"] = "PASS"
        results["summary"] = "All checks passed"
    elif all_valid:
        results["overall"] = "WARNING"
        results["summary"] = f"Valid but {total_warnings} warning(s) found"
    else:
        results["overall"] = "FAIL"
        results["summary"] = f"{total_errors} error(s), {total_warnings} warning(s)"

    print(json.dumps(results, indent=2, ensure_ascii=False))

    # 실패 시 exit code 1
    if results["overall"] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
