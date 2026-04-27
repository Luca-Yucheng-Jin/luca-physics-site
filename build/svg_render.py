"""
svg_render.py — render TikZ / tikz-feynman / pgfplots / Wick-contraction
LaTeX snippets to inline SVG via lualatex + dvisvgm.

The rendered SVG is content-hashed and cached under build/svg-cache/, so
subsequent runs only re-compile changed snippets.

Each call to render() returns an inline-SVG string ready to drop into the
HTML output. The SVG has had hardcoded #000 strokes/fills swapped for
currentColor, so it inherits the page's text color (dark-mode safe).
"""

from __future__ import annotations
import hashlib
import os
import re
import shutil
import subprocess
import tempfile

# ---------------------------------------------------------------------------
# Toolchain location

TEXLIVE_PREFIX = "/opt/homebrew/Cellar/texlive/20260301"
LUALATEX = "/opt/homebrew/bin/lualatex"
DVISVGM = "/opt/homebrew/bin/dvisvgm"

# Env vars that make dvisvgm find tex.pro / texps.pro / special.pro / color.pro
# in the Homebrew TeXLive prefix (its own kpathsea would otherwise look in
# /opt/homebrew/Cellar/dvisvgm/... which is empty).
DVISVGM_ENV = {
    "TEXMFCNF": f"{TEXLIVE_PREFIX}/share/texmf-dist/web2c",
    "TEXMF":    f"{TEXLIVE_PREFIX}/share/texmf-dist",
    "TEXMFDIST": f"{TEXLIVE_PREFIX}/share/texmf-dist",
    "TEXMFROOT": f"{TEXLIVE_PREFIX}/share",
}

# Cache dir — sibling to this file. Hash → SVG content.
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "svg-cache")

# ---------------------------------------------------------------------------
# Standalone document preamble. Mirrors the user's elegantphys.sty + the
# packages actually used in tex/*.tex.

PREAMBLE = r"""
\documentclass[border=2pt,preview]{standalone}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsthm,mathtools}
\usepackage{physics}
\usepackage{tensor}
\usepackage{slashed}
\usepackage{dsfont}
\usepackage{mathrsfs}
\usepackage{cancel}
\usepackage{simpler-wick}
\usepackage{tikz}
\usepackage[compat=1.1.0]{tikz-feynman}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{
  arrows.meta, positioning, shapes.geometric,
  decorations.markings, decorations.pathmorphing,
  patterns.meta, calc, intersections
}
% --- User-defined macros mirroring tex/QFTsoln.tex preamble + page template ---
\newcommand{\R}{\mathbb{R}}
\newcommand{\C}{\mathbb{C}}
\newcommand{\Z}{\mathbb{Z}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\Q}{\mathbb{Q}}
\newcommand{\A}{\mathcal{A}}
\newcommand{\Lagrangian}{\mathcal{L}}
\newcommand{\Cdot}{\boldsymbol{\cdot}}
\providecommand{\Tilde}[1]{\tilde{#1}}
\providecommand{\Tr}{\operatorname{Tr}}
"""

# ---------------------------------------------------------------------------
# Snippet kinds. Each kind tells render() how to wrap the inner snippet
# in \begin{document} / \end{document}.

KIND_TIKZ      = "tikz"        # raw \begin{tikzpicture}…\end{tikzpicture} or \feynmandiagram{…};
KIND_AXIS      = "axis"        # raw \begin{tikzpicture}\begin{axis}…\end{axis}\end{tikzpicture}
KIND_MATH      = "math"        # math expression (e.g. a Wick equation) — wrapped in \[ \]
KIND_RAW       = "raw"         # snippet is its own complete document body


def _hash(content: str) -> str:
    """Stable content hash for cache key. Includes preamble version, so
    a preamble bump invalidates everything automatically."""
    h = hashlib.sha256()
    h.update(PREAMBLE.encode("utf-8"))
    h.update(b"\x00")
    h.update(content.encode("utf-8"))
    return h.hexdigest()[:24]


def _cache_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.svg")


def _wrap(snippet: str, kind: str) -> str:
    """Build a complete standalone .tex document containing the snippet."""
    snippet = snippet.strip()
    if kind == KIND_TIKZ or kind == KIND_AXIS:
        body = snippet
    elif kind == KIND_MATH:
        body = f"\\[{snippet}\\]"
    elif kind == KIND_RAW:
        body = snippet
    else:
        raise ValueError(f"unknown kind: {kind}")
    return f"{PREAMBLE}\n\\begin{{document}}\n{body}\n\\end{{document}}\n"


def _strip_xml_decl(svg: str) -> str:
    """Drop the <?xml ?> processing instruction and the leading comment so the
    SVG can be inlined inside HTML without choking the parser."""
    svg = re.sub(r"<\?xml[^?]*\?>\s*", "", svg)
    svg = re.sub(r"<!--[^-]*(?:-(?!->)[^-]*)*-->\s*", "", svg)
    return svg.strip()


def _rewrite_to_currentcolor(svg: str) -> str:
    """Swap hardcoded black strokes/fills for currentColor so the SVG inherits
    the page's text color in both light and dark mode. Leave non-black colors
    (e.g. tikz-feynman patterns, intentional gray fills) untouched.

    dvisvgm emits attributes with single quotes by default — handle both."""
    def repl(m):
        attr, q, val = m.group(1), m.group(2), m.group(3).lower()
        if val in ("#000", "#000000", "black"):
            return f'{attr}={q}currentColor{q}'
        return m.group(0)
    return re.sub(
        r"(stroke|fill)=(['\"])(#[0-9a-fA-F]{3,6}|black|none)\2",
        repl, svg,
    )


def _post_process(svg: str) -> str:
    svg = _strip_xml_decl(svg)
    svg = _rewrite_to_currentcolor(svg)
    return svg


def _compile(tex: str, key: str) -> str:
    """Run lualatex → dvisvgm in a temp dir; return inline SVG content."""
    with tempfile.TemporaryDirectory(prefix="svg-render-") as tmp:
        tex_path = os.path.join(tmp, "diag.tex")
        with open(tex_path, "w") as f:
            f.write(tex)

        # 1. lualatex --output-format=dvi diag.tex
        try:
            r = subprocess.run(
                [LUALATEX, "--interaction=batchmode",
                 "--output-format=dvi", "diag.tex"],
                cwd=tmp, capture_output=True, text=True, timeout=120,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"lualatex timed out for cache key {key}")
        dvi = os.path.join(tmp, "diag.dvi")
        if not os.path.exists(dvi):
            log = ""
            log_path = os.path.join(tmp, "diag.log")
            if os.path.exists(log_path):
                log = open(log_path, errors="replace").read()[-2000:]
            raise RuntimeError(
                f"lualatex failed for cache key {key}\n"
                f"stdout: {r.stdout[-500:]}\n"
                f"--- log tail ---\n{log}"
            )

        # 2. dvisvgm --no-fonts → diag.svg
        env = {**os.environ, **DVISVGM_ENV}
        r = subprocess.run(
            [DVISVGM, "--no-fonts", "--exact-bbox",
             "-o", "diag.svg", "diag.dvi"],
            cwd=tmp, capture_output=True, text=True, env=env, timeout=60,
        )
        svg_path = os.path.join(tmp, "diag.svg")
        if not os.path.exists(svg_path):
            raise RuntimeError(
                f"dvisvgm failed for cache key {key}\n"
                f"stderr: {r.stderr[-1000:]}"
            )
        with open(svg_path) as f:
            return f.read()


def render(snippet: str, kind: str = KIND_TIKZ) -> str:
    """Render `snippet` to inline SVG, with caching.

    Returns the SVG markup ready to drop into HTML. On compile failure,
    raises RuntimeError with the LaTeX log tail."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    tex = _wrap(snippet, kind)
    key = _hash(tex)
    cache = _cache_path(key)
    if os.path.exists(cache):
        with open(cache) as f:
            return f.read()
    raw = _compile(tex, key)
    svg = _post_process(raw)
    # Write atomically so a Ctrl-C mid-write doesn't poison the cache.
    tmp_path = cache + ".tmp"
    with open(tmp_path, "w") as f:
        f.write(svg)
    os.replace(tmp_path, cache)
    return svg


def render_or_fallback(snippet: str, kind: str, fallback: str) -> str:
    """Like render() but returns `fallback` HTML on compile failure rather
    than raising. Used at build time so one bad diagram doesn't kill the
    whole site rebuild — the failure prints to stderr and we move on."""
    try:
        return render(snippet, kind)
    except Exception as e:
        import sys
        print(f"  ! svg_render: {e}", file=sys.stderr)
        return fallback


# ---------------------------------------------------------------------------
# CLI for dev / testing

def _main():
    import sys
    if len(sys.argv) < 2:
        print("usage: svg_render.py {wick|feyn|loop|smoke|<file.tex>}", file=sys.stderr)
        sys.exit(1)
    arg = sys.argv[1]
    samples = {
        "wick": (KIND_MATH,
                 r"\wick{\c1 \phi(x_1)\c2 \phi(x_2)\c1 \phi(x)\c3 \phi(x)\c4 \phi(x)\c2 \phi(y)\c3 \phi(y)\c4 \phi(y)} = D_{1x}D_{2y}D_{xy}^2"),
        "feyn": (KIND_TIKZ,
                 r"\begin{tikzpicture}\feynmandiagram [horizontal=a to b]{i1 [particle=\(e^-\)] -- [fermion] a -- [fermion] i2 [particle=\(e^-\)], a -- [photon, momentum=\(q\)] b [blob],};\end{tikzpicture}"),
        "loop": (KIND_TIKZ,
                 r"\begin{tikzpicture}\begin{feynman}\vertex (a); \vertex [right=1.5cm of a] (b); \vertex [right=1.5cm of b] (c); \vertex [right=1.5cm of c] (d);\diagram* {(a) -- [photon, momentum=\(q\)] (b),(b) -- [fermion, half left, momentum=\(k\)] (c),(c) -- [fermion, half left, momentum=\(k+q\)] (b),(c) -- [photon, momentum=\(q\)] (d),};\end{feynman}\end{tikzpicture}"),
        "smoke": (KIND_TIKZ,
                  r"\begin{tikzpicture}\draw (0,0) -- (1,1);\end{tikzpicture}"),
    }
    if arg in samples:
        kind, snip = samples[arg]
        svg = render(snip, kind)
        print(svg)
    elif os.path.exists(arg):
        with open(arg) as f:
            snip = f.read()
        svg = render(snip, KIND_RAW)
        print(svg)
    else:
        print(f"unknown sample / file: {arg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _main()
