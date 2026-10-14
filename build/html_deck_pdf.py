#!/usr/bin/env python3
"""Export a Slides-Hub HTML deck (one NN_*.html per slide, listed in its index.html) to a 1600x900 PDF
that build/talks_import.py can take as --slides.

    python build/html_deck_pdf.py ~/.claude/data/slides/items/<deck> out.pdf

Serves the deck folder on a local port, prints every slide with ?all=1 (all fragments shown) through
headless Chromium, and joins the pages with pdfunite. Needs: playwright (chromium), poppler-utils."""
import re, subprocess, sys, tempfile, time, socket
from pathlib import Path


def main():
    deck, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    files = re.findall(r'\["([^"]+\.html)"', (deck / "index.html").read_text(encoding="utf-8"))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=deck,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(0.8)
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as td, sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1600, "height": 900}); parts = []
            for i, f in enumerate(files):
                pg.goto(f"http://127.0.0.1:{port}/{f}?all=1"); pg.wait_for_timeout(300)
                o = Path(td) / f"{i:02d}.pdf"
                pg.pdf(path=str(o), width="1600px", height="900px", print_background=True,
                       margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
                parts.append(str(o))
            b.close()
            subprocess.run(["pdfunite", *parts, str(out)], check=True)
    finally:
        srv.terminate()
    print(f"{out}: {len(files)} pages, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
