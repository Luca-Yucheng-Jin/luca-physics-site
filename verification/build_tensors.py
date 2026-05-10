#!/usr/bin/env python3
"""
verification/tensors/index.html — for every \\tensor{base}{indices} call
in the .tex sources, render side-by-side:
  - LEFT  (web): apply the build-time _rewrite_tensor and feed to MathJax
                 (live render, same as the deployed page).
  - RIGHT (LaTeX): compile the original \\tensor{...}{...} expression with
                   the real tensor.sty package; render to PNG.

A match means MathJax displays the indices in distinct horizontal
columns (μ above-left, ν below-right) — the rewrite did its job.
"""

from __future__ import annotations
import html
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "build"))
from tex_to_html import _rewrite_tensor  # noqa
from svg_render import LUALATEX           # noqa

OUT = os.path.join(ROOT, "verification", "tensors")
os.makedirs(OUT, exist_ok=True)

def _balanced_brace_arg(s, i):
    """Given s[i] == '{', return (arg_text, next_i_after_closing_brace)."""
    if i >= len(s) or s[i] != "{":
        return None, i
    depth = 1
    j = i + 1
    start = j
    while j < len(s) and depth > 0:
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[start:j], j + 1
        j += 1
    return None, i


TENSOR_HEAD = re.compile(r"\\tensor\s*\{")


def collect():
    """Walk tex/*.tex and pull out every \\tensor{}{} expression with
    its surrounding line of context. Balanced-brace matching so nested
    {...} inside the indices argument (e.g. {^\\beta\\rho\\sigma}) is
    handled correctly."""
    out = []
    tex_dir = os.path.join(ROOT, "tex")
    for fn in sorted(os.listdir(tex_dir)):
        if not fn.endswith(".tex"):
            continue
        path = os.path.join(tex_dir, fn)
        with open(path) as f:
            for lineno, line in enumerate(f, start=1):
                i = 0
                while i < len(line):
                    m = TENSOR_HEAD.search(line, i)
                    if not m:
                        break
                    start = m.start()
                    # parse arg1
                    base, j = _balanced_brace_arg(line, m.end() - 1)
                    if base is None:
                        i = m.end()
                        continue
                    # skip whitespace
                    while j < len(line) and line[j] in " \t":
                        j += 1
                    if j >= len(line) or line[j] != "{":
                        i = j
                        continue
                    indices, k = _balanced_brace_arg(line, j)
                    if indices is None:
                        i = j + 1
                        continue
                    expr = line[start:k]
                    out.append({
                        "file": f"tex/{fn}",
                        "line": lineno,
                        "expr": expr,
                        "base": base,
                        "indices": indices,
                    })
                    i = k
    return out


def render_pdflatex_to_png(expr: str, out_png: str):
    """Compile a snippet wrapping the tensor expression in display math,
    using the real tensor.sty for the ground-truth render."""
    body = (
        r"\documentclass[border=4pt,preview]{standalone}"
        r"\usepackage{amsmath,amssymb,amsthm,mathtools}"
        r"\usepackage{tensor}"
        r"\begin{document}"
        r"\(\displaystyle " + expr + r"\)"
        r"\end{document}"
    )
    with tempfile.TemporaryDirectory(prefix="tensor-verify-") as tmp:
        with open(os.path.join(tmp, "x.tex"), "w") as f:
            f.write(body)
        r = subprocess.run(
            [LUALATEX, "--interaction=batchmode", "x.tex"],
            cwd=tmp, capture_output=True, check=False,
        )
        pdf = os.path.join(tmp, "x.pdf")
        if not os.path.exists(pdf):
            log_path = os.path.join(tmp, "x.log")
            tail = open(log_path).read()[-2000:] if os.path.exists(log_path) else "(no log)"
            raise RuntimeError(f"lualatex failed for {expr}\n{tail}")
        subprocess.run(
            ["gs", "-dNOPAUSE", "-dQUIET", "-dBATCH", "-sDEVICE=png16m",
             "-r240", f"-sOutputFile={out_png}", pdf],
            check=True, capture_output=True,
        )


def main():
    rows = collect()
    print(f"found {len(rows)} \\tensor expressions across {len({r['file'] for r in rows})} files")

    # Compute the rewritten form for each so the verification page can show
    # web vs latex side by side.
    for i, r in enumerate(rows):
        r["rewritten"] = _rewrite_tensor(r["expr"])
        png_name = f"expr-{i:02d}.png"
        png_path = os.path.join(OUT, png_name)
        try:
            render_pdflatex_to_png(r["expr"], png_path)
            r["png"] = png_name
        except Exception as e:
            print(f"  ! row {i}: {e}", file=sys.stderr)
            r["png"] = None

    # ----------------------------------------------------------------
    # Build the HTML
    head = r"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<title>Tensor index verification — web vs pdfLaTeX</title>

<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    packages: {'[+]': ['physics', 'boldsymbol', 'cancel', 'ams', 'configmacros', 'mathtools']}
  },
  loader: { load: ['[tex]/physics', '[tex]/boldsymbol', '[tex]/cancel', '[tex]/ams', '[tex]/configmacros', '[tex]/mathtools'] }
};
</script>
<script async src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'></script>

<style>
:root { color-scheme: light; }
body { font: 14px/1.4 -apple-system, sans-serif; max-width: 1400px;
       margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; background: #fff; }
h1 { font-size: 1.8rem; }
.row { display: grid; grid-template-columns: 32% 1fr 1fr; gap: 1rem;
       border: 1px solid #ddd; padding: 12px; background: #fff;
       margin: 6px 0; align-items: center; }
.row > div { padding: 8px 12px; }
.row > div h3 { margin: 0 0 0.4rem; font-size: 11px;
                color: #666; text-transform: uppercase;
                letter-spacing: 0.05em; font-weight: 600; }
.source-cell { font-family: 'Menlo', monospace; font-size: 11px;
               background: #f6f6f6; border-radius: 3px; }
.source-cell pre { margin: 0; white-space: pre-wrap; word-break: break-all; }
.source-cell .meta { font-size: 10px; color: #777; margin-bottom: 4px;
                     font-family: -apple-system, sans-serif; }
.web-cell { font-size: 22px; }
.latex-cell img { max-width: 100%; height: auto; vertical-align: middle; }
.legend { background: #f0f7ff; border: 1px solid #b0d4ff; padding: 12px;
          border-radius: 4px; margin-bottom: 1.5rem; }
</style>
</head>
<body>
<h1>Tensor index verification</h1>

<div class='legend'>
<strong>Goal:</strong> every <code>\tensor{base}{indices}</code> call
in the source must render with the upper and lower indices at <em>distinct
horizontal positions</em> (μ above-left, ν below-right) — never stacked
in the same column.<br><br>
<strong>Approach:</strong> the build pipeline (<code>build/tex_to_html.py:_rewrite_tensor</code>)
walks math regions and rewrites <code>\tensor{R}{^μ_{νρσ}}</code>
to <code>R^μ{}_{νρσ}</code> (empty-group trick) before MathJax sees it.
The empty <code>{}</code> separator is what makes MathJax kern the
indices into separate columns.<br><br>
The MIDDLE column below is live MathJax (same renderer as the deployed
site). The RIGHT column is ground-truth pdfLaTeX with the actual
<code>tensor.sty</code> package. They should look visually identical.
</div>
"""

    rows_html = []
    for i, r in enumerate(rows):
        rows_html.append(f"""
<div class='row' id='row-{i}'>
  <div class='source-cell'>
    <div class='meta'>{html.escape(r['file'])}:{r['line']}</div>
    <pre>{html.escape(r['expr'])}</pre>
    <div class='meta' style='margin-top:6px'>↓ rewritten</div>
    <pre>{html.escape(r['rewritten'])}</pre>
  </div>
  <div class='web-cell'>
    <h3>Web (MathJax, after rewrite)</h3>
    \\(\\displaystyle {r['rewritten']}\\)
  </div>
  <div class='latex-cell'>
    <h3>pdfLaTeX (tensor.sty)</h3>
    {f"<img src='{r['png']}' alt='pdfLaTeX render'>" if r['png'] else "<em>compile failed</em>"}
  </div>
</div>
""")

    foot = "\n</body>\n</html>"
    out_path = os.path.join(OUT, "index.html")
    with open(out_path, "w") as f:
        f.write(head + "\n".join(rows_html) + foot)
    print(f"wrote {out_path} with {len(rows)} entries")


if __name__ == "__main__":
    main()
