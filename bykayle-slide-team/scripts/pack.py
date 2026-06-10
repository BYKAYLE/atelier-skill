#!/usr/bin/env python3
"""
pack.py — 수정된 XML 폴더를 다시 .pptx로 패키징한다.

Usage:
    python3 pack.py <unpacked_dir> <output.pptx>

Output:
    JSON으로 결과를 stdout에 출력
"""
import sys
import os
import json
import zipfile


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python3 pack.py <unpacked_dir> <output.pptx>"}))
        sys.exit(1)

    unpacked_dir = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.isdir(unpacked_dir):
        print(json.dumps({"error": f"Directory not found: {unpacked_dir}"}))
        sys.exit(1)

    if not output_path.lower().endswith('.pptx'):
        output_path += '.pptx'

    # 기존 파일이 있으면 백업
    if os.path.exists(output_path):
        backup_path = output_path + '.bak'
        os.rename(output_path, backup_path)
        print(json.dumps({"warning": f"Existing file backed up to: {backup_path}"}), file=sys.stderr)

    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            file_count = 0
            for root, dirs, files in os.walk(unpacked_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, unpacked_dir)

                    # .DS_Store 등 시스템 파일 제외 (.rels 파일은 유지)
                    if file.startswith('.') and not file.endswith('.rels'):
                        continue

                    # 미디어 파일은 압축하지 않음 (이미 압축된 형식)
                    media_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.wmf', '.emf'}
                    ext = os.path.splitext(file)[1].lower()
                    if ext in media_extensions:
                        zf.write(file_path, arcname, compress_type=zipfile.ZIP_STORED)
                    else:
                        zf.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)

                    file_count += 1

        file_size = os.path.getsize(output_path)

        result = {
            "success": True,
            "output_path": os.path.abspath(output_path),
            "file_count": file_count,
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 1)
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": f"Failed to create .pptx: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
