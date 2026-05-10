#!/usr/bin/env python3
"""Tiny static dev server with no-cache headers — avoids the stale
asset problem when iterating on theme.js / styles.css. Used by
preview_start; production deploys (GitHub Pages, Vercel, etc.) are
unaffected."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
import sys


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("", port), NoCacheHandler)
    print(f"Serving on http://localhost:{port} (no-cache)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
