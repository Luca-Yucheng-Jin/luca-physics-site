#!/usr/bin/env python3
"""Generate the public crawler directives and canonical HTML sitemap."""

from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://luca-physics-observatory.jinluca3.chatgpt.site"


def public_pages() -> list[Path]:
    """Return every indexable HTML page in stable, human-readable order."""
    pages = [ROOT / "index.html", ROOT / "notes.html"]
    pages.extend(sorted(ROOT.glob("notes-*.html")))
    pages.extend(sorted((ROOT / "notes").glob("*.html")))
    missing = [str(path.relative_to(ROOT)) for path in pages if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing public pages: {', '.join(missing)}")
    return pages


def canonical_url(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return f"{SITE_URL}/" if relative == "index.html" else f"{SITE_URL}/{relative}"


def write_sitemap(pages: list[Path]) -> None:
    rows = "\n".join(
        f"  <url><loc>{escape(canonical_url(path))}</loc></url>" for path in pages
    )
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{rows}\n"
        "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(content, encoding="utf-8")


def write_robots() -> None:
    content = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )
    (ROOT / "robots.txt").write_text(content, encoding="utf-8")


def main() -> None:
    pages = public_pages()
    write_sitemap(pages)
    write_robots()
    print(f"  wrote sitemap.xml ({len(pages)} canonical pages)")
    print("  wrote robots.txt")


if __name__ == "__main__":
    main()
