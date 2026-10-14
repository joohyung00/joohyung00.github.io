#!/usr/bin/env bash
# Build the CV from its LaTeX source and drop the PDF where the site serves it.
#   bash build/cv_build.sh            # expects cv/cv.tex (Awesome-CV layout: cv/cv.tex + cv/fonts/ + cv/awesome-cv.cls …)
#   CV_MAIN=cv/main.tex bash build/cv_build.sh
# Needs xelatex + latexmk (TeX Live). The source folder is whatever Overleaf's "Download as ZIP" gives, unzipped into cv/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAIN="${CV_MAIN:-cv/cv.tex}"
[ -f "$ROOT/$MAIN" ] || { echo "no $MAIN — unzip the Overleaf project into $ROOT/cv/ first (set CV_MAIN if the main file has another name)"; exit 1; }
cd "$ROOT/$(dirname "$MAIN")"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -quiet "$(basename "$MAIN")" >/dev/null
latexmk -c "$(basename "$MAIN")" >/dev/null 2>&1 || true
cp "$(basename "${MAIN%.tex}").pdf" "$ROOT/assets/cv/cv.pdf"
echo "assets/cv/cv.pdf updated ($(pdfinfo "$ROOT/assets/cv/cv.pdf" | awk '/^Pages/{print $2}') pages). Now: git add assets/cv/cv.pdf cv && git commit && git push"
