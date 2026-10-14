#!/usr/bin/env python3
"""Import a talk (slides and/or poster) into assets/talks/<key>/ for the Talks page.

    python build/talks_import.py <key> [--slides deck.pptx|deck.pdf] [--poster poster.pptx|poster.pdf]

Writes, under assets/talks/<key>/:
    slides/NN.webp         1280px-wide slide images        (from --slides)
    slides/thumb/NN.webp   320px thumbnails for the rail
    slides.pdf             the deck as PDF (download link)
    poster.webp            poster image, 2400px on the long side (from --poster)
    poster_thumb.webp      640px thumbnail for the listing
    poster.pdf
    meta.json              {"slides": N, "poster": {"w":..,"h":..}}  — read by build.py

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
    a = ap.parse_args()
    if not (a.slides or a.poster):
        ap.error("give --slides and/or --poster")
    dest = os.path.join(ROOT, "assets", "talks", a.key)
    meta_path = os.path.join(dest, "meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    with tempfile.TemporaryDirectory() as tmp:
        if a.slides:
            pdf = to_pdf(os.path.abspath(a.slides), tmp)
            sd = os.path.join(dest, "slides"); shutil.rmtree(sd, ignore_errors=True)
            os.makedirs(os.path.join(sd, "thumb"))
            subprocess.run(["pdftoppm", "-png", "-scale-to-x", "1600", "-scale-to-y", "-1", pdf, os.path.join(tmp, "s")], check=True)
            pngs = sorted(glob.glob(os.path.join(tmp, "s-*.png")))
            for i, p in enumerate(pngs, 1):
                webp(p, os.path.join(sd, f"{i:02d}.webp"), 1280)
                webp(p, os.path.join(sd, "thumb", f"{i:02d}.webp"), 320, 75)
            shutil.copy(pdf, os.path.join(dest, "slides.pdf"))
            meta["slides"] = len(pngs)
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
