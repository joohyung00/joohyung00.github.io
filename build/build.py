#!/usr/bin/env python3
"""Build joohyung00.github.io from build/content/*.yml + build/templates/*.j2.

    python build/build.py                 # writes index.html, 404.html, talks/index.html, talks/<key>/index.html
    python build/build.py --inline out.html [--page talks/index.html]
                                          # single-file bundle (CSS/JS inlined, images as data URIs)
                                          # for previewing on the my-page Preview Hub

Dependencies: jinja2, pyyaml (pip install jinja2 pyyaml). No Jekyll, no Ruby.
"""
import argparse, base64, datetime, json, mimetypes, os, re, sys
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONTENT = os.path.join(HERE, "content")
TEMPLATES = os.path.join(HERE, "templates")


def load_content():
    data = {}
    for name in sorted(os.listdir(CONTENT)):
        if name.endswith(".yml"):
            with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
                data[name[:-4]] = yaml.safe_load(f) or {}
    return data


def bold_self(authors, me):
    """'Yun, J., Lee, D., Han, W.' -> '<b>Yun, J.</b>, Lee, D., Han, W.'"""
    return authors.replace(me, f"<b>{me}</b>")


def recent_posts(n=3, exclude=()):
    """Latest n posts from the my-page manifest (mypages/index.json), or [] if it is missing.
    Slugs in `exclude` (profile.yml posts_exclude, e.g. theme demos) are skipped here and at runtime."""
    path = os.path.join(ROOT, "mypages", "index.json")
    if not os.path.exists(path):
        return []
    try:
        pages = json.load(open(path, encoding="utf-8")).get("pages", [])
    except Exception:
        return []
    pages = [p for p in pages if p.get("slug") not in set(exclude)]
    pages = sorted(pages, key=lambda p: p.get("created", ""), reverse=True)[:n]
    out = []
    for p in pages:
        ex = re.sub(r"\s+", " ", p.get("excerpt", "")).strip()
        out.append({"date": (p.get("created") or "")[:10], "url": p.get("url", "#"),
                    "title": p.get("title") or p.get("slug", ""), "excerpt": (ex[:140] + "…") if len(ex) > 140 else ex})
    return out


def render(inline=False):
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters["bold_self"] = bold_self
    data = load_content()
    ctx = dict(data)
    ctx["recent_posts"] = recent_posts(exclude=data["profile"].get("posts_exclude") or [])
    ctx["build_date"] = datetime.date.today().strftime("%Y-%m")
    ctx["build_month"] = datetime.date.today().strftime("%B %Y")
    ctx["year"] = datetime.date.today().year
    ctx["inline"] = inline
    if inline:
        ctx["inline_css"] = open(os.path.join(ROOT, "assets", "site.css"), encoding="utf-8").read()
        ctx["inline_js"] = open(os.path.join(ROOT, "assets", "site.js"), encoding="utf-8").read()
    ctx["talks"] = load_talks(data)

    def page(tpl, root, **extra):
        # `root` = relative path back to the site root ("" / "../" / "../../"); the inline bundle
        # is assembled from the repo root, so it always uses "".
        return env.get_template(tpl).render(**dict(ctx, root="" if inline else root, **extra))

    pages = {"index.html": page("index.html.j2", ""),
             "404.html": page("404.html.j2", ""),
             "talks/index.html": page("talks.html.j2", "../", nav_on="talks")}
    for t in ctx["talks"]:
        pages[f"talks/{t['key']}/index.html"] = page("talk.html.j2", "../../", t=t, nav_on="talks")
    if inline:
        site = data["profile"]["site_url"].rstrip("/")
        pages = {k: absolutize_links(inline_images(v), site) for k, v in pages.items()}
    return pages


def load_talks(data):
    """talks.yml entries joined with their publication and with assets/talks/<key>/meta.json
    (slide count, poster size) written by talks_import.py."""
    pubs = {p["key"]: p for p in data.get("publications", []) or []}
    out = []
    for t in data.get("talks", []) or []:
        t = dict(t)
        t["pub"] = pubs[t["pub"]]
        meta_path = os.path.join(ROOT, "assets", "talks", t["key"], "meta.json")
        meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}
        t["slides"] = meta.get("slides", 0)
        t["poster"] = meta.get("poster")
        if not (t["slides"] or t["poster"]):
            print(f"warning: talks/{t['key']} has no slides or poster (run build/talks_import.py)", file=sys.stderr)
        out.append(t)
    return out


def absolutize_links(html, site):
    """Preview bundle only: point root-relative and repo-relative links (posts, CV, legacy, the
    posts manifest) at the live site, so clicking them in the Preview Hub does not hit localhost.
    In-page anchors (#...), mailto:, http(s) and data: URLs are left alone."""
    def repl(m):
        attr, url = m.group(1), m.group(2)
        if url.startswith(("#", "http://", "https://", "mailto:", "data:", "//")):
            return m.group(0)
        return f'{attr}="{site}/{url.lstrip("/")}"'
    return re.sub(r'\b(href|data-posts)="([^"]+)"', repl, html)


def inline_images(html):
    def repl(m):
        path = os.path.join(ROOT, m.group(2))
        if not os.path.exists(path):
            return m.group(0)
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'{m.group(1)}="data:{mime};base64,{b64}"'
    return re.sub(r'(src|content)="(assets/(?:img|talks)/[^"]+)"', repl, html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inline", metavar="OUT", help="write a single-file preview bundle to OUT instead of the site files")
    ap.add_argument("--page", default="index.html", help="with --inline: which page to bundle (default index.html)")
    args = ap.parse_args()
    pages = render(inline=bool(args.inline))
    if args.inline:
        with open(args.inline, "w", encoding="utf-8") as f:
            f.write(pages[args.page])
        print(f"inline bundle -> {args.inline} ({os.path.getsize(args.inline) // 1024} KB)")
        return
    for name, html in pages.items():
        out = os.path.join(ROOT, name)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"wrote {name} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    sys.exit(main())
