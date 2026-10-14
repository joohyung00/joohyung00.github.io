#!/usr/bin/env python3
"""Expand a .pptx into one slide per animation STEP, so a converter that ignores animations
(LibreOffice) still yields the intermediate states, like clicking through in PowerPoint.

    python build/pptx_steps.py deck.pptx expanded.pptx [--keep 1-18] [--drop 8,11] [--json steps.json]

What counts as a step: every click group in the slide's main animation sequence (p:timing →
mainSeq → one p:par per click) that contains an ENTRANCE or EXIT effect (presetClass entr/exit)
targeting a shape (p:spTgt) or a paragraph range of a shape (p:txEl/p:pRg). Emphasis, motion-path
and media effects are ignored (they end in the final look anyway). For a slide with K such clicks the
output holds K+1 copies: state 0 (before any click) … state K (= the original slide, final look),
in that order. Shapes not yet entered / already exited are REMOVED from the copy; not-yet-shown
paragraphs are removed from their text body. All p:timing blocks are stripped from the output.

steps.json: {"slides": [{"n": 1, "steps": 0}, {"n": 2, "steps": 3}, …], "pages": total} — for each
kept original slide (1-based, in output order) how many intermediate states precede its final page.
"""
import argparse, copy, json, re, sys, zipfile
from xml.etree import ElementTree as ET

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
      "ct": "http://schemas.openxmlformats.org/package/2006/content-types"}
for k, v in NS.items():
    ET.register_namespace("" if k in ("rel", "ct") else k, v)
# keep the other common prefixes stable so PowerPoint-style XML round-trips
for pfx, uri in {"mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
                 "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
                 "p15": "http://schemas.microsoft.com/office/powerpoint/2012/main",
                 "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
                 "a16": "http://schemas.microsoft.com/office/drawing/2014/main",
                 "v": "urn:schemas-microsoft-com:vml", "o": "urn:schemas-microsoft-com:office:office"}.items():
    ET.register_namespace(pfx, uri)
P, A = "{%s}" % NS["p"], "{%s}" % NS["a"]


def _xml(el):
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(el, encoding="unicode").encode("utf-8")


def parse_range(spec, n):
    keep = set()
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1); keep.update(range(int(a), int(b) + 1))
        else:
            keep.add(int(part))
    return {i for i in keep if 1 <= i <= n}


def click_plan(slide_root):
    """Returns (K, shape_enter, shape_exit, para_enter) where the dicts map shape id → click
    number (1-based) and para_enter maps (shape id, paragraph index) → click number."""
    timing = slide_root.find(f"{P}timing")
    if timing is None:
        return 0, {}, {}, {}
    main = None
    for ctn in timing.iter(f"{P}cTn"):
        if ctn.get("nodeType") == "mainSeq":
            main = ctn; break
    if main is None:
        return 0, {}, {}, {}
    child = main.find(f"{P}childTnLst")
    if child is None:
        return 0, {}, {}, {}
    shape_enter, shape_exit, para_enter = {}, {}, {}
    k = 0
    for par in child.findall(f"{P}par"):          # one p:par per click group
        found = False
        for ctn in par.iter(f"{P}cTn"):
            cls = ctn.get("presetClass")
            if cls not in ("entr", "exit"):
                continue
            for tgt in ctn.iter(f"{P}spTgt"):
                spid = tgt.get("spid")
                if spid is None:
                    continue
                prg = tgt.find(f"{P}txEl/{P}pRg")
                if prg is not None and cls == "entr":
                    st, en = int(prg.get("st", 0)), int(prg.get("end", prg.get("st", 0)))
                    for i in range(st, en + 1):
                        para_enter.setdefault((spid, i), k + 1)
                    found = True
                elif prg is None:
                    d = shape_enter if cls == "entr" else shape_exit
                    if spid not in d:
                        d[spid] = k + 1
                    found = True
        if found:
            k += 1
    # a shape that both enters and exits: exit must come after entrance to mean anything
    for spid, c in list(shape_exit.items()):
        if spid in shape_enter and shape_enter[spid] >= c:
            del shape_exit[spid]
    return k, shape_enter, shape_exit, para_enter


def shape_elems(spTree):
    """Yield (element, parent, id) for every shape-like child anywhere under spTree."""
    out = []
    def walk(parent):
        for el in list(parent):
            tag = el.tag.split("}")[1]
            if tag in ("sp", "pic", "grpSp", "graphicFrame", "cxnSp", "contentPart"):
                cnv = None
                for c in el.iter(f"{P}cNvPr"):
                    cnv = c; break
                out.append((el, parent, cnv.get("id") if cnv is not None else None))
                if tag == "grpSp":
                    walk(el)
    walk(spTree)
    return out


def freeze_slidenum(root, number):
    """Replace every slide-number field (<a:fld type="slidenum">) with plain text of the ORIGINAL
    slide number: converters evaluate the field by position, and the expanded deck has more pages."""
    for parent in root.iter():
        for fld in list(parent):
            if fld.tag == f"{A}fld" and fld.get("type") == "slidenum":
                r = ET.Element(f"{A}r")
                rpr = fld.find(f"{A}rPr")
                if rpr is not None:
                    r.append(copy.deepcopy(rpr))
                t = ET.SubElement(r, f"{A}t"); t.text = str(number)
                parent.insert(list(parent).index(fld), r); parent.remove(fld)


def state_xml(slide_root, state, shape_enter, shape_exit, para_enter):
    """A deep copy of the slide showing the look after `state` clicks (timing removed)."""
    root = copy.deepcopy(slide_root)
    t = root.find(f"{P}timing")
    if t is not None:
        root.remove(t)
    spTree = root.find(f"{P}cSld/{P}spTree")
    if spTree is None:
        return root
    for el, parent, spid in shape_elems(spTree):
        if spid is None:
            continue
        hidden = (spid in shape_enter and shape_enter[spid] > state) or (spid in shape_exit and shape_exit[spid] <= state)
        if hidden:
            try:
                parent.remove(el)
            except ValueError:
                pass
            continue
        # paragraph builds inside a visible shape
        paras = [key for key in para_enter if key[0] == spid and para_enter[key] > state]
        if paras:
            tx = el.find(f"{P}txBody")
            if tx is None:
                continue
            ps = tx.findall(f"{A}p")
            for key in paras:
                idx = key[1]
                if idx < len(ps) and ps[idx] in list(tx):
                    tx.remove(ps[idx])
            if not tx.findall(f"{A}p"):
                tx.append(ET.SubElement(tx, f"{A}p"))
    return root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--keep", help="keep only these original slides, e.g. 1-18")
    ap.add_argument("--drop", help="drop these original slides, e.g. 8,11")
    ap.add_argument("--json", help="write the steps map here")
    a = ap.parse_args()

    zin = zipfile.ZipFile(a.src)
    names = zin.namelist()
    pres = ET.fromstring(zin.read("ppt/presentation.xml"))
    prels = ET.fromstring(zin.read("ppt/_rels/presentation.xml.rels"))
    ctypes = ET.fromstring(zin.read("[Content_Types].xml"))
    sldIdLst = pres.find(f"{P}sldIdLst")
    rid2target = {r.get("Id"): r.get("Target") for r in prels}
    order = [(s.get("id"), s.get(f"{{{NS['r']}}}id")) for s in sldIdLst]
    n = len(order)
    keep = parse_range(a.keep, n) if a.keep else set(range(1, n + 1))
    keep -= parse_range(a.drop, n) if a.drop else set()
    max_id = max(int(sid) for sid, _ in order)
    max_rid = max(int(re.sub(r"\D", "", r.get("Id")) or 0) for r in prels)

    out_files = {}   # name -> bytes (new/modified parts)
    new_sld = []     # (sldId, rId) in output order
    steps_map = []
    removed_rels = set()
    for i, (sid, rid) in enumerate(order, 1):
        target = rid2target[rid]                     # slides/slideN.xml
        sname = "ppt/" + target
        if i not in keep:
            removed_rels.add(rid); continue
        root = ET.fromstring(zin.read(sname))
        K, se, sx, pe = click_plan(root)
        base = re.sub(r"\.xml$", "", target.split("/")[-1])
        rels_name = f"ppt/slides/_rels/{base}.xml.rels"
        rels_xml = zin.read(rels_name) if rels_name in names else None
        for state in range(K):                       # intermediate states first
            max_id += 1; max_rid += 1
            cname = f"ppt/slides/{base}_s{state}.xml"
            st_root = state_xml(root, state, se, sx, pe); freeze_slidenum(st_root, i)
            out_files[cname] = _xml(st_root)
            if rels_xml:
                rr = ET.fromstring(rels_xml)
                for r in list(rr):                   # the clone must not claim the notes slide
                    if r.get("Type", "").endswith("/notesSlide"):
                        rr.remove(r)
                out_files[f"ppt/slides/_rels/{base}_s{state}.xml.rels"] = _xml(rr)
            ET.SubElement(prels, f"{{{NS['rel']}}}Relationship", {"Id": f"rId{max_rid}", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", "Target": f"slides/{base}_s{state}.xml"})
            ET.SubElement(ctypes, f"{{{NS['ct']}}}Override", {"PartName": f"/{cname}", "ContentType": "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"})
            new_sld.append((str(max_id), f"rId{max_rid}"))
        # final state = original slide, timing stripped
        final = copy.deepcopy(root)
        t = final.find(f"{P}timing")
        if t is not None:
            final.remove(t)
        freeze_slidenum(final, i)
        out_files[sname] = _xml(final)
        new_sld.append((sid, rid))
        steps_map.append({"n": len(steps_map) + 1, "orig": i, "steps": K})

    for s in list(sldIdLst):
        sldIdLst.remove(s)
    for sid, rid in new_sld:
        ET.SubElement(sldIdLst, f"{P}sldId", {"id": sid, f"{{{NS['r']}}}id": rid})
    for r in list(prels):
        if r.get("Id") in removed_rels:
            prels.remove(r)
    out_files["ppt/presentation.xml"] = _xml(pres)
    out_files["ppt/_rels/presentation.xml.rels"] = _xml(prels)
    out_files["[Content_Types].xml"] = _xml(ctypes)

    with zipfile.ZipFile(a.dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for nm in names:
            if nm in out_files:
                continue
            zout.writestr(nm, zin.read(nm))
        for nm, data in out_files.items():
            zout.writestr(nm, data)
    total = sum(s["steps"] + 1 for s in steps_map)
    info = {"slides": steps_map, "pages": total}
    if a.json:
        with open(a.json, "w") as f:
            json.dump(info, f, indent=1)
    animated = [s for s in steps_map if s["steps"]]
    print(f"{a.dst}: {len(steps_map)} slides → {total} pages; {len(animated)} animated slide(s), {sum(s['steps'] for s in animated)} steps")


if __name__ == "__main__":
    sys.exit(main())
