#!/usr/bin/env bash
# build.sh — convert every .tex file in tex/ to a rendered HTML note page,
# then optionally start the dev server.
#
# Usage:
#   ./build.sh           # one-shot: convert all .tex → notes/*.html
#   ./build.sh --serve   # convert, then start a local server on :8000
#   ./build.sh --watch   # watch tex/ and rebuild whenever a .tex changes

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

build_once() {
    echo "▶ Converting tex/*.tex → notes/*.html ..."
    python3 build/tex_to_html.py
    echo "✔ Build complete."
}

case "${1:-}" in
  --serve)
    build_once
    echo "▶ Starting dev server at http://localhost:8000 (Ctrl-C to stop)"
    exec python3 -m http.server 8000
    ;;
  --watch)
    if ! command -v fswatch >/dev/null 2>&1; then
      echo "fswatch not installed; falling back to polling every 2 s."
      build_once
      while sleep 2; do
        latest=$(stat -f %m tex/*.tex 2>/dev/null | sort -n | tail -1)
        if [[ "${latest:-0}" != "${last:-0}" ]]; then
          last=$latest
          build_once
        fi
      done
    else
      build_once
      echo "▶ Watching tex/ — rebuild on change..."
      fswatch -o tex/ | while read; do build_once; done
    fi
    ;;
  --help|-h)
    grep '^#' "$0" | sed 's/^# \{0,1\}//'
    ;;
  "")
    build_once
    ;;
  *)
    echo "Unknown option: $1" >&2
    echo "Usage: $0 [--serve|--watch|--help]" >&2
    exit 1
    ;;
esac
