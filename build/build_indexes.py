#!/usr/bin/env python3
"""
build_indexes.py — generate per-category index pages plus the top-level
notes.html overview from a single source-of-truth list.

Each category has:
  - slug  : URL component, used in notes-<slug>.html
  - title : displayed in <h1>
  - blurb : 1-line description for the top-level overview
  - body  : ready-to-inject HTML (the <ul class="catalogue"> and any
            interleaved <h3> sub-headings)
"""

from __future__ import annotations
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Shared chrome (header + footer). Rendered once per page.

def page_chrome_head(title: str, description: str, css_path: str = "styles.css",
                     theme_path: str = "assets/theme.js",
                     font_path: str = "assets/font-size.js",
                     icon_path: str = "assets/favicon.svg") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Yucheng (Luca) Jin</title>
<meta name="description" content="{description}">

<link rel="icon" type="image/svg+xml" href="{icon_path}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<link rel="stylesheet" href="{css_path}">

<script src="{theme_path}"></script>
<script src="{font_path}"></script>
</head>
<body>"""


def topbar(active: str, index_path: str = "index.html",
           notes_path: str = "notes.html",
           research_path: str = "research.html") -> str:
    """`active` ∈ {'about', 'notes', 'research'} marks the current nav item."""
    a_about = ' class="is-active"' if active == "about" else ""
    a_notes = ' class="is-active"' if active == "notes" else ""
    a_research = ' class="is-active"' if active == "research" else ""
    return f"""
<header class="topbar">
  <a href="{index_path}" class="topbar__brand">Yucheng (Luca) Jin <small>BSc · Imperial</small></a>
  <nav class="topbar__nav">
    <a href="{index_path}"{a_about}>About</a>
    <a href="{notes_path}"{a_notes}>Notes</a>
    <a href="{research_path}"{a_research}>Research</a>
    <a href="mailto:luca.jin@outlook.com">Contact</a>
    <button class="font-toggle" type="button" data-font-size="dec" aria-label="Decrease font size" title="Decrease font size">A<span class="font-toggle__small">−</span></button>
    <button class="font-toggle" type="button" data-font-size="inc" aria-label="Increase font size" title="Increase font size">A<span class="font-toggle__large">+</span></button>
    <button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch to dark theme" title="Toggle theme">
      <svg class="icon-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/></svg>
      <svg class="icon-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
    </button>
  </nav>
</header>"""


def footer_html(index_path: str = "index.html",
                research_path: str = "research.html") -> str:
    return f"""
<footer class="footer">
  <span>© 2026 Yucheng (Luca) Jin</span>
  <span>
    <a href="{index_path}">About</a> ·
    <a href="{research_path}">Research</a> ·
    <a href="mailto:luca.jin@outlook.com">Email</a>
  </span>
</footer>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Per-category catalogue body. Roman numerals are kept exactly as the user
# had them in the original notes.html.

def roman(n: int) -> str:
    """Render n as Roman numerals (1 → 'I', 4 → 'IV', etc.)."""
    pairs = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
             (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
             (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'),
             (1, 'I')]
    out = []
    for v, s in pairs:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


CATEGORIES = [
    {
        "slug": "essays",
        "title": "Long-form essays",
        "blurb": "Sustained essays that develop one idea start-to-finish.",
        "tag": "1 essay",
        "body": """    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">I.</span>
        <span class="catalogue__main">
          <a href="notes/path-integral.html">Path Integrals and the Quantum–Statistical Correspondence</a>
          <span class="catalogue__desc">Imperial Year-2 essay — Feynman's path integral, Wick rotation, and the partition function.</span>
        </span>
        <span class="catalogue__tag">Essay</span>
      </li>
    </ul>""",
    },
    {
        "slug": "qft",
        "title": "Quantum Field Theory",
        "blurb": "Peskin solved problems, Tong PS1–3, and Schwartz chapter notes.",
        "tag": "12 notes",
        "body": """    <h3>Peskin &amp; Schroeder — solved problems</h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">II.</span>
        <span class="catalogue__main">
          <a href="notes/peskin-6-2.html">Equivalent Photon Approximation</a>
          <span class="catalogue__desc">Peskin &amp; Schroeder, Problem 6.2.</span>
        </span>
        <span class="catalogue__tag">Ch. 6</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">III.</span>
        <span class="catalogue__main">
          <a href="notes/peskin-7.html">Alternative Regulators in QED</a>
          <span class="catalogue__desc">Peskin &amp; Schroeder, Chapter 7 — Pauli–Villars vs. dimensional regularization.</span>
        </span>
        <span class="catalogue__tag">Ch. 7</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">IV.</span>
        <span class="catalogue__main">
          <a href="notes/peskin-final.html">Final Project — Radiation of Gluon Jets</a>
          <span class="catalogue__desc">Peskin &amp; Schroeder, end-of-book project.</span>
        </span>
        <span class="catalogue__tag">Final</span>
      </li>
    </ul>

    <h3>Tong QFT — problem sheets</h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">PS1.</span>
        <span class="catalogue__main">
          <a href="notes/tong-qft-ps1.html">Lorentz, Symmetries &amp; Currents</a>
          <span class="catalogue__desc">SO(3), infinitesimal Lorentz, energy-momentum tensor (incl. EM field), Proca, scale invariance.</span>
        </span>
        <span class="catalogue__tag">Tong PS1</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">PS2.</span>
        <span class="catalogue__main">
          <a href="notes/tong-qft-ps2.html">Canonical Quantization &amp; the Free Scalar</a>
          <span class="catalogue__desc">String quantization, free scalar, normal ordering, Yukawa, Wick's theorem, Feynman propagator.</span>
        </span>
        <span class="catalogue__tag">Tong PS2</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">PS3.</span>
        <span class="catalogue__main">
          <a href="notes/tong-qft-ps3.html">Dirac Field &amp; Spin-Statistics</a>
          <span class="catalogue__desc">Clifford algebra, Lorentz from γ-matrices, traces, plane-wave spinors, canonical quantisation.</span>
        </span>
        <span class="catalogue__tag">Tong PS3</span>
      </li>
    </ul>

    <h3>Schwartz — chapter notes</h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">V.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-classical-field.html">Classical Field Theory</a>
          <span class="catalogue__desc">Schwartz, Ch. 1–3 — Euler–Lagrange, Noether, Green's functions.</span>
        </span>
        <span class="catalogue__tag">Ch. 1–3</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">VI.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-second-quantization.html">Second Quantization &amp; LSZ Reduction</a>
          <span class="catalogue__desc">Schwartz, Ch. 2–6 — from the harmonic oscillator to the S-matrix and the Feynman propagator.</span>
        </span>
        <span class="catalogue__tag">Ch. 2–6</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">VII.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-spin-1.html">Spin 1, Gauge Invariance, Photon Propagator</a>
          <span class="catalogue__desc">Schwartz, Ch. 8–9 — quantising massless spin-1, Ward identity, scalar QED.</span>
        </span>
        <span class="catalogue__tag">Ch. 8–9</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">VIII.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-spinors.html">Spinors, Dirac Equation, CPT</a>
          <span class="catalogue__desc">Schwartz, Ch. 10–11 — Lorentz reps, Weyl/Majorana, charge conjugation, parity, time reversal.</span>
        </span>
        <span class="catalogue__tag">Ch. 10–11</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">IX.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-qed-tree.html">QED Tree Amplitudes</a>
          <span class="catalogue__desc">Schwartz, Ch. 13 — e+e− → μ+μ− and Rutherford scattering from the Feynman rules.</span>
        </span>
        <span class="catalogue__tag">Ch. 13</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">X.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-path-integrals.html">Path Integrals (in QFT)</a>
          <span class="catalogue__desc">Schwartz, Ch. 14 — from QM to functional integrals over fields.</span>
        </span>
        <span class="catalogue__tag">Ch. 14</span>
      </li>
    </ul>""",
    },
    {
        "slug": "advanced",
        "title": "General Relativity & Beyond",
        "blurb": "Brans–Dicke, 11d supergravity, and PSI QFT II finite-temperature correlators.",
        "tag": "3 notes",
        "body": """    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">α.</span>
        <span class="catalogue__main">
          <a href="notes/gr-brans-dicke.html">Brans–Dicke Theory</a>
          <span class="catalogue__desc">Tong GR PS3 Q2 — scalar-tensor gravity and the variation of Newton's constant.</span>
        </span>
        <span class="catalogue__tag">Tong GR</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">β.</span>
        <span class="catalogue__main">
          <a href="notes/psi-11d-supergravity.html">11-Dimensional Supergravity</a>
          <span class="catalogue__desc">PSI Strings PS1 Q3 — graviton, gravitino, and three-form on the maximal supergravity algebra.</span>
        </span>
        <span class="catalogue__tag">PSI Strings</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">γ.</span>
        <span class="catalogue__main">
          <a href="notes/psi-correlation-functions-qm.html">Correlation Functions in Quantum Mechanics</a>
          <span class="catalogue__desc">PSI QFT II PS1 — Euclidean / real-time propagators of the harmonic oscillator at finite temperature.</span>
        </span>
        <span class="catalogue__tag">PSI QFT II</span>
      </li>
    </ul>""",
    },
    {
        "slug": "qm",
        "title": "Quantum Mechanics",
        "blurb": "Bound-state existence, parity arguments, factorisation method.",
        "tag": "3 notes",
        "body": """    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XI.</span>
        <span class="catalogue__main">
          <a href="notes/qm-bound-states.html">Non-Degeneracy &amp; Reality of Bound States in 1D</a>
          <span class="catalogue__desc">D. Tong, <em>Quantum Mechanics</em>, PS1 Q3.</span>
        </span>
        <span class="catalogue__tag">Tong QM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XII.</span>
        <span class="catalogue__main">
          <a href="notes/qm-shallow-well.html">Absence of Odd-Parity Bound States in a Shallow Square Well</a>
          <span class="catalogue__desc">D. Tong, <em>Quantum Mechanics</em>, PS1 Q7.</span>
        </span>
        <span class="catalogue__tag">Tong QM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XIII.</span>
        <span class="catalogue__main">
          <a href="notes/qm-sech-squared.html">Factorisation Method for the Sech-Squared Potential</a>
          <span class="catalogue__desc">D. Tong, <em>Quantum Mechanics</em>, PS1 Q8.</span>
        </span>
        <span class="catalogue__tag">Tong QM</span>
      </li>
    </ul>""",
    },
    {
        "slug": "ed",
        "title": "Electrodynamics",
        "blurb": "Tong EM problem-sheet selections — radiation, Liénard–Wiechert, dielectric boundaries.",
        "tag": "8 notes",
        "body": """    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XIV.</span>
        <span class="catalogue__main">
          <a href="notes/ed-retarded.html">Retarded Potentials and Far-Field Radiation</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS7 Q4.</span>
        </span>
        <span class="catalogue__tag">Tong EM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XV.</span>
        <span class="catalogue__main">
          <a href="notes/ed-lienard-wiechert.html">Liénard–Wiechert Potential and the Field Tensor</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS7 Q6.</span>
        </span>
        <span class="catalogue__tag">Tong EM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XVI.</span>
        <span class="catalogue__main">
          <a href="notes/ed-relativistic-uniform.html">Relativistic Motion in a Uniform Electric Field</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS3 Q9.</span>
        </span>
        <span class="catalogue__tag">Tong EM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XVII.</span>
        <span class="catalogue__main">
          <a href="notes/ed-gauge-plane-wave.html">Gauge Transformation of a Plane EM Wave</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS3 Q5.</span>
        </span>
        <span class="catalogue__tag">Tong EM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XVIII.</span>
        <span class="catalogue__main">
          <a href="notes/ed-moving-mirror.html">Reflection of an EM Wave from a Moving Mirror</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS3 Q7.</span>
        </span>
        <span class="catalogue__tag">Tong EM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XIX.</span>
        <span class="catalogue__main">
          <a href="notes/ed-covariant-ohms.html">Covariant Form of Ohm's Law</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS3 Q10.</span>
        </span>
        <span class="catalogue__tag">Tong EM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XX.</span>
        <span class="catalogue__main">
          <a href="notes/ed-dielectric-sphere.html">Dielectric Sphere in a Uniform Electric Field</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS8 Q1.</span>
        </span>
        <span class="catalogue__tag">Tong EM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXI.</span>
        <span class="catalogue__main">
          <a href="notes/ed-frustrated-tir.html">Frustrated Total Internal Reflection &amp; Evanescent Waves</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS8 Q3.</span>
        </span>
        <span class="catalogue__tag">Tong EM</span>
      </li>
    </ul>""",
    },
    {
        "slug": "mm",
        "title": "Mathematical Methods",
        "blurb": "Complex methods (Santos PS), Cambridge variational principles.",
        "tag": "6 notes",
        "body": """    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XXII.</span>
        <span class="catalogue__main">
          <a href="notes/mm-jordans-lemma.html">Jordan's Lemma</a>
          <span class="catalogue__desc">Standard statement, proof, and applications.</span>
        </span>
        <span class="catalogue__tag">Complex Analysis</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXIII.</span>
        <span class="catalogue__main">
          <a href="notes/mm-convolution-fourier.html">Convolution and Fourier Representation of e<sup>-|x|</sup></a>
          <span class="catalogue__desc">J. E. Santos, Cambridge Part IB Complex Methods, PS3 Q2.</span>
        </span>
        <span class="catalogue__tag">Santos CM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXIV.</span>
        <span class="catalogue__main">
          <a href="notes/mm-residues.html">Residues at Simple and Higher-Order Poles</a>
          <span class="catalogue__desc">J. E. Santos, Cambridge Part IB Complex Methods, PS2 Q7.</span>
        </span>
        <span class="catalogue__tag">Santos CM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXV.</span>
        <span class="catalogue__main">
          <a href="notes/mm-contour-integration.html">Contour Integration via Residues and Cauchy</a>
          <span class="catalogue__desc">J. E. Santos, Cambridge Part IB Complex Methods, PS2 Q9.</span>
        </span>
        <span class="catalogue__tag">Santos CM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXVI.</span>
        <span class="catalogue__main">
          <a href="notes/mm-laplace-bromwich.html">Laplace Transform of t<sup>-1/2</sup> and the Bromwich Contour</a>
          <span class="catalogue__desc">J. E. Santos, Cambridge Part IB Complex Methods, PS3 Q12.</span>
        </span>
        <span class="catalogue__tag">Santos CM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXVII.</span>
        <span class="catalogue__main">
          <a href="notes/mm-variational-euler.html">Variational Derivation of Euler's Equation for Inviscid Flow</a>
          <span class="catalogue__desc">Cambridge Part II Variational Principles, PS2 Q9.</span>
        </span>
        <span class="catalogue__tag">VarPrin</span>
      </li>
    </ul>""",
    },
    {
        "slug": "de",
        "title": "Differential Equations",
        "blurb": "Green's-function and method-of-images problems.",
        "tag": "3 notes",
        "body": """    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XXVIII.</span>
        <span class="catalogue__main">
          <a href="notes/de-greens-function.html">Green's Function with Heaviside Forcing</a>
          <span class="catalogue__desc">Imperial College, Carlo Contaldi DE, PS9 Q4.</span>
        </span>
        <span class="catalogue__tag">Imperial DE</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXIX.</span>
        <span class="catalogue__main">
          <a href="notes/de-images-laplace.html">Laplace Operator in 3D — Method of Images</a>
          <span class="catalogue__desc">Imperial College, Carlo Contaldi DE, PS9 Q5.</span>
        </span>
        <span class="catalogue__tag">Imperial DE</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXX.</span>
        <span class="catalogue__main">
          <a href="notes/de-greens-identity-halfspace.html">Green's Identity &amp; Method of Images for the Half-Space</a>
          <span class="catalogue__desc">Cambridge Part IB past paper 2025, 14D.</span>
        </span>
        <span class="catalogue__tag">Cambridge IB</span>
      </li>
    </ul>""",
    },
    {
        "slug": "tdsp",
        "title": "Thermodynamics & Statistical Physics",
        "blurb": "Joule–Thomson, water near the triple point, partition functions.",
        "tag": "4 notes",
        "body": """    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XXXI.</span>
        <span class="catalogue__main">
          <a href="notes/tdsp-joule-thomson.html">The Joule–Thomson Process</a>
          <span class="catalogue__desc">D. Tong, <em>Statistical Physics</em>, PS4 Q4.</span>
        </span>
        <span class="catalogue__tag">Tong SP</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXXII.</span>
        <span class="catalogue__main">
          <a href="notes/tdsp-adiabatic-water.html">Adiabatic Compression of Water Near the Triple Point</a>
          <span class="catalogue__desc">Imperial 2023 TPSM paper, Q3.</span>
        </span>
        <span class="catalogue__tag">Imperial TPSM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXXIII.</span>
        <span class="catalogue__main">
          <a href="notes/tdsp-spin-half.html">Partition Function of a Spin-½ System</a>
          <span class="catalogue__desc">D. Tong, <em>Statistical Physics</em>, PS1 Q3.</span>
        </span>
        <span class="catalogue__tag">Tong SP</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXXIV.</span>
        <span class="catalogue__main">
          <a href="notes/tdsp-interacting-spin.html">Heat Capacity of an Interacting Spin System</a>
          <span class="catalogue__desc">D. Tong, <em>Statistical Physics</em>, PS1 Q4.</span>
        </span>
        <span class="catalogue__tag">Tong SP</span>
      </li>
    </ul>""",
    },
]


# ---------------------------------------------------------------------------
# Page templates

def category_page(cat: dict) -> str:
    """One per-category index — heading, breadcrumb back to top-level
    notes.html, and the catalogue body."""
    description = f"Notes catalogue: {cat['title']} — {cat['blurb']}"
    return (
        page_chrome_head(f"{cat['title']} — Notes", description)
        + topbar(active="notes")
        + f"""
<main class="page page--index">

  <div class="note__breadcrumb">
    <a href="notes.html">Notes</a> &nbsp;·&nbsp; {cat['title']}
  </div>

  <section class="hero">
    <div class="hero__eyebrow">Notes · category</div>
    <h1>{cat['title']}</h1>
    <p class="hero__lede">{cat['blurb']}</p>
  </section>

  <section class="section" id="{cat['slug']}">
{cat['body']}
  </section>

  <hr class="ornament-rule">

  <p style="text-align:center; font-style:italic; color:var(--muted); font-family:var(--display);">
    <a href="notes.html">← Back to all notes</a>
  </p>

</main>
"""
        + footer_html()
    )


def top_index_page(categories: list[dict]) -> str:
    cards = []
    for cat in categories:
        cards.append(f"""    <li class="catalogue__item">
      <span class="catalogue__num">·</span>
      <span class="catalogue__main">
        <a href="notes-{cat['slug']}.html">{cat['title']}</a>
        <span class="catalogue__desc">{cat['blurb']}</span>
      </span>
      <span class="catalogue__tag">{cat['tag']}</span>
    </li>""")
    cards_html = "\n".join(cards)
    return (
        page_chrome_head(
            "Notes",
            "A working notebook of solved problems and self-contained derivations in QFT, GR, QM, electrodynamics, and mathematical methods.",
        )
        + topbar(active="notes")
        + f"""
<main class="page page--index">

  <section class="hero">
    <div class="hero__eyebrow">A working notebook</div>
    <h1>Notes</h1>
    <p class="hero__lede">
      Solved problems and self-contained derivations from coursework and
      independent reading, organised by topic.
    </p>

    <svg class="hero__vertex" viewBox="0 0 60 60" aria-hidden="true">
      <line x1="6" y1="6" x2="30" y2="30"/>
      <line x1="54" y1="6" x2="30" y2="30"/>
      <path d="M30,30 Q35,40 30,46 Q25,52 30,58" stroke-dasharray="3 3"/>
      <circle cx="30" cy="30" r="2.2" fill="currentColor" stroke="none" style="fill: var(--accent);"/>
    </svg>
  </section>

  <section class="section">
    <h2>Topics</h2>
    <ul class="catalogue">
{cards_html}
    </ul>
  </section>

  <hr class="ornament-rule">

  <p style="text-align:center; font-style:italic; color:var(--muted); font-family:var(--display);">
    Sources are credited on every page. All write-ups are mine; corrections welcome.
  </p>

</main>
"""
        + footer_html()
    )


# ---------------------------------------------------------------------------

import re as _re


_ROMAN_LABEL_RE = _re.compile(r"^[IVXLCDM]+\.$")


def _renumber_body(body: str) -> str:
    """Restart Roman-numeral catalogue labels at I within each <ul>.

    The original notes.html was one continuous page, so labels ran
    II–X, XI–XIII, XIV–XXI, … across categories. Now each category has
    its own page, so the labels should restart at I per category. This
    pass walks each <ul>...</ul> in order and replaces every
    `<span class="catalogue__num">XYZ.</span>` whose label parses as
    Roman with a fresh sequential numeral. Non-Roman labels (PS1, PS2,
    α, β, γ, …) are left alone."""

    def renumber_one_ul(m):
        ul = m.group(0)
        n = [0]   # mutable counter
        def num_repl(mm):
            existing = mm.group(1)
            if not _ROMAN_LABEL_RE.match(existing):
                return mm.group(0)
            n[0] += 1
            return f'<span class="catalogue__num">{roman(n[0])}.</span>'
        return _re.sub(
            r'<span class="catalogue__num">([^<]+)</span>',
            num_repl, ul,
        )

    return _re.sub(r"<ul class=\"catalogue\">.*?</ul>",
                   renumber_one_ul, body, flags=_re.DOTALL)


def main():
    # Per-category pages
    for cat in CATEGORIES:
        cat = {**cat, "body": _renumber_body(cat["body"])}
        path = os.path.join(ROOT, f"notes-{cat['slug']}.html")
        with open(path, "w") as f:
            f.write(category_page(cat))
        print(f"  wrote notes-{cat['slug']}.html")

    # Top-level overview
    top = os.path.join(ROOT, "notes.html")
    with open(top, "w") as f:
        f.write(top_index_page(CATEGORIES))
    print(f"  wrote notes.html (overview, {len(CATEGORIES)} categories)")


if __name__ == "__main__":
    main()
