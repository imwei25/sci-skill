#!/usr/bin/env bash
# One-command install for the sci-skill suite (Linux / macOS).
#   bash install.sh              # Python deps only
#   bash install.sh --with-pdf   # also install pandoc + xelatex (for render-pdf-doc)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"
REQ="$ROOT/scripts/requirements-skills.txt"
WITH_PDF=0
[ "${1:-}" = "--with-pdf" ] && WITH_PDF=1

echo "== sci-skill install (Linux/macOS) =="

# 1) venv
if [ ! -x "$PY" ]; then
  base=""
  for c in python3 python; do command -v "$c" >/dev/null 2>&1 && { base="$c"; break; }; done
  [ -z "$base" ] && { echo "Python not found. Install Python 3.10+ first."; exit 1; }
  echo "Creating .venv ..."
  "$base" -m venv "$VENV"
fi
"$PY" --version

# 2) deps
echo "Installing Python deps (first run ~3-8 min) ..."
"$PY" -m pip install -U pip -q
"$PY" -m pip install -r "$REQ"

# 3) optional PDF toolchain
if [ "$WITH_PDF" = 1 ]; then
  echo "Installing pandoc + xelatex + CJK fonts (for render-pdf-doc) ..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y pandoc texlive-xetex texlive-lang-cjk fonts-noto-cjk
  elif command -v brew >/dev/null 2>&1; then
    brew install pandoc && brew install --cask mactex-no-gui
  else
    echo "  ! no apt/brew; install pandoc + texlive-xetex manually for PDF output."
  fi
fi

# 4) validate
"$PY" "$ROOT/scripts/validate_skills.py"

echo ""
echo "Done."
echo "Interpreter: $PY"
echo "Skills dir : $ROOT/skills"
echo "Load them: point your agent framework at the skills/ folder (see README)."
echo "Tip: 'source .venv/bin/activate' so vendored skills' bare 'python3' resolves to this venv."
[ "$WITH_PDF" = 0 ] && echo "PDF (render-pdf-doc)? re-run: bash install.sh --with-pdf"
