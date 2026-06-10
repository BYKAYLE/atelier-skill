#!/usr/bin/env python3
"""Path A 전용 텍스트 교체 엔진. 언팩된 슬라이드 XML의 <a:t> 텍스트를 교체한다."""

import argparse
import json
import os
import sys
import copy
import re
import xml.etree.ElementTree as ET

NSMAP = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

for prefix, uri in NSMAP.items():
    ET.register_namespace(prefix, uri)


def tag(ns, local):
    return '{%s}%s' % (NSMAP[ns], local)


def has_korean(text):
    return bool(re.search(r'[\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F]', text))


def detect_lang(text):
    return 'ko-KR' if has_korean(text) else 'en-US'


def set_lang_attr(rpr_elem, text):
    if rpr_elem is not None:
        rpr_elem.set('lang', detect_lang(text))


def merge_runs_to_first(para, text_value):
    """
    여러 <a:r> 요소로 분할된 텍스트를 첫 번째 <a:r>의 <a:t>에 통합,
    나머지 <a:r> 삭제. rPr 서식은 건드리지 않음.
    """
    a_r = tag('a', 'r')
    a_t = tag('a', 't')
    a_rPr = tag('a', 'rPr')

    runs = para.findall(a_r)
    if not runs:
        # <a:r> 없으면 새로 생성
        new_r = ET.SubElement(para, a_r)
        new_t = ET.SubElement(new_r, a_t)
        new_t.text = text_value
        return

    first_run = runs[0]
    first_t = first_run.find(a_t)
    if first_t is None:
        first_t = ET.SubElement(first_run, a_t)
    first_t.text = text_value

    # lang 속성 업데이트
    first_rpr = first_run.find(a_rPr)
    set_lang_attr(first_rpr, text_value)

    # 나머지 <a:r> 삭제
    for run in runs[1:]:
        para.remove(run)


def get_first_para_format(txBody):
    """
    첫 번째 <a:p>의 <a:pPr> 및 첫 <a:r>의 <a:rPr>를 deep copy해서 반환.
    """
    a_p = tag('a', 'p')
    a_pPr = tag('a', 'pPr')
    a_r = tag('a', 'r')
    a_rPr = tag('a', 'rPr')

    first_p = txBody.find(a_p)
    pPr_copy = None
    rPr_copy = None

    if first_p is not None:
        pPr = first_p.find(a_pPr)
        if pPr is not None:
            pPr_copy = copy.deepcopy(pPr)

        first_r = first_p.find(a_r)
        if first_r is not None:
            rPr = first_r.find(a_rPr)
            if rPr is not None:
                rPr_copy = copy.deepcopy(rPr)

    return pPr_copy, rPr_copy


def build_bullet_para(text_value, pPr_template, rPr_template):
    """
    배열 텍스트 항목 하나를 위한 <a:p> 요소 생성.
    """
    a_p = tag('a', 'p')
    a_pPr = tag('a', 'pPr')
    a_r = tag('a', 'r')
    a_rPr = tag('a', 'rPr')
    a_t = tag('a', 't')

    new_p = ET.Element(a_p)

    if pPr_template is not None:
        new_pPr = copy.deepcopy(pPr_template)
        new_p.append(new_pPr)

    new_r = ET.SubElement(new_p, a_r)

    if rPr_template is not None:
        new_rPr = copy.deepcopy(rPr_template)
        new_rPr.set('lang', detect_lang(text_value))
        new_r.append(new_rPr)

    new_t = ET.SubElement(new_r, a_t)
    new_t.text = text_value

    return new_p


def replace_txbody_text(txBody, text_value):
    """
    <p:txBody> 내부 텍스트 교체.
    text_value가 문자열이면 단일 교체, 리스트면 배열(불릿) 교체.
    """
    a_p = tag('a', 'p')
    a_bodyPr = tag('a', 'bodyPr')
    a_lstStyle = tag('a', 'lstStyle')

    if isinstance(text_value, list):
        # 배열 텍스트: 서식 템플릿 추출 후 기존 <a:p> 모두 삭제, 새로 생성
        pPr_template, rPr_template = get_first_para_format(txBody)

        # 보존해야 할 비-<a:p> 자식들 목록화
        preserved = []
        for child in list(txBody):
            if child.tag != a_p:
                preserved.append(child)

        # 기존 자식 모두 제거
        for child in list(txBody):
            txBody.remove(child)

        # 보존 자식 재삽입
        for child in preserved:
            txBody.append(child)

        # 새 <a:p> 생성
        for item in text_value:
            new_p = build_bullet_para(item, pPr_template, rPr_template)
            txBody.append(new_p)

    else:
        # 단일 문자열: 첫 번째 <a:p>만 사용, 나머지 삭제
        paras = txBody.findall(a_p)
        if not paras:
            new_p = ET.SubElement(txBody, a_p)
            merge_runs_to_first(new_p, text_value)
        else:
            first_p = paras[0]
            merge_runs_to_first(first_p, text_value)
            # 나머지 <a:p> 삭제
            for para in paras[1:]:
                txBody.remove(para)


def find_placeholder_sp(root, idx_str):
    """
    idx로 placeholder sp 탐색.
    <p:ph idx="N"/> 또는 type 기반 (idx=0 → type="title" 등).
    """
    p_sp = tag('p', 'sp')
    p_nvSpPr = tag('p', 'nvSpPr')
    p_nvPr = tag('p', 'nvPr')
    p_ph = tag('p', 'ph')
    p_txBody = tag('p', 'txBody')

    idx_int = int(idx_str)

    for sp in root.iter(p_sp):
        nvSpPr = sp.find(p_nvSpPr)
        if nvSpPr is None:
            continue
        nvPr = nvSpPr.find(p_nvPr)
        if nvPr is None:
            continue
        ph = nvPr.find(p_ph)
        if ph is None:
            continue

        ph_idx = ph.get('idx')
        ph_type = ph.get('type', '')

        # idx 매칭
        if ph_idx is not None and int(ph_idx) == idx_int:
            txBody = sp.find(p_txBody)
            if txBody is not None:
                return txBody

        # idx=0 은 title/ctrTitle 타입으로도 매칭
        if idx_int == 0 and ph_idx is None and ph_type in ('title', 'ctrTitle'):
            txBody = sp.find(p_txBody)
            if txBody is not None:
                return txBody

    return None


def find_textbox_sp(root, name):
    """
    name으로 textbox sp 탐색.
    <p:nvSpPr><p:cNvPr name="..."/>
    """
    p_sp = tag('p', 'sp')
    p_nvSpPr = tag('p', 'nvSpPr')
    p_cNvPr = tag('p', 'cNvPr')
    p_txBody = tag('p', 'txBody')

    for sp in root.iter(p_sp):
        nvSpPr = sp.find(p_nvSpPr)
        if nvSpPr is None:
            continue
        cNvPr = nvSpPr.find(p_cNvPr)
        if cNvPr is None:
            continue
        if cNvPr.get('name') == name:
            txBody = sp.find(p_txBody)
            if txBody is not None:
                return txBody

    return None


def serialize_xml(tree, file_path):
    """
    XML 파일 직렬화. XML 선언 보존, UTF-8 인코딩.
    """
    xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    xml_bytes = ET.tostring(tree.getroot(), encoding='unicode')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(xml_declaration)
        f.write(xml_bytes)


def process_slide(file_path, slide_spec):
    """
    슬라이드 XML 파일에 교체 수행. 교체 횟수 반환.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    count = 0

    # placeholder 교체
    placeholders = slide_spec.get('placeholders', {})
    for idx_str, spec in placeholders.items():
        text_value = spec.get('text')
        if text_value is None:
            continue
        txBody = find_placeholder_sp(root, idx_str)
        if txBody is None:
            raise ValueError(
                'placeholder idx=%s not found in %s' % (idx_str, file_path)
            )
        replace_txbody_text(txBody, text_value)
        count += 1

    # textbox 교체
    textboxes = slide_spec.get('textboxes', {})
    for name, spec in textboxes.items():
        text_value = spec.get('text')
        if text_value is None:
            continue
        txBody = find_textbox_sp(root, name)
        if txBody is None:
            raise ValueError(
                'textbox name="%s" not found in %s' % (name, file_path)
            )
        replace_txbody_text(txBody, text_value)
        count += 1

    serialize_xml(tree, file_path)
    return count


def main():
    parser = argparse.ArgumentParser(description='슬라이드 XML 텍스트 교체 엔진')
    parser.add_argument('--dir', required=True, help='언팩된 슬라이드 디렉토리 경로')
    parser.add_argument('--replacements', required=True, help='replacements.json 파일 경로')
    args = parser.parse_args()

    with open(args.replacements, 'r', encoding='utf-8') as f:
        replacements = json.load(f)

    modified_files = []
    replacements_made = 0
    errors = []

    for slide_filename, slide_spec in replacements.items():
        file_path = os.path.join(args.dir, 'ppt', 'slides', slide_filename)
        if not os.path.exists(file_path):
            # slides/ 없이 직접 dir 하위 탐색
            file_path = os.path.join(args.dir, slide_filename)

        try:
            count = process_slide(file_path, slide_spec)
            modified_files.append(slide_filename)
            replacements_made += count
        except Exception as e:
            errors.append({'file': slide_filename, 'error': str(e)})

    result = {
        'success': len(errors) == 0,
        'modified_files': modified_files,
        'replacements_made': replacements_made,
        'errors': errors,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
