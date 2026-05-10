#!/usr/bin/env python3
"""
Generate verification/wick/index.html — a side-by-side comparison of
each Wick-contraction equation's web rendering vs the pdfLaTeX render.

For each equation:
  - "Web" column: the inline SVG that the build pipeline emits (read
    straight from the rendered HTML — same bytes the user sees).
  - "LaTeX" column: a PNG produced by `lualatex` (two passes) →
    `dvips/dvipdfm` → `gs` rasterisation. This is the ground-truth.
"""

from __future__ import annotations
import hashlib
import html
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "build"))
from svg_render import PREAMBLE, _wrap, KIND_MATH, DVISVGM_ENV, LUALATEX, TEXLIVE_PREFIX  # noqa

OUT = os.path.join(ROOT, "verification", "wick")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# Each entry: (label, source_file, source_line, snippet, page_slug, page_eq_label)

WICKS = [
    ("Eq. (8.40) — first definition",
     "tex/QFTschwartz.tex", 1168,
     r"""\begin{aligned}
        \wick{\c\phi(x)\c\phi(y)} \equiv
        \begin{cases}
            \big[\phi^+(x), \phi^-(y)\big] & \text{for } x^0 > y^0; \\
            \big[\phi^+(y), \phi^-(x)\big] & \text{for } y^0 > x^0,
        \end{cases}
\end{aligned}""",
     "schwartz-second-quantization", "(8.40)"),

    ("Eq. (8.41) — Wick's theorem two-field case",
     "tex/QFTschwartz.tex", 1179,
     r"T\{\phi_0(x)\phi_0(y)\} = :\phi_0(x)\phi_0(y) + \wick{\c\phi_0(x) \c\phi_0(y)}.",
     "schwartz-second-quantization", "(8.41)"),

    ("Eq. (8.46) — multi-line aligned, two cases",
     "tex/QFTschwartz.tex", 1219,
     r"""\begin{aligned}
        \wick{\c\phi(x)\c\phi(y)}=\bra{0}\wick{\c\phi(x)\c\phi(y)}\ket{0}&=
        \begin{cases}
        \bra{0}\big[\phi^+(x), \phi^-(y)\big]\ket{0} & \text{for } x^0 > y^0; \\
        \bra{0}\big[\phi^+(y), \phi^-(x)\big]\ket{0} & \text{for } y^0 > x^0,
    \end{cases}
    \\
    &=
    \begin{cases}
        \bra{0}\phi^+(x)\phi^-(y)\ket{0} & \text{for } x^0 > y^0; \\
        \bra{0}\phi^+(y)\phi^-(x)\ket{0} & \text{for } y^0 > x^0,
    \end{cases}
\end{aligned}""",
     "schwartz-second-quantization", "(8.46)"),

    ("Eq. (8.47) — Feynman propagator identification",
     "tex/QFTschwartz.tex", 1234,
     r"\wick{\c\phi(x)\c\phi(y)} = D_F(x, y) = \int \frac{d^4q }{(2\pi)^4} \frac{i}{q^2 - m^2 +i\epsilon} e^{iq(x-y)}.",
     "schwartz-second-quantization", "(8.47)"),

    ("Eq. (8.49) — multi-pair contraction (4 levels)",
     "tex/QFTschwartz.tex", 1247,
     r"\wick{\c1 \phi_0(x_1)\c2 \phi_0(x_2)\c1 \phi_0(x)\c3 \phi_0(x)\c4 \phi_0(x)\c2 \phi_0(y)\c3 \phi_0(y)\c4 \phi_0(y)} = D_{1x}D_{2y}D_{xy}^2.",
     "schwartz-second-quantization", "(8.49)"),

    ("Eq. (13.49) — schwartz-qed-tree two-point function",
     "tex/QFTschwartz.tex", 5436,
     r"\wick{\c\phi(x_1)\c\phi(x_2)} = \bra{0}T\{\phi(x_1)\phi(x_2)\}\ket{0}.",
     "schwartz-qed-tree", "(13.49)"),
]


def render_pdflatex_to_png(snippet: str, out_png: str) -> str:
    """Compile snippet via lualatex (two passes for simpler-wick) → PDF →
    PNG via Ghostscript at 200 DPI."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix="wick-verify-") as tmp:
        # Use a slightly larger border so we never crop the contraction arcs.
        tex_body = (
            r"\documentclass[border={4pt 16pt 4pt 4pt},preview]{standalone}"
            r"\usepackage{amsmath,amssymb,amsthm,mathtools}"
            r"\usepackage{physics}"
            r"\usepackage{tensor}"
            r"\usepackage{slashed}"
            r"\usepackage{dsfont}"
            r"\usepackage{mathrsfs}"
            r"\usepackage{cancel}"
            r"\usepackage{simpler-wick}"
            r"\usepackage{tikz}"
            r"\usepackage[compat=1.1.0]{tikz-feynman}"
            r"\providecommand{\Tilde}[1]{\tilde{#1}}"
            r"\providecommand{\Tr}{\operatorname{Tr}}"
            r"\begin{document}"
            r"\[" + snippet + r"\]"
            r"\end{document}"
        )
        with open(os.path.join(tmp, "x.tex"), "w") as f:
            f.write(tex_body)
        # two passes for simpler-wick's overlay
        for _ in range(2):
            subprocess.run(
                [LUALATEX, "--interaction=batchmode", "x.tex"],
                cwd=tmp, capture_output=True, check=False,
            )
        pdf = os.path.join(tmp, "x.pdf")
        if not os.path.exists(pdf):
            log = os.path.join(tmp, "x.log")
            tail = open(log).read()[-2000:] if os.path.exists(log) else "(no log)"
            raise RuntimeError(f"lualatex failed: {tail}")
        subprocess.run(
            ["gs", "-dNOPAUSE", "-dQUIET", "-dBATCH", "-sDEVICE=png16m",
             "-r200", f"-sOutputFile={out_png}", pdf],
            check=True, capture_output=True,
        )
    return out_png


def find_web_svg(slug: str, eq_label: str) -> str | None:
    """Pull the matching <figure class="wick-figure">…</figure> from the
    rendered HTML page so we show exactly what the user would see."""
    html_path = os.path.join(ROOT, "notes", f"{slug}.html")
    if not os.path.exists(html_path):
        return None
    with open(html_path) as f:
        html_text = f.read()
    figs = re.findall(r'<figure class="wick-figure">(.*?)</figure>',
                      html_text, re.DOTALL)
    # We can't easily map figure-index to equation label without parsing the
    # surrounding HTML.  Heuristic: the equations come in source order, so the
    # k-th wick-figure on a given page corresponds to the k-th wick equation.
    return figs


# Map page → list of svgs in source order
_svg_cache: dict[str, list[str]] = {}


def get_web_svg(slug: str, idx_on_page: int) -> str:
    if slug not in _svg_cache:
        figs = find_web_svg(slug, "")
        _svg_cache[slug] = figs or []
    figs = _svg_cache[slug]
    if idx_on_page >= len(figs):
        return f"<em>(figure {idx_on_page} not found in {slug})</em>"
    return figs[idx_on_page]


def main():
    page_idx: dict[str, int] = {}
    rows = []
    for label, src_file, src_line, snippet, slug, eq_label in WICKS:
        idx = page_idx.get(slug, 0)
        page_idx[slug] = idx + 1

        # 1. pdfLaTeX → PNG
        png_name = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") + ".png"
        png_path = os.path.join(OUT, png_name)
        try:
            render_pdflatex_to_png(snippet, png_path)
        except Exception as e:
            print(f"  ! {label}: {e}", file=sys.stderr)
            png_name = None

        # 2. Pull web SVG
        web_svg = get_web_svg(slug, idx)

        rows.append({
            "label": label,
            "source_file": src_file,
            "source_line": src_line,
            "snippet": snippet,
            "page_slug": slug,
            "eq_label": eq_label,
            "png": png_name,
            "web_svg": web_svg,
        })

    # 3. Write index.html
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<title>Wick verification — web vs pdfLaTeX</title>",
        "<style>",
        ":root { color-scheme: light; }",
        "body { font: 14px/1.4 -apple-system, sans-serif; max-width: 1400px;",
        "       margin: 2rem auto; padding: 0 1rem; color: #1a1a1a;",
        "       background: #ffffff; }",
        "h1 { font-size: 1.8rem; }",
        "h2 { font-size: 1.1rem; margin-top: 2.5rem;",
        "     border-bottom: 1px solid #ccc; padding-bottom: 4px; }",
        ".source { background: #f6f6f6; padding: 8px 12px; border-radius: 4px;",
        "          font-family: 'Menlo', monospace; font-size: 12px;",
        "          white-space: pre-wrap; word-break: break-all; margin: 8px 0 16px; }",
        ".compare { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;",
        "           border: 1px solid #ddd; padding: 16px; background: #fff; }",
        ".compare > div { padding: 12px; min-height: 80px; }",
        ".compare > div h3 { margin: 0 0 0.5rem; font-size: 12px;",
        "                    color: #666; text-transform: uppercase;",
        "                    letter-spacing: 0.05em; font-weight: 600; }",
        ".compare img { max-width: 100%; height: auto; }",
        ".compare svg { max-width: 100%; height: auto; color: #1a1a1a; }",
        ".meta { font-size: 12px; color: #777; margin-bottom: 8px; }",
        "</style>",
        "</head><body>",
        "<h1>Wick contraction verification</h1>",
        f"<p class='meta'>{len(rows)} equations across schwartz-second-quantization (5) and schwartz-qed-tree (1).",
        " Left column: the SVG inlined into the live web page (build/svg_render.py output).",
        " Right column: ground-truth pdfLaTeX render (lualatex 2-pass + gs PNG, 200dpi).",
        " Both columns should be visually identical.</p>",
    ]
    for row in rows:
        html_lines.append(f"<h2>{html.escape(row['label'])}</h2>")
        html_lines.append(f"<div class='meta'>{row['source_file']}:{row['source_line']} · "
                          f"<a href='../../notes/{row['page_slug']}.html'>{row['page_slug']}.html</a></div>")
        html_lines.append("<details><summary>source LaTeX</summary>")
        html_lines.append(f"<pre class='source'>{html.escape(row['snippet'])}</pre>")
        html_lines.append("</details>")
        html_lines.append("<div class='compare'>")
        html_lines.append("  <div><h3>Web (inline SVG)</h3>")
        html_lines.append(f"  {row['web_svg']}")
        html_lines.append("  </div>")
        html_lines.append("  <div><h3>pdfLaTeX (ground truth)</h3>")
        if row['png']:
            html_lines.append(f"  <img src='{row['png']}' alt='pdfLaTeX render'>")
        else:
            html_lines.append("  <em>compile failed — see stderr</em>")
        html_lines.append("  </div>")
        html_lines.append("</div>")
    html_lines.append("</body></html>")
    out = os.path.join(OUT, "index.html")
    with open(out, "w") as f:
        f.write("\n".join(html_lines))
    print(f"wrote {out} with {len(rows)} entries")


if __name__ == "__main__":
    main()
