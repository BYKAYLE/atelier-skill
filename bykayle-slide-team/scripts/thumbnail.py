#!/usr/bin/env python3
"""
thumbnail.py — .pptx 슬라이드의 텍스트 기반 썸네일 그리드를 생성한다.

Usage:
    python3 thumbnail.py <input.pptx> [--cols 3] [--width 40]

Output:
    각 슬라이드의 레이아웃 구조를 ASCII 박스로 시각화하여 stdout에 출력.
    Pencil MCP 없이도 슬라이드 구성을 빠르게 확인할 수 있다.
"""
import sys
import os
import json
import argparse
import zipfile
import xml.etree.ElementTree as ET

NSMAP = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

# 16:9 슬라이드 기준 EMU
SLIDE_W_EMU = 12192000
SLIDE_H_EMU = 6858000


def tag(ns, local):
    return '{%s}%s' % (NSMAP[ns], local)


def extract_text(sp_elem):
    """sp 요소에서 텍스트 추출."""
    texts = []
    for t_elem in sp_elem.iter(tag('a', 't')):
        if t_elem.text:
            texts.append(t_elem.text)
    return ' '.join(texts).strip()


def get_shape_type(sp_elem):
    """shape의 placeholder 타입 또는 일반 타입 반환."""
    nvSpPr = sp_elem.find(tag('p', 'nvSpPr'))
    if nvSpPr is None:
        return 'shape'

    nvPr = nvSpPr.find(tag('p', 'nvPr'))
    if nvPr is not None:
        ph = nvPr.find(tag('p', 'ph'))
        if ph is not None:
            ph_type = ph.get('type', 'body')
            return ph_type

    return 'textbox'


def get_shape_position(sp_elem):
    """shape의 위치/크기 (EMU) 반환."""
    spPr = sp_elem.find(tag('p', 'spPr'))
    if spPr is None:
        return None

    xfrm = spPr.find(tag('a', 'xfrm'))
    if xfrm is None:
        return None

    off = xfrm.find(tag('a', 'off'))
    ext = xfrm.find(tag('a', 'ext'))
    if off is None or ext is None:
        return None

    return {
        'x': int(off.get('x', 0)),
        'y': int(off.get('y', 0)),
        'w': int(ext.get('cx', 0)),
        'h': int(ext.get('cy', 0)),
    }


def parse_slide_xml(xml_content):
    """슬라이드 XML에서 shape 정보 추출."""
    root = ET.fromstring(xml_content)
    shapes = []

    for sp in root.iter(tag('p', 'sp')):
        shape_type = get_shape_type(sp)
        text = extract_text(sp)
        pos = get_shape_position(sp)
        if pos and (text or shape_type in ('pic', 'chart', 'tbl', 'media', 'dgm')):
            shapes.append({
                'type': shape_type,
                'text': text[:30] if text else '',
                'pos': pos,
            })

    # 이미지 (p:pic)
    for pic in root.iter(tag('p', 'pic')):
        spPr = pic.find(tag('p', 'spPr'))
        if spPr is not None:
            xfrm = spPr.find(tag('a', 'xfrm'))
            if xfrm is not None:
                off = xfrm.find(tag('a', 'off'))
                ext = xfrm.find(tag('a', 'ext'))
                if off is not None and ext is not None:
                    shapes.append({
                        'type': 'image',
                        'text': '[IMG]',
                        'pos': {
                            'x': int(off.get('x', 0)),
                            'y': int(off.get('y', 0)),
                            'w': int(ext.get('cx', 0)),
                            'h': int(ext.get('cy', 0)),
                        }
                    })

    return shapes


def render_thumbnail(shapes, width=40, height=15):
    """shapes 리스트를 ASCII 그리드로 렌더링."""
    # 빈 캔버스
    canvas = [[' ' for _ in range(width)] for _ in range(height)]

    # 테두리
    for x in range(width):
        canvas[0][x] = '─'
        canvas[height - 1][x] = '─'
    for y in range(height):
        canvas[y][0] = '│'
        canvas[y][width - 1] = '│'
    canvas[0][0] = '┌'
    canvas[0][width - 1] = '┐'
    canvas[height - 1][0] = '└'
    canvas[height - 1][width - 1] = '┘'

    # 타입별 표시 문자
    type_chars = {
        'ctrTitle': 'T',
        'title': 'T',
        'subTitle': 'S',
        'body': 'B',
        'pic': 'I',
        'image': 'I',
        'chart': 'C',
        'tbl': '#',
        'media': 'M',
        'dgm': 'D',
        'textbox': 't',
        'shape': '.',
        'ftr': 'f',
        'dt': 'd',
        'sldNum': 'n',
    }

    for shape in shapes:
        pos = shape['pos']
        st = shape['type']
        text = shape['text']

        # EMU → 캔버스 좌표 변환
        cx = max(1, min(width - 2, int(pos['x'] / SLIDE_W_EMU * (width - 2)) + 1))
        cy = max(1, min(height - 2, int(pos['y'] / SLIDE_H_EMU * (height - 2)) + 1))
        cw = max(1, int(pos['w'] / SLIDE_W_EMU * (width - 2)))
        ch = max(1, int(pos['h'] / SLIDE_H_EMU * (height - 2)))

        char = type_chars.get(st, '?')

        # 영역 표시
        for dy in range(ch):
            for dx in range(cw):
                ny = cy + dy
                nx = cx + dx
                if 1 <= ny < height - 1 and 1 <= nx < width - 1:
                    if dy == 0 and dx == 0:
                        canvas[ny][nx] = char
                    elif dy == 0 and dx < len(text) + 1 and dx > 0:
                        if dx - 1 < len(text):
                            canvas[ny][nx] = text[dx - 1]
                    elif canvas[ny][nx] == ' ':
                        canvas[ny][nx] = '·'

    return '\n'.join(''.join(row) for row in canvas)


def get_slide_order(pptx_path):
    """presentation.xml에서 슬라이드 순서 추출."""
    with zipfile.ZipFile(pptx_path, 'r') as zf:
        if 'ppt/presentation.xml' not in zf.namelist():
            return []

        pres_xml = zf.read('ppt/presentation.xml')
        root = ET.fromstring(pres_xml)

        ns_p = NSMAP['p']
        ns_r = NSMAP['r']

        sldIdLst = root.find('{%s}sldIdLst' % ns_p)
        if sldIdLst is None:
            return []

        rIds = []
        for sldId in sldIdLst:
            rId = sldId.get('{%s}id' % ns_r)
            if rId:
                rIds.append(rId)

        # presentation.xml.rels에서 rId → 파일명 매핑
        rels_path = 'ppt/_rels/presentation.xml.rels'
        if rels_path not in zf.namelist():
            return []

        rels_xml = zf.read(rels_path)
        rels_root = ET.fromstring(rels_xml)
        rId_to_file = {}
        for rel in rels_root:
            rid = rel.get('Id')
            target = rel.get('Target')
            if rid and target:
                rId_to_file[rid] = target

        ordered = []
        for rId in rIds:
            target = rId_to_file.get(rId)
            if target:
                # "slides/slide1.xml" → "ppt/slides/slide1.xml"
                if not target.startswith('ppt/'):
                    target = 'ppt/' + target
                ordered.append(target)

        return ordered


def main():
    parser = argparse.ArgumentParser(description='슬라이드 ASCII 썸네일 생성')
    parser.add_argument('input', help='.pptx 파일 경로')
    parser.add_argument('--cols', type=int, default=3, help='열 수 (기본: 3)')
    parser.add_argument('--width', type=int, default=40, help='썸네일 너비 (기본: 40)')
    parser.add_argument('--height', type=int, default=15, help='썸네일 높이 (기본: 15)')
    parser.add_argument('--json', action='store_true', help='JSON 형식으로 출력')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(json.dumps({'error': f'File not found: {args.input}'}))
        sys.exit(1)

    slide_order = get_slide_order(args.input)

    with zipfile.ZipFile(args.input, 'r') as zf:
        slide_files = slide_order if slide_order else sorted(
            [n for n in zf.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')],
            key=lambda x: int(''.join(filter(str.isdigit, x.split('/')[-1])) or '0')
        )

        thumbnails = []
        for sf in slide_files:
            try:
                xml_content = zf.read(sf)
                shapes = parse_slide_xml(xml_content)
                thumb = render_thumbnail(shapes, args.width, args.height)
                slide_num = ''.join(filter(str.isdigit, sf.split('/')[-1]))
                thumbnails.append({
                    'slide': int(slide_num),
                    'file': sf,
                    'shape_count': len(shapes),
                    'types': list(set(s['type'] for s in shapes)),
                    'thumbnail': thumb,
                })
            except Exception as e:
                thumbnails.append({
                    'slide': sf,
                    'error': str(e),
                })

    if args.json:
        print(json.dumps({
            'success': True,
            'total_slides': len(thumbnails),
            'thumbnails': thumbnails,
        }, ensure_ascii=False, indent=2))
    else:
        # 그리드 출력
        cols = args.cols
        for i in range(0, len(thumbnails), cols):
            group = thumbnails[i:i + cols]

            # 슬라이드 번호 헤더
            headers = []
            for t in group:
                if 'error' in t:
                    headers.append(f"  Slide {t['slide']} (ERROR)")
                else:
                    types_str = ','.join(t['types'][:3])
                    headers.append(f"  Slide {t['slide']} [{types_str}]")
            header_line = '  '.join(h.ljust(args.width) for h in headers)
            print(header_line)

            # 썸네일 행 병합
            thumb_lines = []
            for t in group:
                if 'error' in t:
                    lines = [f"  ERROR: {t['error'][:args.width - 4]}"]
                    lines += [''] * (args.height - 1)
                else:
                    lines = t['thumbnail'].split('\n')
                thumb_lines.append(lines)

            max_lines = max(len(tl) for tl in thumb_lines)
            for line_idx in range(max_lines):
                row_parts = []
                for tl in thumb_lines:
                    if line_idx < len(tl):
                        row_parts.append(tl[line_idx].ljust(args.width))
                    else:
                        row_parts.append(' ' * args.width)
                print('  '.join(row_parts))

            print()  # 행 사이 간격

        # 범례
        print('Legend: T=Title, S=Subtitle, B=Body, I=Image, C=Chart, #=Table, M=Media, t=TextBox')
        print(f'Total: {len(thumbnails)} slides')


if __name__ == '__main__':
    main()
