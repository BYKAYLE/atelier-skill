#!/usr/bin/env python3
"""
inject_animation.py
Injects <p:timing> and <p:transition> elements into slide XML files.
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy

# Namespace declarations
NAMESPACES = {
    "a":   "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p":   "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r":   "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    "mc":  "http://schemas.openxmlformats.org/markup-compatibility/2006",
}

for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

def p(tag):
    return f"{{{P}}}{tag}"

def a(tag):
    return f"{{{A}}}{tag}"


PRESET_MAP = {
    "Appear":        {"presetID": 1,  "presetClass": "entr", "presetSubtype": 0},
    "Fly In Bottom": {"presetID": 2,  "presetClass": "entr", "presetSubtype": 4},
    "Fly In Left":   {"presetID": 2,  "presetClass": "entr", "presetSubtype": 8},
    "Fly In Right":  {"presetID": 2,  "presetClass": "entr", "presetSubtype": 2},
    "Fly In Top":    {"presetID": 2,  "presetClass": "entr", "presetSubtype": 1},
    "Fade":          {"presetID": 10, "presetClass": "entr", "presetSubtype": 0},
    "Wipe Bottom":   {"presetID": 22, "presetClass": "entr", "presetSubtype": 4},
    "Wipe Left":     {"presetID": 22, "presetClass": "entr", "presetSubtype": 8},
    "Wipe Right":    {"presetID": 22, "presetClass": "entr", "presetSubtype": 2},
    "Wipe Top":      {"presetID": 22, "presetClass": "entr", "presetSubtype": 1},
    "Zoom In":       {"presetID": 53, "presetClass": "entr", "presetSubtype": 16},
    "Pulse":         {"presetID": 26, "presetClass": "emph", "presetSubtype": 0},
}

TRANSITION_MAP = {
    "fade": "<p:fade/>",
    "push": '<p:push dir="{direction}"/>',
    "wipe": '<p:wipe dir="{direction}"/>',
    "none": "",
}


def get_shape_id_map(root):
    """Returns {shape_name: shape_id} by scanning <p:cNvPr id="..." name="..."/>."""
    shape_map = {}
    for elem in root.iter():
        if elem.tag == p("cNvPr") or elem.tag == f"{{{A}}}cNvPr":
            name = elem.get("name")
            sid = elem.get("id")
            if name and sid:
                shape_map[name] = sid
    # Also scan a:cNvPr which may appear in drawingml
    for elem in root.iter(f"{{{A}}}cNvPr"):
        name = elem.get("name")
        sid = elem.get("id")
        if name and sid:
            shape_map[name] = sid
    return shape_map


def build_anim_par(anim_data, shape_id, id_counter, trigger, prev_id=None, delay=0):
    """
    Builds a <p:par> element representing a single animation effect.
    Returns (element, next_id_counter).
    id_counter: starting id for this animation block (uses id, id+1, id+2, id+3, id+4)
    """
    preset_info = PRESET_MAP.get(anim_data["effect"])
    if preset_info is None:
        return None, id_counter

    preset_id_val = str(preset_info["presetID"])
    preset_class  = preset_info["presetClass"]
    preset_sub    = str(preset_info["presetSubtype"])
    duration      = str(anim_data.get("duration", 500))
    delay_val     = str(anim_data.get("delay", 0))

    id0 = id_counter
    id1 = id_counter + 1
    id2 = id_counter + 2
    id3 = id_counter + 3
    id4 = id_counter + 4

    # Determine stCondLst for the outermost par based on trigger
    if trigger == "onClick":
        outer_cond_attrib = {"delay": "0"}
    elif trigger == "withPrevious":
        if prev_id is not None:
            outer_cond_attrib = {"delay": "0", "evt": "begin", "tn": str(prev_id)}
        else:
            outer_cond_attrib = {"delay": "0"}
    elif trigger == "afterPrevious":
        if prev_id is not None:
            outer_cond_attrib = {"delay": delay_val, "evt": "end", "tn": str(prev_id)}
        else:
            outer_cond_attrib = {"delay": delay_val}
    else:
        outer_cond_attrib = {"delay": "0"}

    # Build the XML structure
    outer_par = ET.Element(p("par"))

    ctn0 = ET.SubElement(outer_par, p("cTn"), {"id": str(id0), "fill": "hold"})
    stCond0 = ET.SubElement(ctn0, p("stCondLst"))
    ET.SubElement(stCond0, p("cond"), outer_cond_attrib)
    childLst0 = ET.SubElement(ctn0, p("childTnLst"))

    par1 = ET.SubElement(childLst0, p("par"))
    ctn1 = ET.SubElement(par1, p("cTn"), {"id": str(id1), "fill": "hold"})
    stCond1 = ET.SubElement(ctn1, p("stCondLst"))
    ET.SubElement(stCond1, p("cond"), {"delay": "0"})
    childLst1 = ET.SubElement(ctn1, p("childTnLst"))

    par2 = ET.SubElement(childLst1, p("par"))
    ctn2 = ET.SubElement(par2, p("cTn"), {
        "id": str(id2),
        "presetID": preset_id_val,
        "presetClass": preset_class,
        "presetSubtype": preset_sub,
        "fill": "hold",
    })
    stCond2 = ET.SubElement(ctn2, p("stCondLst"))
    ET.SubElement(stCond2, p("cond"), {"delay": delay_val})
    childLst2 = ET.SubElement(ctn2, p("childTnLst"))

    # <p:set>
    set_elem = ET.SubElement(childLst2, p("set"))
    cBhvr_set = ET.SubElement(set_elem, p("cBhvr"))
    ctn3 = ET.SubElement(cBhvr_set, p("cTn"), {"id": str(id3), "dur": "1", "fill": "hold"})
    stCond3 = ET.SubElement(ctn3, p("stCondLst"))
    ET.SubElement(stCond3, p("cond"), {"delay": "0"})
    tgtEl_set = ET.SubElement(cBhvr_set, p("tgtEl"))
    ET.SubElement(tgtEl_set, p("spTgt"), {"spid": str(shape_id)})
    attrNameLst = ET.SubElement(cBhvr_set, p("attrNameLst"))
    attrName = ET.SubElement(attrNameLst, p("attrName"))
    attrName.text = "style.visibility"
    to_elem = ET.SubElement(set_elem, p("to"))
    strVal = ET.SubElement(to_elem, p("strVal"), {"val": "visible"})

    # <p:animEffect>
    animEffect = ET.SubElement(childLst2, p("animEffect"), {"transition": "in", "filter": "fade"})
    cBhvr_anim = ET.SubElement(animEffect, p("cBhvr"))
    ET.SubElement(cBhvr_anim, p("cTn"), {"id": str(id4), "dur": duration})
    tgtEl_anim = ET.SubElement(cBhvr_anim, p("tgtEl"))
    ET.SubElement(tgtEl_anim, p("spTgt"), {"spid": str(shape_id)})

    return outer_par, id_counter + 5


def build_timing(animations, shape_map, warnings):
    """
    Builds a <p:timing> element from the list of animation dicts.
    Returns the element or None if no valid animations.
    """
    id_counter = 1

    # Root structure
    timing_el = ET.Element(p("timing"))
    tnLst = ET.SubElement(timing_el, p("tnLst"))
    root_par = ET.SubElement(tnLst, p("par"))

    root_ctn = ET.SubElement(root_par, p("cTn"), {
        "id": str(id_counter),
        "dur": "indefinite",
        "restart": "never",
        "nodeType": "tmRoot",
    })
    id_counter += 1

    root_child = ET.SubElement(root_ctn, p("childTnLst"))

    seq = ET.SubElement(root_child, p("seq"), {"concurrent": "1", "nextAc": "seek"})
    main_ctn = ET.SubElement(seq, p("cTn"), {
        "id": str(id_counter),
        "dur": "indefinite",
        "nodeType": "mainSeq",
    })
    id_counter += 1

    seq_child = ET.SubElement(main_ctn, p("childTnLst"))

    # prevCondLst / nextCondLst
    prevCondLst = ET.SubElement(seq, p("prevCondLst"))
    prev_cond = ET.SubElement(prevCondLst, p("cond"), {"evt": "onPrev", "delay": "0"})
    prev_tgt = ET.SubElement(prev_cond, p("tgtEl"))
    ET.SubElement(prev_tgt, p("sldTgt"))

    nextCondLst = ET.SubElement(seq, p("nextCondLst"))
    next_cond = ET.SubElement(nextCondLst, p("cond"), {"evt": "onNext", "delay": "0"})
    next_tgt = ET.SubElement(next_cond, p("tgtEl"))
    ET.SubElement(next_tgt, p("sldTgt"))

    anim_added = 0
    prev_id = None  # id of the last animation's outermost cTn for withPrevious/afterPrevious

    for anim in animations:
        target_name = anim.get("target_shape_name", "")
        shape_id = shape_map.get(target_name)
        if shape_id is None:
            warnings.append(f"Shape '{target_name}' not found; skipping animation.")
            continue

        effect = anim.get("effect", "Fade")
        if effect not in PRESET_MAP:
            warnings.append(f"Unknown effect '{effect}'; skipping.")
            continue

        trigger = anim.get("trigger", "onClick")
        delay = anim.get("delay", 0)

        par_el, id_counter = build_anim_par(
            anim_data=anim,
            shape_id=shape_id,
            id_counter=id_counter,
            trigger=trigger,
            prev_id=prev_id,
            delay=delay,
        )
        if par_el is None:
            continue

        seq_child.append(par_el)
        prev_id = id_counter - 5  # id of the outermost cTn we just added
        anim_added += 1

    return timing_el, anim_added


def build_transition_element(transition_spec):
    """
    Builds a <p:transition> element from the spec dict.
    Returns the element string (will be parsed) or None.
    """
    t_type = transition_spec.get("type", "none")
    speed  = transition_spec.get("speed", "med")
    direction = transition_spec.get("direction", "l")

    trans_el = ET.Element(p("transition"), {"spd": speed})

    inner_template = TRANSITION_MAP.get(t_type, "")
    if inner_template:
        inner_str = inner_template.format(direction=direction)
        # Parse inner element and append
        try:
            # Register namespace so p: prefix works
            inner_str_full = (
                f'<root xmlns:p="{P}" xmlns:a="{A}">'
                f'{inner_str}'
                f'</root>'
            )
            inner_root = ET.fromstring(inner_str_full)
            for child in inner_root:
                trans_el.append(child)
        except ET.ParseError:
            pass  # no inner element

    return trans_el


def serialize_xml(tree, original_decl=None):
    """Serialize ElementTree to bytes, preserving XML declaration if present."""
    import io
    buf = io.BytesIO()
    tree.write(buf, xml_declaration=True, encoding="UTF-8")
    content = buf.getvalue()
    return content


def process_slide(slide_path, slide_spec, warnings, errors):
    """
    Process a single slide XML file.
    Returns (modified: bool, anim_added: int, transition_added: int, skipped: bool)
    """
    try:
        with open(slide_path, "rb") as f:
            raw = f.read()
    except OSError as e:
        errors.append(f"{os.path.basename(slide_path)}: cannot read file: {e}")
        return False, 0, 0, False

    # Detect XML declaration
    has_decl = raw.lstrip().startswith(b"<?xml")

    try:
        # Parse preserving namespaces
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        errors.append(f"{os.path.basename(slide_path)}: XML parse error: {e}")
        return False, 0, 0, False

    # Check for existing <p:timing> — if present, skip (preserve)
    existing_timing = root.find(p("timing"))
    if existing_timing is not None:
        return False, 0, 0, True  # skipped

    shape_map = get_shape_id_map(root)

    animations = slide_spec.get("animations", [])
    transition_spec = slide_spec.get("transition")

    if len(animations) > 3:
        warnings.append(
            f"{os.path.basename(slide_path)}: {len(animations)} animations specified (max 3); processing all but warning."
        )

    anim_added = 0
    transition_added = 0
    modified = False

    # ---- Handle animations ----
    if animations:
        timing_el, anim_added = build_timing(animations, shape_map, warnings)
        if anim_added > 0:
            root.append(timing_el)
            modified = True

    # ---- Handle transition ----
    if transition_spec:
        existing_trans = root.find(p("transition"))
        trans_el = build_transition_element(transition_spec)

        # Find cSld to insert before it
        cSld = root.find(p("cSld"))
        children = list(root)

        if existing_trans is not None:
            # Replace existing
            idx = children.index(existing_trans)
            root.remove(existing_trans)
            root.insert(idx, trans_el)
        elif cSld is not None:
            idx = children.index(cSld)
            root.insert(idx, trans_el)
        else:
            root.append(trans_el)

        transition_added = 1
        modified = True

    if not modified:
        return False, 0, 0, False

    # Write back
    tree = ET.ElementTree(root)
    try:
        content = serialize_xml(tree)
        with open(slide_path, "wb") as f:
            f.write(content)
    except OSError as e:
        errors.append(f"{os.path.basename(slide_path)}: cannot write file: {e}")
        return False, 0, 0, False

    return True, anim_added, transition_added, False


def main():
    parser = argparse.ArgumentParser(description="Inject animations and transitions into slide XML files.")
    parser.add_argument("--dir",        required=True, help="Unpacked PPTX directory (contains ppt/slides/)")
    parser.add_argument("--animations", required=True, help="Path to animations.json")
    args = parser.parse_args()

    # Load animations JSON
    try:
        with open(args.animations, "r", encoding="utf-8") as f:
            anim_config = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        result = {
            "success": False,
            "modified_files": [],
            "animations_added": 0,
            "transitions_added": 0,
            "skipped_existing": [],
            "warnings": [],
            "errors": [f"Failed to load animations JSON: {e}"],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    # Locate slides directory
    slides_dir = os.path.join(args.dir, "ppt", "slides")
    if not os.path.isdir(slides_dir):
        # Fallback: maybe dir already points to slides/
        if os.path.isdir(args.dir):
            slides_dir = args.dir
        else:
            result = {
                "success": False,
                "modified_files": [],
                "animations_added": 0,
                "transitions_added": 0,
                "skipped_existing": [],
                "warnings": [],
                "errors": [f"Slides directory not found: {slides_dir}"],
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)

    modified_files    = []
    total_anim        = 0
    total_trans       = 0
    skipped_existing  = []
    warnings          = []
    errors            = []

    for slide_name, slide_spec in anim_config.items():
        slide_path = os.path.join(slides_dir, slide_name)
        if not os.path.isfile(slide_path):
            errors.append(f"{slide_name}: file not found in {slides_dir}")
            continue

        try:
            modified, anim_added, trans_added, skipped = process_slide(
                slide_path, slide_spec, warnings, errors
            )
        except Exception as e:
            errors.append(f"{slide_name}: unexpected error: {e}")
            continue

        if skipped:
            skipped_existing.append(slide_name)
        elif modified:
            modified_files.append(slide_name)
            total_anim  += anim_added
            total_trans += trans_added

    result = {
        "success": len(errors) == 0,
        "modified_files": modified_files,
        "animations_added": total_anim,
        "transitions_added": total_trans,
        "skipped_existing": skipped_existing,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
