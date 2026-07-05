#!/usr/bin/env bash
#
# check_sync.sh — verify the repo's mirrored files are byte-identical.
#
# This project keeps several copies of the same asset in different places, and
# the deployed GitHub Pages site is served from the repo ROOT (not web-app/).
# When a copy drifts, the live site silently serves stale code — that is exactly
# how the root landing page ended up months behind web-app/index.html.
#
# Two invariants are enforced:
#   1. TEMPLATE TRIPLET  — template.html, html_template.html and
#      web-app/template.html must be identical. rex_parser.py embeds
#      html_template.html; the dashboard template must match everywhere.
#   2. PAGES-ROOT MIRROR — the files GitHub Pages serves from the repo root must
#      match their maintained source under web-app/.
#
# Run manually any time:   bash scripts/check_sync.sh
# It also runs automatically on `git push` via .githooks/pre-push.
#
# Exit status: 0 = all in sync, 1 = drift detected (prints the fix commands).

set -u

# Resolve repo root regardless of where the script is invoked from.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || { echo "check_sync: cannot cd to repo root" >&2; exit 2; }

drift=0

# --- helper: assert two files are byte-identical --------------------------
# Usage: same <fileA> <fileB> <fix-hint>
same() {
  local a="$1" b="$2" hint="$3"
  if [ ! -f "$a" ]; then echo "  ✗ MISSING: $a"; drift=1; return; fi
  if [ ! -f "$b" ]; then echo "  ✗ MISSING: $b"; drift=1; return; fi
  if cmp -s "$a" "$b"; then
    echo "  ✓ $a == $b"
  else
    echo "  ✗ DRIFT:  $a  !=  $b"
    echo "      fix:  $hint"
    drift=1
  fi
}

echo "== Template triplet =="
# All three must match template.html (the source of truth for edits).
same "template.html" "html_template.html" "cp template.html html_template.html"
same "template.html" "web-app/template.html" "cp template.html web-app/template.html"

echo "== Pages-root mirror (root files served by GitHub Pages) =="
# The maintained source lives in web-app/; the root copy is what Pages serves.
same "index.html"               "web-app/index.html"               "cp web-app/index.html index.html"
same "agentforce-ops-logo.svg"  "web-app/agentforce-ops-logo.svg"  "cp web-app/agentforce-ops-logo.svg agentforce-ops-logo.svg"
same "cloud-logo.png"           "web-app/cloud-logo.png"           "cp web-app/cloud-logo.png cloud-logo.png"

echo
if [ "$drift" -ne 0 ]; then
  echo "✗ Sync check FAILED — copies have drifted (see fixes above)."
  echo "  After copying, re-stage and re-run: bash scripts/check_sync.sh"
  exit 1
fi
echo "✓ Sync check passed — all mirrored files are identical."
exit 0
