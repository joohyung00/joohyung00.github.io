#!/usr/bin/env python3
"""Import a talk (slides and/or poster) into assets/talks/<key>/ for the Talks page,
or a seminar deck into assets/seminars/<key>/ with --into assets/seminars.

    python build/talks_import.py <key> [--slides deck.pptx|deck.pdf] [--poster poster.pptx|poster.pdf] [--into assets/seminars]
    python build/talks_import.py <key> --html ~/.claude/data/slides/items/<deck> --into assets/seminars
    python build/talks_import.py <key> --slides deck.pptx --steps [--keep 1-18] [--drop 8,11]   # keep click animations as steps

Writes, under assets/talks/<key>/:
    slides/NN.webp         1280px-wide slide images        (from --slides)
    slides/thumb/NN.webp   320px thumbnails for the rail
    slides.pdf             the deck as PDF (download link)
    poster.webp            poster image, 2400px on the long side (from --poster)
    poster_thumb.webp      640px thumbnail for the listing
    poster.pdf
    meta.json              {"slides": N, "poster": {"w":..,"h":..}}  — read by build.py
With --html (a Slides-Hub deck: one NN_*.html per slide, order in its index.html) the slides are served as
the original HTML files instead of images:
    html/NN_*.html, html/deck.html   copied verbatim (self-contained pages; deck.html = all slides on one page)
    slides/thumb/NN.webp, slides.pdf  from a Playwright print of the deck (build/html_deck_pdf.py)
    meta.json              {"slides": N, "html": ["00_cover.html", ...]}
With --steps (pptx only) the deck is first expanded by build/pptx_steps.py into one page per click
step; intermediate states land in slides/steps/NN-k.webp (k = 0 … K-1, before the final look), the
final look stays slides/NN.webp, slides.pdf keeps only the final pages, and meta.json records
{"steps": {"NN": K}} so the viewer plays the states before moving to the next slide.
--keep / --drop select original slides (1-based) and need --steps.

Then add/adjust the entry in build/content/talks.yml and run `python build/build.py`.

Needs: soffice (LibreOffice, only for .pptx input), pdftoppm (poppler), Pillow.
Font note: PowerPoint decks set in Calibri/Consolas render faithfully only if metric-compatible
fonts are installed (Carlito, Inconsolata via ~/.config/fontconfig/fonts.conf aliases); exporting the
PDF from PowerPoint and passing the .pdf here avoids the issue entirely.
"""
import argparse, glob, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def to_pdf(src, workdir):
    if src.lower().endswith(".pdf"):
        return src
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", workdir, src],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = os.path.join(workdir, os.path.splitext(os.path.basename(src))[0] + ".pdf")
    if not os.path.exists(out):
        sys.exit(f"soffice did not produce {out}")
    return out


def webp(png, dst, width, q=82):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    if im.width != width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=q, method=6)
    return im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key")
    ap.add_argument("--slides")
    ap.add_argument("--poster")
    ap.add_argument("--html", metavar="DECKDIR", help="Slides-Hub HTML deck folder: serve the slide pages themselves (see docstring)")
    ap.add_argument("--steps", action="store_true", help="pptx: expand click animations into step images (build/pptx_steps.py)")
    ap.add_argument("--keep", help="with --steps: keep only these original slides, e.g. 1-18")
    ap.add_argument("--drop", help="with --steps: drop these original slides, e.g. 8,11")
    ap.add_argument("--into", default="assets/talks", help="destination folder under the repo root (default assets/talks; use assets/seminars for seminars.yml entries)")
    a = ap.parse_args()
    if not (a.slides or a.poster or a.html):
        ap.error("give --slides, --poster and/or --html")
    dest = os.path.join(ROOT, *a.into.strip("/").split("/"), a.key)
    meta_path = os.path.join(dest, "meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    with tempfile.TemporaryDirectory() as tmp:
        if a.html:
            import re
            deck = os.path.abspath(a.html)
            names = re.findall(r'\["([^"]+\.html)"', open(os.path.join(deck, "index.html"), encoding="utf-8").read())
            hd = os.path.join(dest, "html"); shutil.rmtree(hd, ignore_errors=True); os.makedirs(hd)
            for n in names:
                shutil.copy(os.path.join(deck, n), os.path.join(hd, n))
            if os.path.exists(os.path.join(deck, "deck.html")):
                shutil.copy(os.path.join(deck, "deck.html"), os.path.join(hd, "deck.html"))
            pdf = os.path.join(tmp, "deck.pdf")
            subprocess.run([sys.executable, os.path.join(HERE, "html_deck_pdf.py"), deck, pdf], check=True, stdout=subprocess.DEVNULL)
            sd = os.path.join(dest, "slides"); shutil.rmtree(sd, ignore_errors=True)
            os.makedirs(os.path.join(sd, "thumb"))
            subprocess.run(["pdftoppm", "-png", "-scale-to-x", "640", "-scale-to-y", "-1", pdf, os.path.join(tmp, "s")], check=True)
            pngs = sorted(glob.glob(os.path.join(tmp, "s-*.png")))
            for i, p in enumerate(pngs, 1):
                webp(p, os.path.join(sd, "thumb", f"{i:02d}.webp"), 320, 75)
            shutil.copy(pdf, os.path.join(dest, "slides.pdf"))
            meta["slides"] = len(names); meta["html"] = names
            print(f"{a.key}: {len(names)} html slides")
        if a.slides and a.steps:
            if not a.slides.lower().endswith(".pptx"):
                sys.exit("--steps needs a .pptx (animations live in the pptx, not in a PDF)")
            expanded = os.path.join(tmp, "expanded.pptx"); smap = os.path.join(tmp, "steps.json")
            cmd = [sys.executable, os.path.join(HERE, "pptx_steps.py"), os.path.abspath(a.slides), expanded, "--json", smap]
            if a.keep: cmd += ["--keep", a.keep]
            if a.drop: cmd += ["--drop", a.drop]
            subprocess.run(cmd, check=True)
            info = json.load(open(smap))
            pdf = to_pdf(expanded, tmp)
            sd = os.path.join(dest, "slides"); shutil.rmtree(sd, ignore_errors=True)
            os.makedirs(os.path.join(sd, "thumb")); os.makedirs(os.path.join(sd, "steps"))
            subprocess.run(["pdftoppm", "-png", "-scale-to-x", "1600", "-scale-to-y", "-1", pdf, os.path.join(tmp, "s")], check=True)
            pngs = sorted(glob.glob(os.path.join(tmp, "s-*.png")))
            if len(pngs) != info["pages"]:
                sys.exit(f"expanded deck has {len(pngs)} pages, expected {info['pages']}")
            page, steps, finals = 0, {}, []
            for sl in info["slides"]:
                n = sl["n"]
                for k in range(sl["steps"]):
                    webp(pngs[page], os.path.join(sd, "steps", f"{n:02d}-{k}.webp"), 1280); page += 1
                webp(pngs[page], os.path.join(sd, f"{n:02d}.webp"), 1280)
                webp(pngs[page], os.path.join(sd, "thumb", f"{n:02d}.webp"), 320, 75)
                finals.append(page); page += 1
                if sl["steps"]:
                    steps[f"{n:02d}"] = sl["steps"]
            from pypdf import PdfReader, PdfWriter          # slides.pdf = final looks only
            r = PdfReader(pdf); w = PdfWriter()
            for i in finals:
                w.add_page(r.pages[i])
            w.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
            w.write(os.path.join(dest, "slides.pdf"))
            meta["slides"] = len(info["slides"]); meta["steps"] = steps; meta.pop("html", None)
            print(f"{a.key}: {len(info['slides'])} slides, {sum(steps.values())} animation steps on {len(steps)} slide(s)")
        elif a.slides:
            pdf = to_pdf(os.path.abspath(a.slides), tmp)
            sd = os.path.join(dest, "slides"); shutil.rmtree(sd, ignore_errors=True)
            os.makedirs(os.path.join(sd, "thumb"))
            subprocess.run(["pdftoppm", "-png", "-scale-to-x", "1600", "-scale-to-y", "-1", pdf, os.path.join(tmp, "s")], check=True)
            pngs = sorted(glob.glob(os.path.join(tmp, "s-*.png")))
            for i, p in enumerate(pngs, 1):
                webp(p, os.path.join(sd, f"{i:02d}.webp"), 1280)
                webp(p, os.path.join(sd, "thumb", f"{i:02d}.webp"), 320, 75)
            shutil.copy(pdf, os.path.join(dest, "slides.pdf"))
            meta["slides"] = len(pngs); meta.pop("html", None); meta.pop("steps", None)
            print(f"{a.key}: {len(pngs)} slides")
        if a.poster:
            pdf = to_pdf(os.path.abspath(a.poster), tmp)
            os.makedirs(dest, exist_ok=True)
            subprocess.run(["pdftoppm", "-png", "-scale-to", "2400", "-singlefile", pdf, os.path.join(tmp, "p")], check=True)
            from PIL import Image
            png = os.path.join(tmp, "p.png"); w = Image.open(png).width
            size = webp(png, os.path.join(dest, "poster.webp"), w, 80)
            webp(png, os.path.join(dest, "poster_thumb.webp"), 640, 78)
            shutil.copy(pdf, os.path.join(dest, "poster.pdf"))
            meta["poster"] = {"w": size[0], "h": size[1]}
            print(f"{a.key}: poster {size[0]}x{size[1]}")
    os.makedirs(dest, exist_ok=True)
    json.dump(meta, open(meta_path, "w"), indent=1)
    print("meta ->", meta_path)


if __name__ == "__main__":
    main()
