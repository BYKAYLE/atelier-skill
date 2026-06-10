#!/usr/bin/env python3
"""
parse_template.py — 해제된 .pptx의 슬라이드 레이아웃과 placeholder를 분석한다.

Usage:
    python3 parse_template.py <unpacked_dir>

Output:
    template-schema.md 형식의 JSON을 stdout에 출력
"""
import sys
import os
import json
import xml.etree.ElementTree as ET


# OOXML 네임스페이스
NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
    'dgm': 'http://schemas.openxmlformats.org/drawingml/2006/diagram',
}


def parse_theme(theme_path):
    """테마 파일에서 색상 팔레트와 폰트를 추출한다."""
    if not os.path.exists(theme_path):
        return {"colors": {}, "fonts": {}}

    tree = ET.parse(theme_path)
    root = tree.getroot()

    colors = {}
    color_scheme = root.find('.//a:clrScheme', NS)
    if color_scheme is not None:
        for color_name in ['dk1', 'lt1', 'dk2', 'lt2',
                           'accent1', 'accent2', 'accent3', 'accent4',
                           'accent5', 'accent6', 'hlink', 'folHlink']:
            elem = color_scheme.find(f'a:{color_name}', NS)
            if elem is not None:
                srgb = elem.find('a:srgbClr', NS)
                sys_clr = elem.find('a:sysClr', NS)
                if srgb is not None:
                    colors[color_name] = srgb.get('val', '')
                elif sys_clr is not None:
                    colors[color_name] = sys_clr.get('lastClr', '')

    fonts = {}
    font_scheme = root.find('.//a:fontScheme', NS)
    if font_scheme is not None:
        for font_type in ['majorFont', 'minorFont']:
            font_elem = font_scheme.find(f'a:{font_type}', NS)
            if font_elem is not None:
                latin = font_elem.find('a:latin', NS)
                ea = font_elem.find('a:ea', NS)
                fonts[font_type] = {
                    'latin': latin.get('typeface', '') if latin is not None else '',
                    'ea': ea.get('typeface', '') if ea is not None else ''
                }

    return {"colors": colors, "fonts": fonts}


def parse_placeholder(sp_elem):
    """도형 요소에서 placeholder 정보를 추출한다."""
    nv_sp_pr = sp_elem.find('p:nvSpPr', NS)
    if nv_sp_pr is None:
        return None

    nv_pr = nv_sp_pr.find('p:nvPr', NS)
    if nv_pr is None:
        return None

    ph = nv_pr.find('p:ph', NS)
    if ph is None:
        return None

    ph_type = ph.get('type', 'body')
    ph_idx = ph.get('idx', '0')

    # 위치 정보
    sp_pr = sp_elem.find('p:spPr', NS)
    position = {}
    if sp_pr is not None:
        xfrm = sp_pr.find('a:xfrm', NS)
        if xfrm is not None:
            off = xfrm.find('a:off', NS)
            ext = xfrm.find('a:ext', NS)
            if off is not None:
                position['left_emu'] = int(off.get('x', 0))
                position['top_emu'] = int(off.get('y', 0))
            if ext is not None:
                position['width_emu'] = int(ext.get('cx', 0))
                position['height_emu'] = int(ext.get('cy', 0))

    # 텍스트 추출
    text_parts = []
    tx_body = sp_elem.find('p:txBody', NS)
    if tx_body is not None:
        for p in tx_body.findall('a:p', NS):
            for r in p.findall('a:r', NS):
                t = r.find('a:t', NS)
                if t is not None and t.text:
                    text_parts.append(t.text)

    return {
        "idx": ph_idx,
        "type": ph_type,
        "position": position,
        "text": ''.join(text_parts) if text_parts else ''
    }


def parse_slide(slide_path):
    """슬라이드 XML에서 도형, placeholder, 애니메이션 정보를 추출한다."""
    tree = ET.parse(slide_path)
    root = tree.getroot()

    placeholders = []
    shapes = []
    special_elements = []

    # 도형 탐색
    sp_tree = root.find('.//p:cSld/p:spTree', NS)
    if sp_tree is not None:
        for sp in sp_tree.findall('p:sp', NS):
            ph_info = parse_placeholder(sp)
            if ph_info:
                placeholders.append(ph_info)

            # shape id
            nv_sp_pr = sp.find('p:nvSpPr/p:cNvPr', NS)
            if nv_sp_pr is not None:
                shapes.append({
                    "id": nv_sp_pr.get('id', ''),
                    "name": nv_sp_pr.get('name', ''),
                    "is_placeholder": ph_info is not None
                })

        # 그룹 도형
        for grp_sp in sp_tree.findall('p:grpSp', NS):
            special_elements.append({"type": "grouped_shape"})

        # 이미지
        for pic in sp_tree.findall('p:pic', NS):
            special_elements.append({"type": "picture"})

    # 애니메이션 확인
    timing = root.find('.//p:timing', NS)
    has_animation = timing is not None

    # 전환 효과
    transition = root.find('.//p:transition', NS)
    has_transition = transition is not None

    return {
        "placeholders": placeholders,
        "shapes": shapes,
        "special_elements": special_elements,
        "has_animation": has_animation,
        "has_transition": has_transition
    }


def parse_layout(layout_path):
    """레이아웃 XML에서 이름과 placeholder 구조를 추출한다."""
    tree = ET.parse(layout_path)
    root = tree.getroot()

    # 레이아웃 이름
    cSld = root.find('p:cSld', NS)
    layout_name = cSld.get('name', 'Unknown') if cSld is not None else 'Unknown'

    # 레이아웃 타입
    layout_type = root.get('type', 'custom')

    placeholders = []
    sp_tree = root.find('.//p:cSld/p:spTree', NS)
    if sp_tree is not None:
        for sp in sp_tree.findall('p:sp', NS):
            ph_info = parse_placeholder(sp)
            if ph_info:
                placeholders.append(ph_info)

    return {
        "name": layout_name,
        "type": layout_type,
        "placeholders": placeholders
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 parse_template.py <unpacked_dir>"}))
        sys.exit(1)

    unpacked_dir = sys.argv[1]
    if not os.path.isdir(unpacked_dir):
        print(json.dumps({"error": f"Directory not found: {unpacked_dir}"}))
        sys.exit(1)

    result = {
        "template_info": {
            "unpacked_dir": os.path.abspath(unpacked_dir)
        },
        "theme": {},
        "layouts": [],
        "slides": []
    }

    # 테마 분석
    theme_path = os.path.join(unpacked_dir, 'ppt', 'theme', 'theme1.xml')
    result["theme"] = parse_theme(theme_path)

    # 레이아웃 분석
    layouts_dir = os.path.join(unpacked_dir, 'ppt', 'slideLayouts')
    if os.path.isdir(layouts_dir):
        layout_files = sorted([
            f for f in os.listdir(layouts_dir)
            if f.startswith('slideLayout') and f.endswith('.xml')
        ])
        for i, lf in enumerate(layout_files):
            layout_path = os.path.join(layouts_dir, lf)
            try:
                layout_info = parse_layout(layout_path)
                layout_info["id"] = f"layout_{i + 1}"
                layout_info["file"] = lf
                result["layouts"].append(layout_info)
            except ET.ParseError as e:
                print(json.dumps({"warning": f"Failed to parse {lf}: {str(e)}"}), file=sys.stderr)

    # 슬라이드 분석
    slides_dir = os.path.join(unpacked_dir, 'ppt', 'slides')
    if os.path.isdir(slides_dir):
        slide_files = sorted([
            f for f in os.listdir(slides_dir)
            if f.startswith('slide') and f.endswith('.xml') and f != 'slide0.xml'
        ], key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))

        for i, sf in enumerate(slide_files):
            slide_path = os.path.join(slides_dir, sf)
            try:
                slide_info = parse_slide(slide_path)
                slide_info["number"] = i + 1
                slide_info["file"] = sf
                result["slides"].append(slide_info)
            except ET.ParseError as e:
                print(json.dumps({"warning": f"Failed to parse {sf}: {str(e)}"}), file=sys.stderr)

    result["template_info"]["slide_count"] = len(result["slides"])
    result["template_info"]["layout_count"] = len(result["layouts"])
    result["template_info"]["animated_slides"] = [
        s["number"] for s in result["slides"] if s.get("has_animation")
    ]

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
