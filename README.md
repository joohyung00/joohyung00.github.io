# joohyung00.github.io

Personal site of Joohyung Yun. Plain static HTML, no Jekyll (`.nojekyll`).

```
build/content/*.yml      ← edit content here (profile, news, publications, experience, teaching, honors, patents, education, photos, talks, seminars)
build/templates/*.j2     ← layout (Jinja2)
assets/site.css, site.js ← style + the little JS (dark mode, carousel, latest posts, slide viewer)
python build/build.py    → index.html, 404.html, talks/…, seminars/… (an index + one viewer page per deck)   (needs: pip install jinja2 pyyaml; bakes the 3 latest posts from mypages/index.json)
python build/build.py --inline out.html   → single-file preview bundle
mypages/                 ← posts published by the my-page skill (do not edit by hand)
legacy/                  ← previous versions of the site, kept as static snapshots (see legacy/README.md)
```

Add a paper: append to `build/content/publications.yml`, drop its thumbnail/figure in `assets/img/pubs/`,
run the build, commit `index.html` together with the content change.

Add a talk or poster: `python build/talks_import.py <key> --slides deck.pptx --poster poster.pptx` (pptx or pdf;
writes `assets/talks/<key>/` with WebP slides, thumbnails, PDFs and `meta.json`), then add the entry to
`build/content/talks.yml` (venue, place, date, `pub` = publications key, or `title` + `pubs` for a seminar talk that
covers several papers) and point the paper's `Slides`/`Poster` links at `talks/<key>/`. The viewer is plain
scroll-snap HTML; PDFs are kept for download.

Add a seminar deck (lab seminar on my work, or a paper I presented in the reading group): same import with
`--into assets/seminars`, then an entry in `build/content/seminars.yml` (`kind`, `venue`, `date`, `summary`, and either
`pubs` or `paper: {authors, venue, url}`; `extra` for a warm-up paper in the same session). Decks authored as HTML in
the Slides Hub go through `python build/html_deck_pdf.py <deck dir> out.pdf` first. Unpublished work and
manuscripts under review never go here.

The home page shows the three latest talks, seminars and posts; the nav is Talks / Seminars / Posts / CV (the PDF).
