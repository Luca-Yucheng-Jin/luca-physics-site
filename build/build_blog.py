#!/usr/bin/env python3
"""Build the informal blog from plain-text JSON entries in content/blog/.

Reuses the site's page chrome and MathJax; no extra publishing dependency.
Only generated HTML is copied into production, never the source drafts.
"""

import html
import json
import re
from datetime import date
from pathlib import Path

from build_indexes import (
    AUTHOR_NAME, PERSON_ID, SITE_URL, collection_schema,
    footer_html, page_chrome_head, topbar,
)

ROOT = Path(__file__).resolve().parent.parent
DESCRIPTION = (
    "Short thoughts, open questions, and things I’m still working out. "
    "A place to write without having to make everything into a full set of notes."
)


def read_posts(source: Path) -> list[dict]:
    posts = []
    for path in sorted(source.glob("*.json")):
        post = json.loads(path.read_text(encoding="utf-8"))
        # Require an explicit publish decision, including for new templates.
        if post.get("draft", True) is not False:
            continue
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path.stem):
            raise ValueError(f"{path.name}: use a lowercase, hyphenated filename")
        for field in ("title", "date", "summary"):
            if not isinstance(post.get(field), str) or not post[field].strip():
                raise ValueError(f"{path.name}: {field} must be nonempty text")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", post["date"]):
            raise ValueError(f"{path.name}: date must use YYYY-MM-DD")
        published = date.fromisoformat(post["date"])
        if (not isinstance(post.get("paragraphs"), list) or not post["paragraphs"]
                or any(not isinstance(p, str) or not p.strip() for p in post["paragraphs"])):
            raise ValueError(f"{path.name}: provide at least one text paragraph")
        footnotes = post.get("footnotes", [])
        if (not isinstance(footnotes, list)
                or any(not isinstance(note, str) or not note.strip() for note in footnotes)):
            raise ValueError(f"{path.name}: footnotes must be a list of text notes")
        references = [int(number) for p in post["paragraphs"]
                      for number in re.findall(r"\[\^(\d+)\]", p)]
        if sorted(references) != list(range(1, len(footnotes) + 1)):
            raise ValueError(f"{path.name}: reference each footnote once using [^1], [^2], etc.")
        posts.append({**post, "slug": path.stem, "published": published})
    return sorted(posts, key=lambda post: (post["date"], post["slug"]), reverse=True)


def date_html(post: dict) -> str:
    published = post["published"]
    label = f"{published.day} {published.strftime('%B %Y')}"
    return f'<time datetime="{post["date"]}">{label}</time>'


def page(title: str, description: str, canonical: str, schema: dict,
         body: str, prefix: str = "") -> str:
    head = page_chrome_head(
        title, description, canonical, schema,
        css_path=f"{prefix}styles.css", theme_path=f"{prefix}assets/theme.js",
        font_path=f"{prefix}assets/font-size.js", icon_path=f"{prefix}assets/favicon.svg",
    ).replace('src="assets/mathjax-config.js"', f'src="{prefix}assets/mathjax-config.js"')
    head = head.replace('<script async src="https://cdn.jsdelivr.net',
                        f'<script src="{prefix}assets/blog-math.js"></script>\n<script async src="https://cdn.jsdelivr.net')
    head = head.replace("</head>", f'<link rel="stylesheet" href="{prefix}assets/blog.css">\n</head>')
    head = head.replace("<body>", '<body class="blog-page">')
    footer = footer_html(f"{prefix}./", f"{prefix}notes.html")
    # Blog entries can be personal; the physics-note disclaimer belongs to notes.
    footer = re.sub(r'\s*<p class="footer__disclaimer">.*?</p>', "", footer, flags=re.S)
    return head + topbar("blog", f"{prefix}./", f"{prefix}notes.html") + body + footer


def build(source: Path = ROOT / "content" / "blog", root: Path = ROOT) -> None:
    posts = read_posts(source)
    output = root / "blog"
    output.mkdir(parents=True, exist_ok=True)
    expected = {f'{post["slug"]}.html' for post in posts}
    # Withdrawing a published entry must also withdraw its generated route.
    for old in output.glob("*.html"):
        if old.name not in expected:
            old.unlink()

    entries = []
    for post in posts:
        title, summary = html.escape(post["title"]), html.escape(post["summary"])
        canonical = f'blog/{post["slug"]}.html'
        entries.append(f'''<li class="blog-entry">
  {date_html(post)}
  <div><h2><a href="{canonical}">{title}<span aria-hidden="true"> ↗</span></a></h2>
  <p>{summary}</p></div>
</li>''')
        def paragraph(text: str) -> str:
            escaped = html.escape(text)
            escaped = re.sub(r"\[\^(\d+)\]", lambda m:
                f'<sup id="fnref-{m[1]}"><a href="#fn-{m[1]}" role="doc-noteref" '
                f'aria-label="Footnote {m[1]}">{m[1]}</a></sup>', escaped)
            return f"<p>{escaped}</p>"

        paragraphs = "\n".join(paragraph(p) for p in post["paragraphs"])
        notes = "".join(
            f'<li id="fn-{number}">{html.escape(note)} '
            f'<a href="#fnref-{number}" role="doc-backlink" aria-label="Back to footnote {number} reference">↩</a></li>'
            for number, note in enumerate(post.get("footnotes", []), 1)
        )
        footnotes = (f'<aside class="blog-footnotes" role="doc-endnotes" aria-label="Footnotes">'
                     f'<ol>{notes}</ol></aside>') if notes else ""
        schema = {
            "@context": "https://schema.org",
            "@graph": [{
                "@type": "BlogPosting", "headline": post["title"],
                "description": post["summary"], "datePublished": post["date"],
                "url": f"{SITE_URL}/{canonical}",
                "author": {"@type": "Person", "@id": PERSON_ID, "name": AUTHOR_NAME},
                "isPartOf": {"@type": "Blog", "url": f"{SITE_URL}/blog.html"},
            }, {
                "@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Blog", "item": f"{SITE_URL}/blog.html"},
                    {"@type": "ListItem", "position": 2, "name": post["title"], "item": f"{SITE_URL}/{canonical}"},
                ],
            }],
        }
        body = f'''<main class="blog-shell">
  <a class="blog-back" href="../blog.html">← All entries</a>
  <article>
    <header class="blog-heading"><p class="blog-eyebrow">{date_html(post)}</p><h1>{title}</h1></header>
    <div class="blog-prose">{paragraphs}</div>
    {footnotes}
  </article>
</main>'''
        article = page(post["title"], post["summary"], canonical, schema, body, "../")
        article = article.replace('property="og:type" content="website"', 'property="og:type" content="article"')
        (output / f'{post["slug"]}.html').write_text(article, encoding="utf-8")

    listing = '<ol class="blog-entries">' + "\n".join(entries) + "</ol>" if entries else '''<div class="blog-empty">
  <p class="blog-eyebrow">An open page</p>
  <h2>Nothing here yet.</h2>
  <p>New entries will appear here, one thought at a time.</p>
</div>'''
    body = f'''<main class="blog-shell">
  <header class="blog-heading">
    <p class="blog-eyebrow">Thinking aloud</p>
    <h1>Blog</h1>
    <p class="blog-intro">{DESCRIPTION}</p>
  </header>
  {listing}
</main>'''
    (root / "blog.html").write_text(page(
        "Blog", DESCRIPTION, "blog.html",
        collection_schema("Blog", DESCRIPTION, "blog.html"), body,
    ), encoding="utf-8")
    print(f"  wrote blog.html ({len(posts)} published entries)")


if __name__ == "__main__":
    build()
