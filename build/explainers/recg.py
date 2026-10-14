"""ReCG worked example — frames. Running example: three small JSON documents (as in the talk's "global example")."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen import *

DOCS_JSON = [
    ('j₁', '{"id": "jhyun", "pswd": "qwer",\n "info": {"age": 23, "gender": "male"}}'),
    ('j₂', '{"name": "wshan",\n "info": {"age": 52, "gender": "male",\n          "email": "w@a.com"}}'),
    ('j₃', '{"id": "btak", "pswd": "zxcv",\n "info": {"age": 45, "gender": "male"}}'),
]
Q_HTML = 'Given <em>three JSON documents</em> and no schema, which <em>set of JSON schemas</em> should describe the collection — specific enough to reject junk, general enough to accept the documents we have not seen yet?'
ANSWER = "Z = {S₁, S₂}"
TABS = ["Problem", "Bottom-up stages", "Search & MDL", "Output"]


def tabs(active, interm=False):
    out = [(t, "active" if i == active else "") for i, t in enumerate(TABS)]
    if interm:
        out = [(t, "") for t, _ in out] + [("✦ Why it works", "intermission")]
    return out


def json_pre(label, body, hl=()):
    s = esc(body)
    import re
    s = re.sub(r'"([^"]+)":', r'<span class="k">"\1"</span>:', s)
    s = re.sub(r': "([^"]*)"', r': <span class="s">"\1"</span>', s)
    s = re.sub(r': (\d+)', r': <span class="n">\1</span>', s)
    for h in hl:
        s = s.replace(h, f'<span class="hl">{h}</span>')
    return f'<div class="mini-label">{label}</div><pre class="json">{s}</pre>'


# ------------------------------------------------------------------ tree drawing
# node: dict(kind='obj'|'val'|'sch', label, children=[(edgelabel, node)], w=None)
def T(kind, label, children=(), **kw):
    return dict(kind=kind, label=label, children=list(children), **kw)


def measure(n):
    if not n["children"]:
        n["w"] = 76 if n["kind"] != "val" else max(64, 9.5 * len(n["label"]) + 22)
        return n["w"]
    w = sum(measure(c) for _, c in n["children"]) + 16 * (len(n["children"]) - 1)
    n["w"] = max(w, 76)
    return n["w"]


def draw(n, x, y, out, lv=0):
    """draw subtree with its left edge at x, top at y; returns centre x."""
    cx = x + n["w"] / 2
    k, lab = n["kind"], n["label"]
    hl = n.get("hl")
    if k == "obj":
        out.append(circle(cx, y + 19, 19, "{ }", fill="#fff" if not hl else "#EDE9FE", stroke="#A78BFA" if not hl else "#7C3AED", color="#6D28D9", fs=14, sw=2.2 if hl else 1.6))
    elif k == "arr":
        out.append(box(cx - 20, y, 40, 38, "[ ]", fill="#fff", stroke="#A78BFA", color="#6D28D9", r=9, fs=14))
    elif k == "val":
        out.append(box(cx - n["w"] / 2 + 4, y + 3, n["w"] - 8, 34, lab, fill="#F8FAFC", stroke="#CBD5E1", color="#334155", r=8, fs=14, bold=False))
    else:  # schema node
        col = {"STR": ("#ECFDF5", "#6EE7B7", "#065F46"), "NUM": ("#EFF6FF", "#93C5FD", "#1E40AF"), "BOOL": ("#FFF7ED", "#FDBA74", "#9A3412"),
               "OBJ": ("#F5F3FF", "#A78BFA", "#5B21B6"), "ANYOF": ("#FDF2F8", "#F9A8D4", "#9D174D"), "NULL": ("#F3F4F6", "#D1D5DB", "#374151")}.get(lab.split()[0], ("#F5F3FF", "#A78BFA", "#5B21B6"))
        out.append(box(cx - 36, y, 72, 38, lab, fill=col[0], stroke=col[1], color=col[2], r=10, fs=14, sw=2.4 if hl else 1.6))
    if n["children"]:
        cxs = x
        for el, c in n["children"]:
            ccx = cxs + c["w"] / 2
            opt = el.endswith("?")
            out.append(line(cx, y + 38, ccx, y + 104, stroke="#C4B5FD" if not opt else "#F9A8D4", sw=1.6, dash="4 3" if opt or el == "*" else ""))
            mx, my = (cx + ccx) / 2, y + 71
            out.append(f'<rect x="{mx - 5 - 3.8 * len(el)}" y="{my - 9}" width="{10 + 7.6 * len(el)}" height="18" rx="5" fill="#fff"/>')
            out.append(text(mx, my + 4.5, el, fs=12.5, color="#7C3AED" if not opt else "#BE185D", anchor="middle", weight=600, mono=True))
            draw(c, cxs, y + 104, out, lv + 1)
            cxs += c["w"] + 16
    return cx


def depth(n):
    return 1 + max((depth(c) for _, c in n["children"]), default=0)


def forest_svg(trees, h=None, gap=40, titles=None, extra="", cols=None):
    """Trees laid out in a grid of `cols` columns (default: all in one row)."""
    for t in trees:
        measure(t)
    cols = cols or len(trees)
    rows = [trees[i:i + cols] for i in range(0, len(trees), cols)]
    colw = [max(t["w"] for r in rows for t in r[c:c + 1]) for c in range(cols)]
    rowh = [max(depth(t) for t in r) * 104 - 104 + 42 + 30 for r in rows]
    W = sum(colw) + gap * (cols - 1) + 20
    H = sum(rowh) + 24 * (len(rows) - 1) + 12
    out, y = [ARROW_DEFS, extra], 10
    k = 0
    for ri, r in enumerate(rows):
        x = 10
        for ci, t in enumerate(r):
            x0 = x + (colw[ci] - t["w"]) / 2
            if titles:
                out.append(text(x0 + t["w"] / 2, y + 14, titles[k], fs=14, color="#6D28D9", anchor="middle", weight=700, mono=True))
            draw(t, x0, y + 30, out)
            x += colw[ci] + gap
            k += 1
        y += rowh[ri] + 24
    return svg(W, H, "".join(out))


# instance trees of the three documents, at three stages of derivation
def inst(stage):
    """stage 0: raw; 1: level-3 leaves → schema; 2: level-2 resolved (info objects → schema id, strings → STR)."""
    def leaf(v, kind):
        if stage >= 1:
            return T("sch", kind)
        return T("val", v)
    def l2(v, kind):
        return T("sch", kind) if stage >= 2 else T("val", v)
    info1 = T("obj", "", [("age", leaf("23", "NUM")), ("gender", leaf("\"male\"", "STR"))])
    info2 = T("obj", "", [("age", leaf("52", "NUM")), ("gender", leaf("\"male\"", "STR")), ("email", leaf("\"w@a.com\"", "STR"))])
    info3 = T("obj", "", [("age", leaf("45", "NUM")), ("gender", leaf("\"male\"", "STR"))])
    if stage >= 2:
        info1 = T("sch", "OBJ Sₘ", hl=True); info2 = T("sch", "OBJ Sₘ", hl=True); info3 = T("sch", "OBJ Sₘ", hl=True)
    elif stage == 1:
        info1["hl"] = info2["hl"] = info3["hl"] = True
    j1 = T("obj", "", [("id", l2("\"jhyun\"", "STR")), ("pswd", l2("\"qwer\"", "STR")), ("info", info1)])
    j2 = T("obj", "", [("name", l2("\"wshan\"", "STR")), ("info", info2)])
    j3 = T("obj", "", [("id", l2("\"btak\"", "STR")), ("pswd", l2("\"zxcv\"", "STR")), ("info", info3)])
    return [j1, j2, j3]


def schema_tree(kind):
    if kind == "Sa":
        return T("sch", "OBJ Sₐ", [("age", T("sch", "NUM")), ("gender", T("sch", "STR"))])
    if kind == "Sb":
        return T("sch", "OBJ S_b", [("age", T("sch", "NUM")), ("gender", T("sch", "STR")), ("email", T("sch", "STR"))])
    if kind == "Sm":
        return T("sch", "OBJ Sₘ", [("age", T("sch", "NUM")), ("gender", T("sch", "STR")), ("email?", T("sch", "STR"))])
    if kind == "Sh":
        return T("sch", "OBJ S_h", [("*", T("sch", "ANYOF", [("", T("sch", "NUM")), ("", T("sch", "STR"))]))])
    if kind == "S1":
        return T("sch", "OBJ S₁", [("id", T("sch", "STR")), ("pswd", T("sch", "STR")), ("info", T("sch", "OBJ Sₘ"))])
    if kind == "S2":
        return T("sch", "OBJ S₂", [("name", T("sch", "STR")), ("info", T("sch", "OBJ Sₘ"))])
    if kind == "S12":
        return T("sch", "OBJ S₁₂", [("id?", T("sch", "STR")), ("pswd?", T("sch", "STR")), ("name?", T("sch", "STR")), ("info", T("sch", "OBJ Sₘ"))])


# search tree (states) drawing
def states_svg(hl=(), beam=(), costs=None, show3=True):
    costs = costs or {}
    pos = {"s0,1": (470, 20), "s1,1": (470, 110), "s2,1": (250, 200), "s2,2": (470, 200), "s2,3": (690, 200),
           "s3,1": (140, 300), "s3,2": (250, 300), "s3,3": (360, 300), "s3,4": (470, 300), "s3,5": (580, 300), "s3,6": (690, 300), "s3,7": (800, 300)}
    edges = [("s0,1", "s1,1"), ("s1,1", "s2,1"), ("s1,1", "s2,2"), ("s1,1", "s2,3"), ("s2,1", "s3,1"), ("s2,1", "s3,2"), ("s2,1", "s3,3"),
             ("s2,2", "s3,4"), ("s2,2", "s3,5"), ("s2,3", "s3,6"), ("s2,3", "s3,7")]
    out = [ARROW_DEFS]
    for a, b in edges:
        if not show3 and b.startswith("s3"):
            continue
        (x1, y1), (x2, y2) = pos[a], pos[b]
        on = a in beam and b in (hl + tuple(beam))
        out.append(line(x1 + 50, y1 + 40, x2 + 50, y2, stroke="#8B5CF6" if on else "#D8D0F0", sw=2.5 if on else 1.3))
    for s, (x, y) in pos.items():
        if not show3 and s.startswith("s3"):
            continue
        sub = costs.get(s, "")
        fill, stroke, sw = "#fff", "#D8D0F0", 1.5
        if s in beam:
            fill, stroke, sw = "#F5F3FF", "#A78BFA", 2
        if s in hl:
            fill, stroke, sw = "#EDE9FE", "#7C3AED", 3
        out.append(box(x, y, 100, 40, s, sub, fill=fill, stroke=stroke, sw=sw, fs=13))
    for i, (y, lab) in enumerate([(20, "stage 0 · instances"), (110, "stage 1 · level 3 → schema"), (200, "stage 2 · level 2"), (300, "stage 3 · level 1 (roots)")]):
        if not show3 and i == 3:
            continue
        out.append(text(10, y + 25, lab, fs=11.5, color="#8B86B5", mono=True))
    return svg(960, 360, "".join(out))


def bars(rows, maxv=100):
    out = ""
    for name, src, drc, on in rows:
        w1, w2 = int(src / maxv * 420), int(drc / maxv * 420)
        out += (f'<div class="row" style="align-items:center"><span class="k" style="min-width:52px">{name}</span><span class="v" style="flex:1">'
                f'<span style="display:inline-block;height:16px;border-radius:5px 0 0 5px;background:#8B5CF6;width:{w1}px;vertical-align:middle"></span>'
                f'<span style="display:inline-block;height:16px;border-radius:0 5px 5px 0;background:#60A5FA;width:{w2}px;vertical-align:middle"></span>'
                f' <span class="mono" style="font-size:12.5px;color:{"#6D28D9" if on else "#8B86B5"};font-weight:{700 if on else 500}">{src} + {drc} = {src + drc}{" ★" if on else ""}</span></span></div>')
    return f'<div class="kv">{out}</div><div class="note" style="font-size:12px;margin-top:6px"><span style="display:inline-block;width:12px;height:12px;background:#8B5CF6;border-radius:3px;vertical-align:middle"></span> SRC · schema representation cost &nbsp; <span style="display:inline-block;width:12px;height:12px;background:#60A5FA;border-radius:3px;vertical-align:middle"></span> DRC · data representation cost (bits, illustrative)</div>'


frames = []
BN = banner(Q_HTML, ANSWER, label="OUTPUT")

# F0 — problem
docs = "".join(f'<div>{json_pre(l, b)}</div>' for l, b in DOCS_JSON)
body = '<div class="cols c12">' + panel("Input D⁺ · three JSON documents", f'<div class="cols c3" style="flex:none">{docs}</div><div class="note" style="margin-top:8px">Same collection, two shapes: two <b>account</b>-like records and one <b>name</b>-only record; every record carries an <b>info</b> object, once with an extra <b>email</b>.</div>', icon="📥") + panel("Instance trees and the goal", f'<div class="fill" style="align-items:flex-start">{forest_svg(inst(0), titles=["j₁", "j₂", "j₃"], cols=3)}</div><div class="kv" style="margin-top:6px"><div class="row"><span class="k">tree form</span><span class="v">objects are {{ }} nodes with <b>edge labels</b> = keys; arrays are [ ] nodes with ordered children; primitives are leaves. Root = level 1.</span></div><div class="row"><span class="k">goal</span><span class="v">a schema set <b>Z</b> with j ⊨ Z for all j ∈ D⁺, judged by <b>F1</b> against held-out positives D₂⁺ (should be accepted) and negatives D⁻ (should be rejected)</span></div><div class="row"><span class="k">spectrum</span><span class="v">most specific: one schema per document (rejects everything new) ⟷ most general: "any object" (accepts junk). The right answer is in between.</span></div></div>', icon="🌳") + "</div>"
frames.append(dict(step="Problem", text="JSON schema discovery: from documents alone, derive a schema set that is neither one-schema-per-document nor accept-anything.",
                   stage=stage("Problem", body, tabs(0), BN), status="PROBLEM"))

# F1 — why top-down struggles
body = '<div class="cols c2">' + panel("Top-down: decide the root first", f'<div class="fill" style="align-items:flex-start">{forest_svg(inst(0), titles=["j₁", "j₂", "j₃"], cols=2)}</div><div class="callout fail" style="margin-top:6px">At the root the only visible facts are key sets {{id, pswd, info}} ×2 vs {{name, info}}. Should these be <b>one</b> schema with optional keys or <b>two</b>? That depends on whether the three <b>info</b> children are the same type — which top-down has not derived yet. <b>Insufficient information → ambiguous choice.</b></div>', icon="⬇️") + panel("ReCG: resolve leaves first, roots last", f'<div class="fill" style="align-items:flex-start">{forest_svg(inst(2), titles=["j₁", "j₂", "j₃"], cols=2)}</div><div class="callout ok" style="margin-top:6px">Bottom-up, every decision at level ℓ sees its children already turned into <b>schema nodes with IDs</b>. When the roots are compared, "info" is known to be the same schema <b>Sₘ</b> in all three documents, so the root decision is about id / pswd / name only.</div>', icon="⬆️") + "</div>"
frames.append(dict(step="Idea", text="Existing algorithms derive schemas top-down and must classify a node before its children are known. ReCG goes bottom-up: children first, so each decision is informed.",
                   stage=stage("Bottom-up", body, tabs(0), BN), status="IDEA"))

# F2 — stage 1: leaves
body = '<div class="cols c21">' + panel("State s₁,₁ · level-3 values → primitive schema nodes", f'<div class="fill" style="align-items:flex-start">{forest_svg(inst(1), titles=["j₁", "j₂", "j₃"], cols=3)}</div>', icon="🧱", tag="stage 1") + panel("Primitive types are trivial", '''<div class="kv">
<div class="row"><span class="k">rule</span><span class="v">23 → <b>NUM</b>, "male" → <b>STR</b>, true → <b>BOOL</b>, null → <b>NULL</b>; no ambiguity, no clustering</span></div>
<div class="row"><span class="k">state</span><span class="v">a <b>state</b> is a bag of partially-derived instances (PD-instances) whose unresolved frontier sits at the same level L(p); here L = 2 after stage 1</span></div>
<div class="row"><span class="k">MDL</span><span class="v">each state carries a cost: SRC for the schemas derived so far + DRC for the data they must encode. s₀,₁ costs 0; s₁,₁ ≈ small SRC (two primitive schemas) + DRC for 7 values</span></div></div>
<div class="callout plain" style="margin-top:12px">Only one child state here, because primitives leave nothing to choose. Choice appears at the next level, with objects.</div>''', icon="🔢") + "</div>"
frames.append(dict(step="Stage 1", text="The lowest level is resolved first: every primitive value becomes a primitive schema node. Arrays would be handled here too (generalized to a single ∗ edge, then clustered once).",
                   stage=stage("Stage 1", body, tabs(1), BN), status="STAGE 1"))

# F3 — stage 2: CD-instances and clustering
L2VALS = [T("val", '"jhyun"'), T("val", '"wshan"'), T("val", '"btak"')]
cd = [T("obj", "", [("age", T("sch", "NUM")), ("gender", T("sch", "STR"))], hl=True),
      T("obj", "", [("age", T("sch", "NUM")), ("gender", T("sch", "STR")), ("email", T("sch", "STR"))], hl=True),
      T("obj", "", [("age", T("sch", "NUM")), ("gender", T("sch", "STR"))], hl=True)]
dist = '''<table class="mx"><tr><th></th><th>c₁</th><th>c₂</th><th>c₃</th></tr>
<tr><th class="rowh">c₁</th><td class="dim">0</td><td>0.33</td><td class="max">0.00</td></tr>
<tr><th class="rowh">c₂</th><td>0.33</td><td class="dim">0</td><td>0.33</td></tr>
<tr><th class="rowh">c₃</th><td class="max">0.00</td><td>0.33</td><td class="dim">0</td></tr></table>'''
body = '<div class="cols c121">' + panel("CD-instances at level 2", f'<div class="fill" style="align-items:flex-start">{forest_svg(cd, titles=["c₁ (j₁.info)", "c₂ (j₂.info)", "c₃ (j₃.info)"], cols=2)}</div><div class="note" style="font-size:13px">A <b>CD-instance</b> ("children-derived") is an instance node whose descendants are all schema nodes. Because the children are schema IDs, each CD-instance is just a flat set of <b>(edge label, schema ID)</b> pairs.</div>', icon="🧩", tag="stage 2") + panel("Distance = Jaccard with partial credit", f'<div class="eq">D(c₁, c₂) = 1 − ( |E(c₁)∩E(c₂)| + |E<sub>S</sub>(c₁)∩E<sub>S</sub>(c₂)| ) / 2|E(c₁)∪E(c₂)|<br><span style="color:var(--ink-mute)">label match = 1 · label match with a different child schema = 0.5</span></div><div class="cols c2" style="flex:none;margin-top:10px;align-items:start"><div>{dist}</div><div class="note" style="font-size:13px">c₁ vs c₂: labels {{age, gender}} shared (2), both with the same child schemas (2), union of labels 3 → 1 − 4/6 = <b>0.33</b>. c₁ vs c₃: identical → <b>0</b>.</div></div><div class="callout info" style="margin-top:10px"><b>Two-phase DBSCAN.</b> Phase 1 (rare labels pre-generalized to ∗) finds homogeneous / composite clusters: {{c₁, c₃}} and c₂ as an outlier. Phase 2 clusters outliers after turning their labels into ∗, to find heterogeneous objects — with one outlier here, c₂ simply forms its own cluster.</div>', icon="📏") + panel("Level-2 primitives", f'<div class="fill" style="align-items:flex-start">{forest_svg(L2VALS, cols=3)}</div><div class="note" style="font-size:13px">"jhyun", "qwer", "wshan", "btak", "zxcv" → <b>STR</b>, as in stage 1. Objects and arrays at the same level go through clustering; primitives never do.</div>', icon="🔢") + "</div>"
frames.append(dict(step="Stage 2 · cluster", text="At level 2 the three <b>info</b> objects are CD-instances. They are clustered by a Jaccard-style distance over (key, child-schema) pairs: {c₁, c₃} together, c₂ apart.",
                   stage=stage("Clustering", body, tabs(1), BN), status="STAGE 2"))

# F4 — stage 2: candidate schema sets by repetitive generalization
body = '<div class="cols c3">' + panel("s₂,₁ · most specific (one schema per cluster)", f'<div class="fill" style="align-items:flex-start">{forest_svg([schema_tree("Sa"), schema_tree("Sb")], titles=["from {c₁, c₃}", "from {c₂}"], cols=1)}</div><div class="note" style="font-size:13px">Schema from a cluster: an <b>OBJ</b> node, one edge per label seen, <b>required</b> if present in every member, child = the single child schema (or an <b>ANYOF</b> of the distinct ones).</div>', icon="1️⃣") + panel("s₂,₂ · one viable merge", f'<div class="fill" style="align-items:flex-start">{forest_svg([schema_tree("Sm")], titles=["Sₐ ⊕ S_b"])}</div><div class="note" style="font-size:13px">Merge is <b>viable</b> because the two label sets overlap ({{age, gender}}). Hierarchical merging picks the pair with the smallest <b>ΔSRC</b>, i.e. the smallest jump in generality. <b>email</b> becomes optional (dashed).</div>', icon="2️⃣", cls="ok") + panel("s₂,₃ · fully generalized", f'<div class="fill" style="align-items:flex-start">{forest_svg([schema_tree("Sh")], titles=["heterogeneous"])}</div><div class="note" style="font-size:13px">All labels → <b>∗</b>, children → <b>ANYOF(NUM, STR)</b>: accepts any object whose values are numbers or strings. Cheap to write down, expensive to encode the data with.</div>', icon="3️⃣") + "</div>"
frames.append(dict(step="Stage 2 · generalize", text="From the clusters ReCG does not pick one schema set — it enumerates a spectrum, from the initial clusters to repeatedly merged (more general) ones. Each is a sibling state of stage 2.",
                   stage=stage("Generalization", body, tabs(1), BN), status="STAGE 2"))

# F5 — MDL
body = '<div class="cols c2">' + panel("MDL cost of the stage-2 states", bars([("s₂,₁", 48, 30, False), ("s₂,₂", 30, 34, True), ("s₂,₃", 14, 70, False)]) + '<div class="eq" style="margin-top:12px">cost(state) = <span class="hl">SRC</span>(schemas derived so far) + <span class="hl">DRC</span>(instances encoded with them)</div>', icon="⚖️") + panel("Why MDL", '''<div class="kv">
<div class="row"><span class="k">principle</span><span class="v">prefer the description that needs the fewest bits in total — a schema is a compression of its documents</span></div>
<div class="row"><span class="k">too specific</span><span class="v">s₂,₁ writes down two near-duplicate schemas (SRC high); data is cheap to encode</span></div>
<div class="row"><span class="k">too general</span><span class="v">s₂,₃ is tiny, but every key name and value type must now be spelled out per document (DRC high)</span></div>
<div class="row"><span class="k">balanced</span><span class="v">s₂,₂ shares one schema and pays a little for the optional key → lowest total</span></div>
<div class="row"><span class="k">beam</span><span class="v">breadth-first beam search with width 3 keeps the 3 cheapest states of each stage; here all three survive, ranked</span></div></div>
<div class="callout plain" style="margin-top:12px">In the paper MDL cost and F1 are strongly anti-correlated (−0.77) across datasets: the cheaper description really is the better schema.</div>''', icon="💡", cls="soft") + "</div>"
frames.append(dict(step="MDL", text="States compete on <b>minimum description length</b>: bits to write the schemas plus bits to write the data given the schemas. The balanced state wins.",
                   stage=stage("MDL cost", body, tabs(2), BN), status="MDL"))

# F6 — stage 3: roots
roots = [T("obj", "", [("id", T("sch", "STR")), ("pswd", T("sch", "STR")), ("info", T("sch", "OBJ Sₘ"))], hl=True),
         T("obj", "", [("name", T("sch", "STR")), ("info", T("sch", "OBJ Sₘ"))], hl=True),
         T("obj", "", [("id", T("sch", "STR")), ("pswd", T("sch", "STR")), ("info", T("sch", "OBJ Sₘ"))], hl=True)]
body = '<div class="cols c121">' + panel("Root CD-instances (continuing from s₂,₂)", f'<div class="fill" style="align-items:flex-start">{forest_svg(roots, titles=["r₁", "r₂", "r₃"], cols=2)}</div><div class="note" style="font-size:13px">Thanks to bottom-up order, all three carry the <b>same</b> child schema Sₘ under info. D(r₁, r₂) = 1 − (1+1)/(2·4) = <b>0.75</b> (only info in common) → clusters {{r₁, r₃}} and {{r₂}}.</div>', icon="🌳", tag="stage 3") + panel("Candidate states at stage 3", f'<div class="fill" style="align-items:flex-start">{forest_svg([schema_tree("S1"), schema_tree("S2")], titles=["s₃,₄ · S₁ (accounts)", "S₂ (name records)"], cols=2)}</div><div class="fill" style="align-items:flex-start;margin-top:4px">{forest_svg([schema_tree("S12")], titles=["s₃,₅ · S₁ ⊕ S₂ (merge, viable: info overlaps)"])}</div>', icon="🧩") + panel("Which one?", '''<div class="kv">
<div class="row"><span class="k">s₃,₄</span><span class="v">two schemas, both sharing Sₘ: SRC pays for two roots, DRC is minimal</span></div>
<div class="row"><span class="k">s₃,₅</span><span class="v">one root with id, pswd, name all <b>optional</b>: it also accepts {name, pswd} or {} — shapes never observed; DRC grows because every document must now say which keys it has</span></div>
<div class="row"><span class="k">MDL</span><span class="v">with the data at hand, s₃,₄ is cheaper → the final answer is <b>Z = {S₁, S₂}</b></span></div></div>
<div class="callout info" style="margin-top:12px">The viability rules make merges <b>possible</b> (labels overlap, or one cluster fits the other's ∗ pattern); MDL decides whether a merge is <b>worth it</b>.</div>''', icon="⚖️", cls="soft") + "</div>"
frames.append(dict(step="Stage 3", text="At the roots the same cluster → generalize → cost loop runs once more. Here the two-schema set beats the merged one: merging would admit key combinations nobody has seen.",
                   stage=stage("Stage 3", body, tabs(1), BN), status="STAGE 3"))

# F7 — search tree
costs = {"s0,1": "0", "s1,1": "10+55", "s2,1": "78", "s2,2": "64 ★", "s2,3": "84", "s3,1": "150", "s3,2": "171", "s3,3": "196", "s3,4": "138 ★", "s3,5": "151", "s3,6": "180", "s3,7": "205"}
body = '<div class="cols c21">' + panel("Search space · breadth-first beam search (width 3)", f'<div class="fill">{states_svg(hl=("s3,4",), beam=("s0,1", "s1,1", "s2,1", "s2,2", "s2,3", "s3,4", "s3,5", "s3,1"), costs=costs)}</div>', icon="🔍") + panel("Reading the tree", '''<div class="kv">
<div class="row"><span class="k">node</span><span class="v">a state s<sub>i,j</sub>: stage i, j-th sibling; label = MDL cost so far (illustrative)</span></div>
<div class="row"><span class="k">children</span><span class="v">GenerateChildrenStates: cluster the CD-instances once, then repetitively generalize → a spectrum of sibling states</span></div>
<div class="row"><span class="k">beam</span><span class="v">at each stage only the 3 cheapest states are expanded (purple); the rest are pruned</span></div>
<div class="row"><span class="k">goal</span><span class="v">a leaf where every PD-instance is fully derived (L(p) = 0); the cheapest such leaf, <b>s₃,₄</b>, is returned</span></div></div>
<div class="callout plain" style="margin-top:12px">Stage count = height of the tallest document: three levels here, so three stages. Real datasets (Wikidata, Twitter, …) have deeper trees and far more siblings per stage — this is where the beam matters.</div>''', icon="🗺️") + "</div>"
frames.append(dict(step="Search", text="The whole run is a beam search over states: each stage clusters, generalizes into siblings, scores them with MDL and keeps the best three.",
                   stage=stage("Search", body, tabs(2), BN), status="SEARCH"))

# F8 — output
schema_json = '''{ "anyOf": [
    { "type": "object",
      "properties": { "id": {"type": "string"}, "pswd": {"type": "string"},
                      "info": {"$ref": "#/$defs/info"} },
      "required": ["id", "pswd", "info"] },
    { "type": "object",
      "properties": { "name": {"type": "string"}, "info": {"$ref": "#/$defs/info"} },
      "required": ["name", "info"] } ],
  "$defs": { "info": { "type": "object",
      "properties": { "age": {"type": "number"}, "gender": {"type": "string"},
                      "email": {"type": "string"} },
      "required": ["age", "gender"] } } }'''
checks = "".join(f'<div class="hslot"><div class="hrow {c}"><span class="hid">{k}</span><span class="hres mono">{d}</span><span class="hmark">{m}</span></div></div>' for k, d, c, m in [
    ("D⁺", '{"id": "jhyun", "pswd": "qwer", "info": {…}}', "ok", "✓ accepted"), ("D₂⁺", '{"id": "yoon", "pswd": "1q2w", "info": {"age": 31, "gender": "f"}}', "ok", "✓ unseen, accepted"),
    ("D₂⁺", '{"name": "han", "info": {"age": 50, "gender": "m", "email": "h@a.kr"}}', "ok", "✓ optional email"), ("D⁻", '{"name": "x", "pswd": "y"}', "fail", "✗ rejected"), ("D⁻", '{"id": "a", "pswd": "b", "info": {"age": "old"}}', "fail", "✗ age not a number")])
body = '<div class="cols c2">' + panel("Discovered schema set Z = {S₁, S₂} as JSON Schema", json_pre("output", schema_json), icon="📤") + panel("What the schema does with new documents", f'<div class="hist">{checks}</div><div class="callout ok" style="margin-top:12px">High recall on unseen positives (optional email, any values of the right type) and high precision on negatives (missing keys, wrong types) — the two halves of the F1 that ReCG is evaluated on.</div>', icon="🧪") + "</div>"
frames.append(dict(step="Output", text="The result is an ordinary JSON Schema set: two document types sharing one <b>info</b> definition with an optional key.",
                   stage=stage("Output", body, tabs(3), BN), status="DONE"))

# F9 — why it works
stats = "".join(f'<div class="stat"><div class="n">{n}</div><div class="l">{l}</div></div>' for n, l in [
    ("+46 %", "F1 over Jxplain, the previous state of the art"), ("+47 % / +18 %", "recall / precision gains over Jxplain (up to)"),
    ("1.54–2.11×", "faster than Jxplain, depending on dataset size"), ("≈ 2×", "slower than KReduce — the price of exploring candidates"),
    ("−0.77", "correlation between MDL cost and F1 across datasets"), ("20", "datasets: 12 real-world + 8 synthetic from JSON Schema Store")])
body = '<div class="cols c12">' + panel("Three ideas", '''<div class="kv">
<div class="row"><span class="k">bottom-up</span><span class="v">children are schema IDs before parents are decided, so parents are compared on <b>resolved</b> structure</span></div>
<div class="row"><span class="k">search</span><span class="v">clustering gives the most specific schema set; <b>repetitive generalization</b> enumerates more general ones; beam search keeps it tractable</span></div>
<div class="row"><span class="k">MDL</span><span class="v">one cost (schema bits + data bits) ranks candidates without labels or thresholds on generality</span></div></div>
<div class="callout plain" style="margin-top:14px">Known limits (from the paper): tiny homogeneous groups can be mistaken for outliers and over-generalized; stages with very many clusters get slow.</div>''', icon="✦", cls="soft") + panel("Numbers from the paper (PVLDB 2024)", f'<div class="cols c3" style="flex:1;align-content:start">{stats}</div><div class="note" style="margin-top:10px;font-size:12.5px;color:var(--ink-mute)">Compared with Jxplain, KReduce, LReduce, KSS and FMC · ReCG in C++ · default beam width 3.</div>', icon="📈") + "</div>"
frames.append(dict(step="✦ Why it works", text="Informed decisions (bottom-up), a spectrum of candidates (cluster-and-generalize) and a principled judge (MDL) — each fixes one failure of top-down discovery.",
                   stage=stage("Why it works", body, tabs(3, interm=True), BN), status="SUMMARY", interm=True))

META = dict(
    title="ReCG — Worked Example",
    eyebrow="ReCG · PVLDB 2024 · Worked Example",
    h1='Discovering a JSON schema <span class="hl">from the leaves up</span>',
    intro=("ReCG infers a set of JSON schemas from documents alone. It resolves instance trees bottom-up, clusters the partially "
           "derived objects at each level, generalizes the clusters into a spectrum of candidate schema sets, and lets the minimum "
           "description length principle pick the winner inside a beam search. Step through one small collection below."),
    qicon="{ }", question=Q_HTML, alabel="OUTPUT", answer=ANSWER,
)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "recg_worked_example.html")
    write(out, render(META, frames))
