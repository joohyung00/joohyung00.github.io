"""LILaC worked example — frames. Running example follows Figure 1 of the paper (Shah Jahan → Taj Mahal)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen import *

# ------------------------------------------------------------------ running example data
Q_HTML = ('In the <em>mausoleum built by the Mughal emperor who married Mumtaz&nbsp;Mahal</em>, how many '
          '<em>slender minarets</em> surround the central dome?')
ANSWER = "Four"
SUBQ = [("q₁", "Mughal emperor who married Mumtaz Mahal", "text"),
        ("q₂", "the mausoleum that emperor built", "text"),
        ("q₃", "number of slender minarets around the central dome", "image")]
MOD_CLS = {"text": "txt", "table": "tbl", "image": "img"}
MOD_ICON = {"text": "¶", "table": "⊞", "image": "🖼"}

# documents: (id, title, components); component: (cid, modality, title, subcomponents)
DOCS = [
    ("D₁", "Shah Jahan", [
        ("C₁,₁", "text", "lead paragraph", ["s₁ Shah Jahan was the fifth Mughal emperor (r. 1628–1658).", "s₂ He commissioned the Taj Mahal for his wife Mumtaz Mahal."]),
        ("C₁,₂", "image", "portrait", ["o₁ man", "o₂ turban"]),
        ("C₁,₃", "table", "infobox", ["r₁ Reign · 1628–1658", "r₂ Spouse · Mumtaz Mahal"]),
    ]),
    ("D₂", "Taj Mahal", [
        ("C₂,₁", "text", "lead paragraph", ["s₁ The Taj Mahal is an ivory-white marble mausoleum in Agra.", "s₂ It was commissioned in 1631 by Shah Jahan."]),
        ("C₂,₂", "image", "photo", ["o₁ central dome", "o₂ minaret ×4"]),
        ("C₂,₃", "table", "infobox", ["r₁ Location · Agra", "r₂ Height · 73 m"]),
    ]),
    ("D₃", "Mumtaz Mahal", [
        ("C₃,₁", "text", "lead paragraph", ["s₁ Mumtaz Mahal was the chief consort of Shah Jahan.", "s₂ She died in 1631 in Burhanpur."]),
        ("C₃,₂", "image", "portrait", ["o₁ woman"]),
        ("C₃,₃", "table", "infobox", ["r₁ Spouse · Shah Jahan"]),
    ]),
]
LINKS = [("C₁,₁", "D₂"), ("C₁,₁", "D₃")]   # link mapping L: paragraph C1,1 hyperlinks to the Taj Mahal and Mumtaz Mahal pages

COARSE_SIM = {"C₁,₁": .71, "C₃,₁": .66, "C₂,₁": .58, "C₁,₃": .52, "C₃,₃": .47, "C₂,₂": .41, "C₂,₃": .33, "C₁,₂": .22, "C₃,₂": .20}
EDGE_SCORES = [  # one-hop expansion from {C1,1, C3,1}: edge, score, (q1,q2,q3 maxima)
    (("C₁,₁", "C₂,₂"), 2.32, (.82, .64, .86)), (("C₁,₁", "C₂,₁"), 1.82, (.82, .79, .21)),
    (("C₁,₁", "C₁,₂"), 1.76, (.82, .64, .30)), (("C₁,₁", "C₂,₃"), 1.72, (.82, .64, .26)),
    (("C₁,₁", "C₃,₂"), 1.71, (.82, .64, .25)), (("C₁,₁", "C₃,₁"), 1.66, (.82, .64, .20)),
    (("C₁,₁", "C₃,₃"), 1.66, (.82, .64, .20)), (("C₁,₁", "C₁,₃"), 1.64, (.82, .64, .18)),
    (("C₃,₁", "C₃,₂"), 1.29, (.74, .31, .24)), (("C₃,₁", "C₃,₃"), 1.24, (.74, .30, .20)),
]
B = 2

TABS = ["Offline · Layered graph", "Online · Decompose", "Online · Traverse", "Result"]


def tabs(active, interm=False):
    out = []
    for i, t in enumerate(TABS):
        out.append((t, "active" if i == active else ""))
    if interm:
        out = [(t, "") for t, _ in out] + [("✦ Why it works", "intermission")]
    return out


def subq_chips(active=None, solved=()):
    rows = []
    for qid, body, mod in SUBQ:
        cls = "subq" + (" active" if qid == active else "") + (" solved" if qid in solved else "")
        st = f'<span class="status">{MOD_ICON[mod]} {mod}</span>'
        rows.append(f'<div class="{cls}"><span class="qid">{qid}</span><span class="qbody">{body}</span>{st}</div>')
    return "".join(rows)


# ------------------------------------------------------------------ graph drawing
# layout: 3 documents side by side; coarse row at y=CY, fine rows below; link arcs run above the documents.
DX = {"D₁": 20, "D₂": 420, "D₃": 820}
DW, DY, DH = 384, 44, 206
CW, CH, CY = 114, 60, 86
FW, FH = 114, 26


def coarse_pos(cid):
    d = "D" + cid[1]
    k = ["₁", "₂", "₃"].index(cid[3])
    return DX[d] + 16 + k * 122, CY


def graph_svg(fine=True, intra=False, inter=False, hi=(), hi_edges=(), edge_labels=None, dim_rest=False, ring=(), beam_nodes=(), hi_fine=()):
    """hi: coarse node ids to highlight; hi_edges: list of (a,b); edge_labels: {(a,b): text}; ring: nodes with a
    dashed ring; hi_fine: fine node keys 'C₁,₁/1' (0-based index) to highlight."""
    W, H = 1224, 262
    g = [ARROW_DEFS]
    for did, title, comps in DOCS:
        x = DX[did]
        g.append(f'<rect x="{x}" y="{DY}" width="{DW}" height="{DH}" rx="16" fill="#FCFBFF" stroke="#E5E0F2" stroke-width="1.5"/>')
        g.append(text(x + 16, DY + 24, f"{did} · {title}", fs=14.5, color="#6D28D9", weight=700))
    labels = dict(edge_labels or {})
    def lab_at(mx, my, s):
        g.append(f'<rect x="{mx - 25}" y="{my - 10}" width="50" height="20" rx="6" fill="#fff" stroke="#C4B5FD"/>')
        g.append(text(mx, my + 4.5, s, fs=12.5, color="#6D28D9", anchor="middle", weight=700, mono=True))
    if intra:
        for did, _, comps in DOCS:
            ids = [c[0] for c in comps]
            for i in range(3):
                for j in range(i + 1, 3):
                    (x1, y1), (x2, y2) = coarse_pos(ids[i]), coarse_pos(ids[j])
                    on = (ids[i], ids[j]) in hi_edges or (ids[j], ids[i]) in hi_edges
                    g.append(line(x1 + CW / 2, y1 + CH / 2, x2 + CW / 2, y2 + CH / 2, stroke="#8B5CF6" if on else "#C4B5FD", sw=3 if on else 1.5, opacity=1 if on or not dim_rest else .45))
    if inter:
        for src, dst in LINKS:
            sx, sy = coarse_pos(src)
            for did, _, comps in DOCS:
                if did != dst:
                    continue
                for cid, *_ in comps:
                    tx, ty = coarse_pos(cid)
                    on = (src, cid) in hi_edges or (cid, src) in hi_edges
                    peak = 10 if dst == "D₂" else 4
                    g.append(f'<path d="M{sx + CW},{sy + 6} C {sx + CW + 60},{peak} {tx - 60},{peak} {tx + 8},{ty - 2}" fill="none" stroke="{"#3B82F6" if on else "#93C5FD"}" stroke-width="{3 if on else 1.4}" stroke-dasharray="{"" if on else "5 4"}" opacity="{1 if on or not dim_rest else .4}" marker-end="url(#arr)"/>')
    for did, _, comps in DOCS:
        for cid, mod, ttl, subs in comps:
            x, y = coarse_pos(cid)
            on = cid in hi
            fill = {"text": "#EEF2FF", "image": "#FDF2F8", "table": "#ECFDF5"}[mod]
            stroke = {"text": "#C7D2FE", "image": "#FBCFE8", "table": "#A7F3D0"}[mod]
            sw = 1.5
            if on:
                stroke, sw = "#7C3AED", 3
            op = .4 if (dim_rest and not on and cid not in beam_nodes) else 1
            if cid in ring:
                g.append(f'<rect x="{x - 6}" y="{y - 6}" width="{CW + 12}" height="{CH + 12}" rx="16" fill="none" stroke="#A78BFA" stroke-width="2" stroke-dasharray="4 3"/>')
            g.append(f'<g opacity="{op}">' + box(x, y, CW, CH, f"{MOD_ICON[mod]} {cid}", ttl, fill=fill, stroke=stroke, sw=sw, fs=15) + "</g>")
            if fine:
                for k, s_ in enumerate(subs):
                    fx, fy = x, y + CH + 22 + k * (FH + 6)
                    key = f"{cid}/{k}"
                    fon = key in hi_fine
                    g.append(line(x + CW / 2, y + CH, fx + FW / 2, fy, stroke="#D8D0F0", sw=1.2))
                    body = s_.split(" ", 1)
                    txt = body[0] + " " + (body[1][:19] + "…" if len(body[1]) > 20 else body[1])
                    g.append(f'<g opacity="{op}">' + box(fx, fy, FW, FH, txt, fill="#fff" if not fon else "#EDE9FE", stroke="#E5E0F2" if not fon else "#7C3AED", sw=2 if fon else 1.2, r=7, fs=10.5, bold=fon, color="#4C4880") + "</g>")
    for (a, b), s_ in labels.items():
        (x1, y1), (x2, y2) = coarse_pos(a), coarse_pos(b)
        if a[1] == b[1]:   # intra: label just under the coarse row, between the two nodes
            lab_at((x1 + x2) / 2 + CW / 2, y1 + CH + 9, s_)
        else:              # inter: on the arc apex
            peak = 10 if b[1] == "₂" else 4
            lab_at((x1 + CW + x2) / 2, peak + 12, s_)
    g.append(text(6, CY + 40, "V₀ · coarse", fs=11, color="#8B86B5", mono=True, extra=f'transform="rotate(-90 6 {CY + 40})" '))
    if fine:
        g.append(text(6, 236, "V₁ · fine", fs=11, color="#8B86B5", mono=True, extra='transform="rotate(-90 6 236)" '))
    return svg(W, H, "".join(g))


def doc_cards():
    cards = []
    for did, title, comps in DOCS:
        rows = "".join(f'<div class="subq"><span class="qid">{cid}</span><span class="qbody">{ttl}</span><span class="chip {MOD_CLS[mod]}">{MOD_ICON[mod]} {mod}</span></div>' for cid, mod, ttl, _ in comps)
        links = ", ".join(d for s, d in LINKS if s.startswith("C" + did[1]))
        lk = f'<div class="note" style="font-size:12.5px;margin-top:4px">links → <b>{links}</b> (from {[s for s, d in LINKS if s.startswith("C" + did[1])][0]})</div>' if links else '<div class="note" style="font-size:12.5px;margin-top:4px;color:var(--ink-mute)">no outgoing links</div>'
        cards.append(f'<div class="panel"><div class="panel-title">📄 {did} · {title}</div>{rows}{lk}</div>')
    return '<div class="cols c3" style="flex:none">' + "".join(cards) + "</div>"


# ------------------------------------------------------------------ frames
frames = []
BN = banner(Q_HTML, ANSWER)

# F0 — setup
body = doc_cards() + '<div class="cols c2" style="flex:1">' + panel("The retrieval task", f'''<div class="note">
<p>Corpus <b>𝒟</b> = multimodal documents; each document <b>D = [C₁, …, C<sub>k</sub>]</b> is a sequence of <span class="em">components</span>, each a paragraph <b>P</b>, a table <b>T</b>, or an image <b>I</b>.
A link mapping <b>L : C → D</b> records hyperlinks from a component to another document.</p>
<p style="margin-top:8px">Given query <b>Q</b>, return a ranked list of components <b>R = [C₁, …, C<sub>n</sub>]</b> that contains the ground-truth components. Here the answer lives in <b>C₂,₂</b>, the Taj Mahal photo, two hops from the words in the query.</p></div>''', icon="🎯") + panel("Why earlier pipelines miss it", '''<div class="kv">
<div class="row"><span class="k">TextRAG</span><span class="v">summarizes the photo into text; the summary may drop the word <b>minarets</b> — information loss.</span></div>
<div class="row"><span class="k">VisRAG</span><span class="v">embeds whole page screenshots; the relevant region is a small part of a screenshot, and screenshots are retrieved independently, so the <b>link</b> Shah Jahan → Taj Mahal is never used.</span></div>
<div class="row"><span class="k">LILaC</span><span class="v">keeps components and their links in a <b>layered graph</b>, decomposes the query by modality, and scores edges with fine-grained <b>late interaction</b>.</span></div></div>''', icon="⚠️", cls="soft") + "</div>"
frames.append(dict(step="Setup", text="Three Wikipedia-style documents, each a sequence of paragraph / image / table components; one paragraph hyperlinks to the other two pages.",
                   stage=stage("Setup", body, tabs(0), BN), status="SETUP"))

# F1 — component trees
body = '<div class="cols stack">' + panel("Layered component graph · component trees (E↓)", f'<div class="fill">{graph_svg(fine=True)}</div>', icon="🕸", tag="offline") + panel("Fine-grained layer V₁", '''<div class="cols c2"><div class="kv">
<div class="row"><span class="k">¶ paragraph</span><span class="v">split into sentences with a Sentence-aware Transformer (SaT) → <b>V<sub>sent</sub></b></span></div>
<div class="row"><span class="k">⊞ table</span><span class="v">every data row becomes a two-row segment [header; row] → <b>V<sub>row</sub></b></span></div>
<div class="row"><span class="k">🖼 image</span><span class="v">a multimodal LLM detects objects; each bounding-box patch is a node → <b>V<sub>obj</sub></b></span></div>
<div class="row"><span class="k">E↓</span><span class="v">containment edges (C, c) for every subcomponent c ∈ S(C)</span></div></div>
<div class="callout plain">Two granularities on purpose: the coarse layer <b>V₀</b> gives context for cheap candidate generation; the fine layer <b>V₁</b> gives precise evidence for scoring. Nothing is summarized away — the photo stays a photo, its detected objects become nodes.</div></div>''', icon="🔬") + "</div>"
frames.append(dict(step="Offline · 1", text="Every component becomes a two-level <b>component tree</b>: sentences under a paragraph, header+row segments under a table, detected objects under an image.",
                   stage=stage("Component trees", body, tabs(0), BN), status="OFFLINE"))

# F2 — inter-component edges
body = '<div class="cols stack">' + panel("Layered component graph · inter-component edges (E₀)", f'<div class="fill">{graph_svg(intra=True, inter=True)}</div>', icon="🕸", tag="offline") + panel("Top layer edges E₀ = E<sub>intra</sub> ∪ E<sub>inter</sub>", '''<div class="cols c2"><div><div class="eq">E<sub>intra</sub> = {(C<sub>i</sub>, C<sub>j</sub>) | C<sub>i</sub> ≠ C<sub>j</sub> ∈ D}<br>E<sub>inter</sub> = {(C, C′) | (C, D) ∈ L, C′ ∈ D}</div>
<div class="callout info" style="margin-top:10px">Edges carry no committed semantics — they only say "these may belong together". Which ones matter is decided per query, online.</div></div>
<div class="kv"><div class="row"><span class="k">clique</span><span class="v">all components of one document are pairwise connected (purple) — within-document context is one hop away</span></div>
<div class="row"><span class="k">link edges</span><span class="v">C₁,₁ hyperlinks to D₂ and D₃, so it is connected to <b>every</b> component of those pages (blue, dashed)</span></div>
<div class="row"><span class="k">embeddings</span><span class="v">every node v ∈ V₀ ∪ V₁ gets <b>v = f(v)</b> from a pre-trained multimodal embedder (MM-Embed here); edges are <b>not</b> embedded</span></div></div></div>''', icon="🔗") + "</div>"
frames.append(dict(step="Offline · 2", text="Coarse nodes are linked by a clique inside each document and by hyperlink edges across documents; then every node is embedded once.",
                   stage=stage("Inter-component edges", body, tabs(0), BN), status="OFFLINE"))

# F3 — query decomposition
body = '<div class="cols c121">' + panel("Query", f'<div class="note"><p>{Q_HTML}</p><p style="margin-top:10px">One query, two documents, three kinds of evidence. A single embedding of Q has to match a paragraph, a hyperlink hop and an <b>image</b> at once.</p></div><div class="callout plain" style="margin-top:14px">Q is also embedded <b>coarsely</b> (no modality instruction) → <b>Q</b> = f(Q; ε), used only to seed the search.</div>', icon="❓") + panel("LLM-driven decomposition → modality-specific subqueries", f'<div class="mem-section-label">prompt<sub>dec</sub> → subqueries</div>{subq_chips()}<div class="mem-section-label" style="margin-top:12px">prompt<sub>mod</sub> → modality label m<sub>j</sub> ∈ {{text, table, image}}</div><div class="note">Each subquery is embedded <b>with</b> its modality as the instruction: <span class="eq" style="display:inline-block;padding:4px 10px">q<sub>j</sub> = f(q<sub>j</sub>; m<sub>j</sub>)</span> — this is what multimodal embedders were trained for, but queries rarely state their modality.</div>', icon="🧩", tag="zero-shot") + panel("Why decompose", '''<div class="kv">
<div class="row"><span class="k">evidence</span><span class="v">each subquery names one fine-grained piece of evidence, so it can match one sentence / row / object</span></div>
<div class="row"><span class="k">modality</span><span class="v">q₃ is an <b>image</b> question; its embedding is steered toward visual nodes</span></div>
<div class="row"><span class="k">cost</span><span class="v">the LLM prompts are the dominant online cost (≈1.4 s per query); everything after runs in milliseconds</span></div></div>''', icon="💡", cls="soft") + "</div>"
frames.append(dict(step="Online · 1", text="The query is decomposed by an LLM into three subqueries, each classified into a modality that becomes the embedding instruction.",
                   stage=stage("Query decomposition", body, tabs(1), BN), status="ONLINE"))

# F4 — initial candidates
bars = "".join(f'<div class="row" style="align-items:center"><span class="k" style="min-width:56px">{cid}</span><span class="v" style="flex:1"><span style="display:inline-block;height:13px;border-radius:7px;background:{"#8B5CF6" if i < B else "#DDD6FE"};width:{int(s * 260)}px;vertical-align:middle"></span> <span class="mono" style="font-size:12.5px;color:{"#6D28D9" if i < B else "#8B86B5"}">{s:.2f}</span></span></div>' for i, (cid, s) in enumerate(sorted(COARSE_SIM.items(), key=lambda t: -t[1])[:6]))
body = '<div class="cols stack">' + panel("Initial candidate node search", f'<div class="fill">{graph_svg(intra=True, inter=True, hi=("C₁,₁", "C₃,₁"), dim_rest=True)}</div>', icon="🎯", tag=f"b = {B}") + panel("sim(Q, C) over the coarse layer", f'<div class="cols c2"><div><div class="eq">V₀⁽⁰⁾ = argmax<sup>b</sup><sub>C ∈ V₀</sub> sim(<b>Q</b>, <b>C</b>), &nbsp; E⁽⁰⁾ = ∅</div><div class="callout plain" style="margin-top:10px">Coarse embeddings are good enough to find <b>where to start</b>: the Shah Jahan paragraph and the Mumtaz Mahal paragraph. They are not asked to find the answer.</div></div><div class="kv">{bars}</div></div>', icon="📊") + "</div>"
frames.append(dict(step="Online · 2", text=f"Seed: the top-b (b = {B}) coarse nodes by similarity to the whole query — one nearest-neighbour search over V₀, nothing else.",
                   stage=stage("Initial candidates", body, tabs(2), BN), status="ONLINE"))

# F5 — one-hop expansion
labels = {e: f"{s:.2f}" for e, s, _ in EDGE_SCORES[:6] if e[0][1] != e[1][1]}
rows = "".join(f'<div class="hslot"><div class="hrow {"ok" if i < B else ""}"><span class="hid">e{i + 1}</span><span class="hq">{a} — {b}</span><span class="hres">q₁ {m[0]:.2f} · q₂ {m[1]:.2f} · q₃ {m[2]:.2f}</span><span class="hmark mono" style="color:{"#10B981" if i < B else "#8B86B5"}">{s:.2f}</span></div></div>' for i, ((a, b), s, m) in enumerate(EDGE_SCORES[:8]))
half = len(EDGE_SCORES[:8]) // 2
rows_a = "".join(f'<div class="hslot"><div class="hrow {"ok" if i < B else ""}"><span class="hid">e{i + 1}</span><span class="hq">{a} — {b}</span><span class="hres">q₁ {m[0]:.2f} · q₂ {m[1]:.2f} · q₃ {m[2]:.2f}</span><span class="hmark mono" style="color:{"#10B981" if i < B else "#8B86B5"}">{s:.2f}</span></div></div>' for i, ((a, b), s, m) in enumerate(EDGE_SCORES[:8]) if i < 4)
rows_b = "".join(f'<div class="hslot"><div class="hrow"><span class="hid">e{i + 1}</span><span class="hq">{a} — {b}</span><span class="hres">q₁ {m[0]:.2f} · q₂ {m[1]:.2f} · q₃ {m[2]:.2f}</span><span class="hmark mono" style="color:#8B86B5">{s:.2f}</span></div></div>' for i, ((a, b), s, m) in enumerate(EDGE_SCORES[:8]) if i >= 4)
body = '<div class="cols stack">' + panel("One-hop node expansion", f'<div class="fill">{graph_svg(intra=True, inter=True, hi=("C₁,₁", "C₃,₁"), hi_edges=[e for e, *_ in EDGE_SCORES[:2]], edge_labels=labels, dim_rest=True, hi_fine=("C₁,₁/1", "C₂,₂/1", "C₂,₁/1"))}</div>', icon="↔", tag="iteration 1") + panel("Candidate edges, scored on the fly", f'<div class="cols c2"><div class="hist">{rows_a}</div><div class="hist">{rows_b}<div class="note" style="font-size:13px;padding-top:6px">… 10 candidate edges in total. Only the top-<b>b</b> are kept (green); their endpoints become the next candidate set.</div></div></div>', icon="🧮") + "</div>"
frames.append(dict(step="Online · 3", text="From the seeds, every incident edge is a candidate; each edge gets a relevance score computed <b>now</b>, from fine-grained nodes — no edge embeddings exist.",
                   stage=stage("One-hop expansion", body, tabs(2), BN), status="ONLINE"))

# F6 — edge-level late interaction (matrices)
def matrix(cols, rows, maxcols, total):
    th = "".join(f"<th>{c}</th>" for c in cols)
    body = ""
    for (q, vals), mi in zip(rows, maxcols):
        tds = "".join(f'<td class="{"max" if k == mi else ""}">{v:.2f}</td>' for k, v in enumerate(vals))
        body += f'<tr><th class="rowh">{q}</th>{tds}<td class="{"sum" if q == "Σ" else "dim"}" style="background:none"></td></tr>'
    body += f'<tr><th class="rowh">s(e)</th>{"<td class=dim></td>" * len(cols)}<td class="sum">{total:.2f}</td></tr>'
    return f'<table class="mx"><tr><th></th>{th}<th></th></tr>{body}</table>'
m1 = matrix(["C₁,₁·s₁", "C₁,₁·s₂", "C₂,₂·o₁ dome", "C₂,₂·o₂ minarets"], [("q₁", [.55, .82, .12, .10]), ("q₂", [.41, .64, .33, .20]), ("q₃", [.08, .11, .72, .86])], [1, 1, 3], 2.32)
m2 = matrix(["C₃,₁·s₁", "C₃,₁·s₂", "C₃,₂·o₁ woman"], [("q₁", [.74, .40, .15]), ("q₂", [.31, .22, .15]), ("q₃", [.10, .07, .24])], [0, 0, 2], 1.29)
body = '<div class="cols c2">' + panel("e₁ = (C₁,₁, C₂,₂) · Shah Jahan paragraph — Taj Mahal photo", f'<div class="fill" style="align-items:flex-start">{m1}</div><div class="callout ok" style="margin-top:8px">Every subquery finds a strong subcomponent on one side of the edge: q₁, q₂ in the sentence about Mumtaz Mahal, q₃ in the detected <b>minaret</b> objects. <b>s(e₁) = 0.82 + 0.64 + 0.86 = 2.32</b></div>', icon="✅") + panel("e₉ = (C₃,₁, C₃,₂) · Mumtaz Mahal paragraph — portrait", f'<div class="fill" style="align-items:flex-start">{m2}</div><div class="callout fail" style="margin-top:8px">q₁ matches, but nothing here answers q₂ or q₃. <b>s(e₉) = 0.74 + 0.31 + 0.24 = 1.29</b> — the edge is dropped even though its paragraph was a seed.</div>', icon="✗") + "</div>" + '<div class="eq" style="flex:none;margin-top:4px">s(e; Q<sub>sub</sub>) = Σ<sub>q ∈ Q<sub>sub</sub></sub> <span class="hl">max<sub>c ∈ S<sub>e</sub></sub> sim(f(c), q)</span>, &nbsp; S<sub>e</sub> = S(C<sub>α</sub>) ∪ S(C<sub>β</sub>) &nbsp;— inner max: the single best subcomponent incident to the edge per subquery; outer sum: every subquery counts exactly once.</div>'
frames.append(dict(step="Online · 4", text="<b>Edge-level late interaction</b>: an edge is scored by matching each subquery against the subcomponents hanging off both endpoints, then summing the per-subquery maxima. (Similarities here are illustrative.)",
                   stage=stage("Late interaction", body, tabs(2), BN), status="ONLINE"))

# F7 — beam & iteration 2
body = '<div class="cols stack">' + panel("Beam keeps the top-b edges → subgraph 𝒢₁ → expand again", f'<div class="fill">{graph_svg(intra=True, inter=True, hi=("C₁,₁", "C₂,₂", "C₂,₁"), hi_edges=[("C₁,₁", "C₂,₂"), ("C₁,₁", "C₂,₁")], edge_labels={("C₁,₁", "C₂,₂"): "2.32", ("C₁,₁", "C₂,₁"): "1.82", ("C₂,₁", "C₂,₂"): "2.23"}, dim_rest=True, ring=("C₂,₁", "C₂,₂"), hi_fine=("C₁,₁/1", "C₂,₂/1", "C₂,₁/1"))}</div>', icon="🔁", tag="iteration 2 of n_i") + panel("Iteration 2 · and two special cases", '''<div class="cols c2"><div class="kv">
<div class="row"><span class="k">𝒢₁</span><span class="v">E₁ = {e₁, e₂}; V₁ = {C₁,₁, C₂,₂, C₂,₁} — the Taj Mahal page has been reached through the link edge</span></div>
<div class="row"><span class="k">expand</span><span class="v">incident edges of V₁ are scored; the intra-document edge (C₂,₁, C₂,₂) now scores 2.23 (q₂ via "commissioned in 1631 by Shah Jahan", q₃ via the minarets)</span></div>
<div class="row"><span class="k">beam</span><span class="v">top-b again → 𝒢₂ = {(C₁,₁, C₂,₂), (C₂,₁, C₂,₂)}; after n<sub>i</sub> iterations the final subgraph 𝒢<sub>n<sub>i</sub></sub> is returned</span></div></div>
<div class="kv"><div class="row"><span class="k">isolated node</span><span class="v">a component with no neighbour gets a dummy edge (C, ε) so it can still be scored</span></div>
<div class="row"><span class="k">one-sided match</span><span class="v">if s(e) equals the best single-node score of one endpoint, only that node is returned — the neighbour contributed nothing</span></div></div></div>''', icon="📐") + "</div>"
frames.append(dict(step="Online · 5", text="Beam search over edges: keep the b best edges, make their endpoints the new candidates, repeat for n<sub>i</sub> iterations. The search never scores more than a few dozen edges.",
                   stage=stage("Beam iterations", body, tabs(2), BN), status="ONLINE"))

# F8 — result
res = "".join(f'<div class="subq {"solved" if i == 0 else ""}"><span class="qid">#{i + 1}</span><span class="qbody"><b>{cid}</b> · {ttl}</span><span class="chip {MOD_CLS[mod]}">{MOD_ICON[mod]} {mod}</span></div>' for i, (cid, mod, ttl) in enumerate([("C₂,₂", "image", "Taj Mahal photo — minaret ×4, central dome"), ("C₁,₁", "text", "Shah Jahan paragraph — "+"\"…for his wife Mumtaz Mahal\""), ("C₂,₁", "text", "Taj Mahal paragraph — \"commissioned in 1631 by Shah Jahan\"")]))
body = '<div class="cols c121">' + panel("Ranked components R (top-n<sub>ret</sub> nodes of 𝒢<sub>n<sub>i</sub></sub>)", res + '<div class="note" style="margin-top:8px;font-size:13px">Nodes of the final subgraph are ranked by their late-interaction evidence; the three best go to the generator.</div>', icon="📦") + panel("Generator (Qwen2.5-VL 7B) reads the three components", f'<div class="fill" style="flex-direction:column;gap:14px"><div class="big">Four<small>minarets surround the central dome</small></div><div class="callout ok">The answer is read off the <b>image</b> component. It was reachable only because (1) the Shah Jahan paragraph is linked to the Taj Mahal page and (2) q₃ was embedded as an image question and matched the detected minarets.</div></div>', icon="🤖") + panel("Same query, other pipelines", '''<div class="kv">
<div class="row"><span class="k">TextRAG</span><span class="v">photo → caption "white marble mausoleum"; <b>minarets</b> never appear in the index</span></div>
<div class="row"><span class="k">VisRAG</span><span class="v">top screenshot = Shah Jahan page (query words); the Taj Mahal screenshot is never reached — no hop</span></div>
<div class="row"><span class="k">LILaC</span><span class="v">hop along the link, score the edge with the image's own objects ✓</span></div></div>''', icon="⚖️", cls="soft") + "</div>"
frames.append(dict(step="Result", text="The final subgraph's nodes are returned as a ranked list; the multimodal LLM answers from the Taj Mahal photo.",
                   stage=stage("Result", body, tabs(3), BN), status="DONE"))

# F9 — why it works
stats = "".join(f'<div class="stat"><div class="n">{n}</div><div class="l">{l}</div></div>' for n, l in [
    ("+14.2 / +11.6", "Recall@3 over VisRAG-Ret / ColPali, averaged over 5 benchmarks"), ("+15.8 / +11.7", "MRR@10 over VisRAG-Ret / ColPali"),
    ("5 / 5", "benchmarks where LILaC is SOTA, with no fine-tuning"), ("48 ms", "late-interaction subgraph retrieval, ≈1.5 % of runtime"),
    ("1,423 ms", "query decomposition — the online bottleneck"), ("+7.3 → +3.2", "R@3 gain from the layered graph, then from decomposition + late interaction (ablation)")])
body = '<div class="cols c12">' + panel("Three ideas, one per failure mode", '''<div class="kv">
<div class="row"><span class="k">granularity</span><span class="v"><b>two layers</b>: coarse nodes to find candidates cheaply, fine nodes (sentences / rows / objects) to score precisely</span></div>
<div class="row"><span class="k">multihop</span><span class="v"><b>edges</b> from document structure and hyperlinks make the second document one hop away; beam search over edges keeps it tractable</span></div>
<div class="row"><span class="k">modality</span><span class="v"><b>decomposed, instruction-conditioned subqueries</b> let an off-the-shelf multimodal embedder look for an image when the question is about an image</span></div></div>
<div class="callout plain" style="margin-top:14px">Open problems noted in the paper: components that need <b>dependency resolution</b> (one answer feeds the next hop's query) and <b>long-hop</b> evidence — the motivation for the follow-up work, Failure is Feedback.</div>''', icon="✦", cls="soft") + panel("Numbers from the paper (EMNLP 2025)", f'<div class="cols c3" style="flex:1;align-content:start">{stats}</div><div class="note" style="margin-top:10px;font-size:12.5px;color:var(--ink-mute)">Benchmarks: MP-DocVQA, SlideVQA, InfoVQA, MultimodalQA, MMCoQA · embedders MM-Embed / UniME / mmE5 · generator Qwen2.5-VL 7B.</div>', icon="📈") + "</div>"
frames.append(dict(step="✦ Why it works", text="Granularity, structure and modality are handled by three separate mechanisms — and the expensive one (the LLM) runs once per query, not per hop.",
                   stage=stage("Why it works", body, tabs(3, interm=True), BN), status="SUMMARY", interm=True))

META = dict(
    title="LILaC — Worked Example",
    eyebrow="LILaC · EMNLP 2025 · Worked Example",
    h1='How a question about a <span class="hl">photo two hops away</span> gets answered',
    intro=("LILaC retrieves from documents that mix paragraphs, tables and images. It builds a two-layer component graph "
           "offline, decomposes the query into modality-specific subqueries online, and walks the graph edge by edge, scoring each "
           "edge with late interaction over fine-grained subcomponents. Step through one query below."),
    qicon="❓", question=Q_HTML, alabel="ANSWER", answer=ANSWER,
)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "lilac_worked_example.html")
    write(out, render(META, frames))
