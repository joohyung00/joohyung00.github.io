"""Shared generator for the "worked example" explainer posts (same shell as the FiF post).

A post = hero (eyebrow / h1 / intro / question bar) + a deck of frames. Each frame is a caption and a
1920x850 "stage" rendered inside a srcdoc iframe (scaled to fit). Stages reuse the FiF stage stylesheet
(tokens, .stage, .tabs, .query-banner, .panels/.panel, chips) plus the extra classes defined here.
"""
import html, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SHELL = open(os.path.join(HERE, "shell.html"), encoding="utf-8").read()
STAGE_CSS = open(os.path.join(HERE, "stage_base.css"), encoding="utf-8").read()

EXTRA_CSS = r"""
/* ===== generic layout for the new stages ===== */
.cols { flex:1; display:grid; gap:16px; min-height:0; grid-template-rows:minmax(0,1fr); }
.panel { overflow:hidden; } .note, .kv, .callout, .eq, .mini-label { flex:none; }
.cols.c2 { grid-template-columns: 1fr 1fr; } .cols.c21 { grid-template-columns: 2fr 1fr; } .cols.c12 { grid-template-columns: 1fr 2fr; }
.cols.c3 { grid-template-columns: 1fr 1fr 1fr; }
.cols.stack { grid-template-columns: 1fr; grid-template-rows: minmax(0,1.45fr) minmax(0,1fr); }
.cols.stack .cols { gap:22px; } .cols.stack .cols > div { min-width:0; } .cols.c121 { grid-template-columns: 1fr 1.6fr 1fr; }
.panel.soft { background: var(--purple-50); border-color: var(--purple-200); }
.panel.ok { background: var(--ok-bg); border-color: #A7F3D0; } .panel.fail { background: var(--fail-bg); border-color: #FECACA; }
.panel .fill { flex:1; min-height:0; display:flex; align-items:center; justify-content:center; }
.panel .fill svg { width:100%; height:100%; max-height:100%; display:block; }
.note { font-size: 14px; color: var(--ink-soft); line-height: 1.45; }
.note b { color: var(--ink); } .note .em { color: var(--purple-700); font-weight: 600; }
.note ul { padding-left: 18px; margin: 6px 0; } .note li { margin: 3px 0; }
.kv { display:flex; flex-direction:column; gap:8px; }
.kv .row { display:flex; gap:10px; align-items:flex-start; font-size:13.5px; }
.kv .k { font-family:'JetBrains Mono',monospace; font-weight:700; color:var(--purple-600); min-width:92px; font-size:12.5px; padding-top:2px; }
.kv .v { color: var(--ink-soft); line-height:1.35; }
.chip { display:inline-flex; align-items:center; gap:6px; font-size:12.5px; font-weight:600; padding:4px 10px; border-radius:999px; background:#fff; border:1px solid var(--border); color:var(--ink-soft); }
.chip.txt { border-color:#C7D2FE; background:#EEF2FF; color:#3730A3; } .chip.tbl { border-color:#A7F3D0; background:#ECFDF5; color:#065F46; }
.chip.img { border-color:#FBCFE8; background:#FDF2F8; color:#9D174D; } .chip.on { box-shadow:0 0 0 3px rgba(167,139,250,.25); border-color:var(--purple-400); }
.callout { border-radius: 13px; padding: 13px 16px; font-size: 14px; line-height: 1.45; border: 1.5px solid; }
.callout.ok { background: var(--ok-bg); border-color: #A7F3D0; color: #065F46; } .callout.fail { background: var(--fail-bg); border-color:#FECACA; color:#991B1B; }
.callout.info { background: var(--blue-50); border-color: var(--blue-300); color: #1E40AF; } .callout.plain { background: var(--purple-50); border-color: var(--purple-200); color: var(--ink-soft); }
.callout b { font-weight: 700; }
.eq { font-family:'JetBrains Mono',monospace; font-size:13.5px; color:var(--ink); background:#fff; border:1px dashed var(--purple-300); border-radius:10px; padding:10px 14px; line-height:1.5; }
.eq .hl { background: var(--purple-100); color: var(--purple-700); padding: 0 4px; border-radius: 4px; }
.big { font-size: 40px; font-weight: 800; letter-spacing: -1px; color: var(--purple-700); line-height: 1; }
.big small { font-size: 14px; font-weight: 600; color: var(--ink-mute); letter-spacing: 0; margin-left: 8px; }
.stat { background:#fff; border:1.5px solid var(--panel-border); border-radius:14px; padding:14px 16px; }
.stat .n { font-size: 30px; font-weight: 800; color: var(--purple-700); letter-spacing:-.5px; line-height:1.05; }
.stat .l { font-size: 12.5px; color: var(--ink-mute); margin-top: 4px; line-height:1.3; }
/* matrix */
table.mx { border-collapse: separate; border-spacing: 5px; font-family:'JetBrains Mono',monospace; font-size:16px; }
table.mx th { font-weight:700; color:var(--ink-mute); font-size:13px; padding:4px 8px; text-align:center; white-space:nowrap; }
table.mx th.rowh { text-align:left; color:var(--purple-600); font-size:15px; }
table.mx td { width:84px; height:50px; text-align:center; border-radius:8px; background:#F6F4FC; color:var(--ink-soft); }
table.mx td.max { background: var(--purple-500); color:#fff; font-weight:700; box-shadow:0 3px 10px rgba(124,58,237,.3); }
table.mx td.sum { background: var(--ok); color:#fff; font-weight:800; width:100px; }
table.mx td.dim { opacity:.45; }
/* json code */
pre.json { font-family:'JetBrains Mono',monospace; font-size:13.5px; line-height:1.5; background:#fff; border:1.5px solid var(--border); border-radius:12px; padding:12px 14px; color:var(--ink); white-space:pre; overflow:hidden; }
pre.json .k { color: var(--purple-700); } pre.json .s { color:#065F46; } pre.json .n { color:#1D4ED8; } pre.json .t { color:#9D174D; font-weight:700; }
pre.json .hl { background: var(--purple-100); border-radius:4px; }
/* svg text defaults */
svg text { font-family:'Inter',sans-serif; } svg .mono { font-family:'JetBrains Mono',monospace; }
"""

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap" rel="stylesheet">'


def esc(s):
    return html.escape(str(s), quote=True)


def stage(title, body, tabs=None, banner="", extra_css=""):
    """A 1920x850 stage document. `tabs` = list of (label, cls) with cls in {'', 'active', 'intermission'}."""
    t = ""
    if tabs:
        t = '<div class="tabs">' + "".join(f'<span class="tab {c}">{l}</span>' for l, c in tabs) + "</div>"
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">'
            f'<title>{esc(title)}</title>{FONTS}<style>{STAGE_CSS}{EXTRA_CSS}{extra_css}</style></head>'
            f'<body><div class="stage">{t}{banner}{body}</div></body></html>')


def banner(question_html, answer, label="ANSWER"):
    return (f'<div class="query-banner"><div class="qmark">❓</div><div class="qtext">{question_html}</div>'
            f'<div class="answer"><span class="lbl">{label}</span><span class="val">{answer}</span></div></div>')


def panel(title, body, icon="", tag="", cls=""):
    tg = f'<span class="mtag">{tag}</span>' if tag else ""
    ic = f'<span class="ico">{icon}</span>' if icon else ""
    return f'<div class="panel {cls}"><div class="panel-title">{ic}{title}{tg}</div>{body}</div>'


def frame(i, step, text, stage_html, interm=False, status=""):
    cls = "frame is-interm" if interm else "frame"
    return (f'<section class="{cls}" data-i="{i}" data-status="{esc(status)}">\n'
            f'  <h2 class="cap"><span class="cap-step">{step}</span><span class="cap-text">{text}</span></h2>\n'
            f'  <div class="screen"><div class="box"><iframe loading="lazy" title="{esc(step)}" srcdoc="{esc(stage_html)}"></iframe></div></div>\n'
            f'</section>\n')


def render(meta, frames):
    """meta: title, eyebrow, h1, intro, qicon, question, alabel, answer. frames: list of dicts
    (step, text, stage, interm?, status?)."""
    n = len(frames)
    dots, secs = [], []
    for i, f in enumerate(frames):
        plain = re.sub(r"<[^>]+>", "", f["text"])
        cls = "dot is-interm" if f.get("interm") else "dot"
        dots.append(f'<button class="{cls}" data-go="{i}" aria-label="{esc(f["step"])}" title="{esc(f["step"] + " — " + plain)}"></button>')
        secs.append(frame(i, f["step"], f["text"], f["stage"], f.get("interm", False), f.get("status", "")))
    out = SHELL
    for k, v in meta.items():
        out = out.replace("{{" + k.upper() + "}}", v)
    out = out.replace("{{DOTS}}", "".join(dots)).replace("{{FRAMES}}", "".join(secs)).replace("{{N}}", str(n))
    out = re.sub(r"· 14 frames", f"· {n} frames", out)
    assert "{{" not in out, re.findall(r"\{\{[A-Z]+\}\}", out)
    return out


# ---------------------------------------------------------------- SVG helpers
def svg(w, h, inner, cls=""):
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" class="{cls}">{inner}</svg>'


def box(x, y, w, h, label, sub="", fill="#fff", stroke="#D8D0F0", color="#1E1B3C", r=12, fs=15, sw=1.5, dash="", bold=True, subcolor="#8B86B5", extra=""):
    t = f'<text x="{x + w / 2}" y="{y + h / 2 + (0 if not sub else -5)}" text-anchor="middle" dominant-baseline="middle" font-size="{fs}" font-weight="{700 if bold else 500}" fill="{color}">{esc(label)}</text>'
    if sub:
        t += f'<text x="{x + w / 2}" y="{y + h / 2 + 13}" text-anchor="middle" dominant-baseline="middle" font-size="{fs - 4}" fill="{subcolor}" class="mono">{esc(sub)}</text>'
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<g {extra}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>{t}</g>'


def circle(cx, cy, r, label, fill="#fff", stroke="#D8D0F0", color="#1E1B3C", fs=14, sw=1.5):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" font-size="{fs}" font-weight="700" fill="{color}">{esc(label)}</text>')


def line(x1, y1, x2, y2, stroke="#CDC7E0", sw=1.5, dash="", arrow=False, opacity=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = ' marker-end="url(#arr)"' if arrow else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}{m} opacity="{opacity}"/>'


def text(x, y, s, fs=13, color="#4C4880", anchor="start", weight=500, mono=False, extra=""):
    c = ' class="mono"' if mono else ""
    return f'<text x="{x}" y="{y}" font-size="{fs}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}"{c} {extra}>{esc(s)}</text>'


ARROW_DEFS = ('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
              '<path d="M0,0 L10,5 L0,10 z" fill="#8B5CF6"/></marker>'
              '<marker id="arrg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
              '<path d="M0,0 L10,5 L0,10 z" fill="#9CA3AF"/></marker></defs>')


def write(path, html_text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_text)
    print(f"wrote {path} ({len(html_text) // 1024} KB)")
