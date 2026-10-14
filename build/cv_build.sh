#!/usr/bin/env bash
# Build the CV from its LaTeX source and drop the PDF where the site serves it (assets/cv/cv.pdf).
#   bash build/cv_build.sh                       # source: $CV_SRC (default ~/.claude/data/cv, the private data repo), main file cv.tex
#   CV_SRC=/path/to/overleaf-export bash build/cv_build.sh
#   CV_OUT=/some/where/cv.pdf bash build/cv_build.sh    # write the PDF elsewhere (the my-page hub builds into an item first)
# The source is the Overleaf project as exported ("Download as ZIP"): Awesome-CV (cv.tex + cv/*.tex + awesome-cv.cls + fonts/ + profile.jpeg).
# Needs TeX Live with xelatex + latexmk and these packages (TinyTeX: tlmgr install …):
#   ragged2e fontawesome fancyhdr xifthen setspace tcolorbox tikzfill roboto sourcesans parskip
# and FontAwesome.otf visible to fontconfig (symlink into ~/.fonts/tex + fc-cache), because awesome-cv loads it by name.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${CV_SRC:-$HOME/.claude/data/cv}"
MAIN="${CV_MAIN:-cv.tex}"
[ -f "$SRC/$MAIN" ] || { echo "no $SRC/$MAIN — put the Overleaf export there (or set CV_SRC / CV_MAIN)"; exit 1; }
cd "$SRC"
latexmk -xelatex -interaction=nonstopmode -halt-on-error "$MAIN" >/dev/null || { echo "xelatex failed; see $SRC/${MAIN%.tex}.log"; exit 1; }
latexmk -c "$MAIN" >/dev/null 2>&1 || true
OUT="${CV_OUT:-$ROOT/assets/cv/cv.pdf}"
mkdir -p "$(dirname "$OUT")"
cp "${MAIN%.tex}.pdf" "$OUT"
echo "$OUT updated ($(pdfinfo "$OUT" | awk '/^Pages/{print $2}') pages)."
