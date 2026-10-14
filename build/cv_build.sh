#!/usr/bin/env bash
# Build the CV from its LaTeX source and drop the PDF where the site serves it (assets/cv/cv.pdf).
#   bash build/cv_build.sh                       # source: $CV_SRC (default ~/.claude/data/cv, the private data repo), main file cv.tex
#   CV_SRC=/path/to/overleaf-export bash build/cv_build.sh
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
cp "${MAIN%.tex}.pdf" "$ROOT/assets/cv/cv.pdf"
echo "assets/cv/cv.pdf updated ($(pdfinfo "$ROOT/assets/cv/cv.pdf" | awk '/^Pages/{print $2}') pages). Now: git add assets/cv/cv.pdf && git commit && git push"
