#!/bin/bash
# Refresh the contribution graph and push it. Runs daily from this Mac.
set -euo pipefail

ROOT="/Users/chandankumar/Aectx"
cd "$ROOT"
mkdir -p "$ROOT/logs"

PY="$ROOT/.venv/bin/python"
"$PY" scripts/fetch_contributions.py
"$PY" scripts/render_heatmap_svg.py

git add data/contributions.json contrib-heatmap.svg
if git diff --cached --quiet; then
  echo "no changes $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit 0
fi

export GIT_AUTHOR_NAME="Rahul Singh"
export GIT_AUTHOR_EMAIL="178564093+Aectx@users.noreply.github.com"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

git commit -m "chore: refresh contribution graph"
git push origin main
echo "pushed $(date -u +%Y-%m-%dT%H:%M:%SZ)"
