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
import re

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

<link rel="stylesheet" href="{css_path}">

<script src="{theme_path}"></script>
<script src="{font_path}"></script>
<script src="assets/mathjax-config.js"></script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
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
  <a href="{index_path}" class="topbar__brand">Luca Jin <small>Physics · Imperial</small></a>
  <nav class="topbar__nav" aria-label="Primary navigation">
    <a href="{index_path}"{a_about}>Home</a>
    <a href="{notes_path}"{a_notes}>Work</a>
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
    <a href="{index_path}">Home</a> ·
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
        "slug": "qft",
        "title": "Quantum Field Theory",
        "blurb": "Path-integral essay, Peskin / Tong / PSI / Srednicki solutions, Schwartz chapter notes, φ³ computation.",
        "tag": "20 works",
        "body": """    <h3>Papers</h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">I.</span>
        <span class="catalogue__main">
          <a href="notes/path-integral.html">Path Integrals and the Quantum–Statistical Correspondence</a>
          <span class="catalogue__desc">Imperial Year-2 essay — Feynman's path integral, Wick rotation, and the partition function.</span>
        </span>
        <span class="catalogue__tag">Essay</span>
      </li>
    </ul>

    <h3>Solutions</h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">I.</span>
        <span class="catalogue__main">
          <a href="notes/peskin-6-2.html">Equivalent Photon Approximation</a>
          <span class="catalogue__desc">Peskin &amp; Schroeder, Problem 6.2.</span>
        </span>
        <span class="catalogue__tag">Peskin Ch. 6</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">II.</span>
        <span class="catalogue__main">
          <a href="notes/peskin-7.html">Alternative Regulators in QED</a>
          <span class="catalogue__desc">Peskin &amp; Schroeder, Chapter 7 — Pauli–Villars vs. dimensional regularization.</span>
        </span>
        <span class="catalogue__tag">Peskin Ch. 7</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">III.</span>
        <span class="catalogue__main">
          <a href="notes/peskin-final.html">Final Project — Radiation of Gluon Jets</a>
          <span class="catalogue__desc">Peskin &amp; Schroeder, end-of-book project.</span>
        </span>
        <span class="catalogue__tag">Peskin Final</span>
      </li>
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
      <li class="catalogue__item">
        <span class="catalogue__num">PS4.</span>
        <span class="catalogue__main">
          <a href="notes/tong-qft-ps4.html">Interactions &amp; Tree-Level Amplitudes</a>
          <span class="catalogue__desc">Wick's theorem at tree level — φ⁴ 3-to-3, vacuum bubbles, Yukawa, Compton, e⁻e⁺ → μ⁻μ⁺.</span>
        </span>
        <span class="catalogue__tag">Tong PS4</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">Ψ1.</span>
        <span class="catalogue__main">
          <a href="notes/psi-correlation-functions-qm.html">Correlation Functions in Quantum Mechanics</a>
          <span class="catalogue__desc">PSI QFT II PS1 — Euclidean / real-time path-integral propagators of the harmonic oscillator at finite temperature.</span>
        </span>
        <span class="catalogue__tag">PSI QFT II</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">O2.</span>
        <span class="catalogue__main">
          <a href="notes/osborn-aqft-ps2.html">Functional Methods &amp; Grassmann Integrals</a>
          <span class="catalogue__desc">Osborn AQFT PS2 — Legendre transform, 1PI effective action, Green's-function/vertex relations, Grassmann Gaussian integrals, Pfaffians, fermionic partition function, SUSY QM. (Q1–Q8)</span>
        </span>
        <span class="catalogue__tag">Osborn AQFT PS2</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">O3.</span>
        <span class="catalogue__main">
          <a href="notes/osborn-aqft-ps3.html">Feynman Graphs &amp; RG Calculations</a>
          <span class="catalogue__desc">Osborn AQFT PS3 — superficial divergence, Feynman parameters, position-space loop integrals, φ⁴ counter-terms, two-loop β functions, RG equations, φ³ in d=6. (Q1–Q10)</span>
        </span>
        <span class="catalogue__tag">Osborn AQFT PS3</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">S1.</span>
        <span class="catalogue__main">
          <a href="notes/srednicki-nonabelian.html">Nonabelian Symmetries</a>
          <span class="catalogue__desc">Srednicki Ch. 24 — antisymmetry of the generator, structure constants from SO(N), Noether current and charge algebra, generators of Sp(2N). (Q24.1–24.4)</span>
        </span>
        <span class="catalogue__tag">Srednicki Ch. 24</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">S2.</span>
        <span class="catalogue__main">
          <a href="notes/srednicki-rg-phi-chi.html">Renormalization Group for φ-χ Theory</a>
          <span class="catalogue__desc">Srednicki Ch. 28 — one-loop Z-factors in MS-bar, β-functions for the φ³ + φχ² couplings, and asymptotic freedom condition on h/g. (Q28.3)</span>
        </span>
        <span class="catalogue__tag">Srednicki Ch. 28</span>
      </li>
    </ul>

    <h3>Notes</h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">I.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-classical-field.html">Classical Field Theory</a>
          <span class="catalogue__desc">Schwartz, Ch. 1–3 — Euler–Lagrange, Noether, Green's functions.</span>
        </span>
        <span class="catalogue__tag">Schwartz Ch. 1–3</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">II.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-second-quantization.html">Second Quantization &amp; LSZ Reduction</a>
          <span class="catalogue__desc">Schwartz, Ch. 2–6 — from the harmonic oscillator to the S-matrix and the Feynman propagator.</span>
        </span>
        <span class="catalogue__tag">Schwartz Ch. 2–6</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">III.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-spin-1.html">Spin 1, Gauge Invariance, Photon Propagator</a>
          <span class="catalogue__desc">Schwartz, Ch. 8–9 — quantising massless spin-1, Ward identity, scalar QED.</span>
        </span>
        <span class="catalogue__tag">Schwartz Ch. 8–9</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">IV.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-spinors.html">Spinors, Dirac Equation, CPT</a>
          <span class="catalogue__desc">Schwartz, Ch. 10–11 — Lorentz reps, Weyl/Majorana, charge conjugation, parity, time reversal.</span>
        </span>
        <span class="catalogue__tag">Schwartz Ch. 10–11</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">V.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-qed-tree.html">QED Tree Amplitudes</a>
          <span class="catalogue__desc">Schwartz, Ch. 13 — e+e− → μ+μ− and Rutherford scattering from the Feynman rules.</span>
        </span>
        <span class="catalogue__tag">Schwartz Ch. 13</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">VI.</span>
        <span class="catalogue__main">
          <a href="notes/schwartz-path-integrals.html">Path Integrals (in QFT)</a>
          <span class="catalogue__desc">Schwartz, Ch. 14 — from QM to functional integrals over fields.</span>
        </span>
        <span class="catalogue__tag">Schwartz Ch. 14</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">VII.</span>
        <span class="catalogue__main">
          <a href="notes/phi3-theory.html">Computation for φ³ Theory</a>
          <span class="catalogue__desc">Counter-terms, partition functional, and one-loop diagrams in φ³ scalar theory; follows Srednicki and Peskin &amp; Schroeder.</span>
        </span>
        <span class="catalogue__tag">φ³</span>
      </li>
    </ul>""",
    },
    {
        "slug": "advanced",
        "title": "GR",
        "blurb": "Manifolds and tensors, connections and curvature, geodesics and Killing vectors, Brans–Dicke scalar-tensor gravity, 11-dimensional supergravity, and linearised gravity / gravitational waves.",
        "tag": "4 notes",
        "body": """    <h3>Solutions</h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">PS1.</span>
        <span class="catalogue__main">
          <a href="notes/tong-gr-ps1.html">Differential Geometry</a>
          <span class="catalogue__desc">Manifolds, tensors, Lie and exterior derivatives, Maurer–Cartan, Poincaré lemma.</span>
        </span>
        <span class="catalogue__tag">Tong GR PS1</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">PS2.</span>
        <span class="catalogue__main">
          <a href="notes/tong-gr-ps2.html">Connections &amp; Curvature</a>
          <span class="catalogue__desc">Christoffel transformation, torsion, Bianchi, parallel transport, Riemann / Ricci / Weyl, geodesics, Reissner–Nordström.</span>
        </span>
        <span class="catalogue__tag">Tong GR PS2</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">PS3.</span>
        <span class="catalogue__main">
          <a href="notes/tong-gr-ps3.html">Geodesics, Killing Vectors &amp; Energy Conditions</a>
          <span class="catalogue__desc">Timelike geodesics, Brans–Dicke scalar-tensor gravity, 11-d supergravity, Killing vectors, conformal compactification, energy conditions.</span>
        </span>
        <span class="catalogue__tag">Tong GR PS3</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">PS4.</span>
        <span class="catalogue__main">
          <a href="notes/tong-gr-ps4.html">Linearised Gravity &amp; Gravitational Waves</a>
          <span class="catalogue__desc">Linearised gravity from a point mass, cosmic strings, Lense–Thirring, Fierz–Pauli, transverse-traceless gauge, binary gravitational-wave emission.</span>
        </span>
        <span class="catalogue__tag">Tong GR PS4</span>
      </li>
    </ul>""",
    },
    {
        "slug": "qm",
        "title": "Quantum Mechanics",
        "blurb": "Bound-state existence, parity arguments, factorisation method.",
        "tag": "3 notes",
        "body": """    <h3>Solutions</h3>
    <ul class="catalogue">
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
        "body": """    <h3>Solutions</h3>
    <ul class="catalogue">
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
        "body": """    <h3>Solutions</h3>
    <ul class="catalogue">
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
        "body": """    <h3>Solutions</h3>
    <ul class="catalogue">
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
        "body": """    <h3>Solutions</h3>
    <ul class="catalogue">
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

def typeset_catalogue_math(text: str) -> str:
    """Use TeX notation for mathematical symbols shown in archive chrome."""
    replacements = (
        ('e<sup>-|x|</sup>', r'\(e^{-\lvert x\rvert}\)'),
        ('t<sup>-1/2</sup>', r'\(t^{-1/2}\)'),
        ('e⁻e⁺ → μ⁻μ⁺', r'\(e^-e^+\to\mu^-\mu^+\)'),
        ('e+e− → μ+μ−', r'\(e^+e^-\to\mu^+\mu^-\)'),
        ('φχ²', r'\(\phi\chi^2\)'),
        ('φ-χ', r'\(\phi\text{-}\chi\)'),
        ('φ⁴', r'\(\phi^4\)'),
        ('φ³', r'\(\phi^3\)'),
        ('χ²', r'\(\chi^2\)'),
        ('γ-matrices', r'\(\gamma\)-matrices'),
        ('β-functions', r'\(\beta\)-functions'),
        ('SO(3)', r'\(\mathrm{SO}(3)\)'),
        ('SO(N)', r'\(\mathrm{SO}(N)\)'),
        ('Sp(2N)', r'\(\mathrm{Sp}(2N)\)'),
        ('d=6', r'\(d=6\)'),
        ('h/g', r'\(h/g\)'),
        ('Spin-½', r'Spin-\(\tfrac{1}{2}\)'),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    return text


def catalogue_with_formats(body: str) -> str:
    """Add honest, route-specific HTML and PDF actions to each work row."""
    body = typeset_catalogue_math(body)
    item_re = re.compile(r'<li class="catalogue__item">.*?</li>', re.DOTALL)

    def decorate(match: re.Match[str]) -> str:
        item = match.group(0)
        href_match = re.search(r'<a href="(notes/([^"]+)\.html)">', item)
        if not href_match:
            return item
        html_href, slug = href_match.groups()
        formats = (
            '<span class="catalogue__formats" aria-label="Available formats">'
            f'<a href="{html_href}">HTML <span aria-hidden="true">↗</span></a>'
            f'<a href="output/pdf/{slug}.pdf">PDF <span aria-hidden="true">↓</span></a>'
            '</span>\n      '
        )
        return item.replace('<span class="catalogue__tag">', formats + '<span class="catalogue__tag">', 1)

    return item_re.sub(decorate, body)

def category_page(cat: dict) -> str:
    """One per-category index — heading, breadcrumb back to top-level
    notes.html, and the catalogue body."""
    description = f"Written-work archive: {cat['title']} — {cat['blurb']}"
    return (
        page_chrome_head(f"{cat['title']} — Notes", description)
        + topbar(active="notes")
        + f"""
<main class="page page--index">

  <div class="note__breadcrumb">
    <a href="notes.html">Work</a> &nbsp;·&nbsp; {cat['title']}
  </div>

  <section class="hero">
    <div class="hero__eyebrow">Written work · subject</div>
    <h1>{cat['title']}</h1>
    <p class="hero__lede">{typeset_catalogue_math(cat['blurb'])}</p>
  </section>

  <section class="section" id="{cat['slug']}">
{catalogue_with_formats(cat['body'])}
  </section>

  <hr class="ornament-rule">

  <p style="text-align:center; font-style:italic; color:var(--muted); font-family:var(--display);">
    <a href="notes.html">← Back to all work</a>
  </p>

</main>
"""
        + footer_html()
    )


_HTML_TAG_RE = _re.compile(r"<[^>]+>") if False else None  # placeholder so import order ok

import re as __re_for_stats
import html as __html_for_stats

_STATS_TAG_RE = __re_for_stats.compile(r"<[^>]+>")
_STATS_SCRIPT_RE = __re_for_stats.compile(r"<(script|style|svg)\b[^>]*>.*?</\1>",
                                          __re_for_stats.DOTALL | __re_for_stats.IGNORECASE)
_STATS_MATH_DISP_RE = __re_for_stats.compile(r"\\\[.*?\\\]", __re_for_stats.DOTALL)
_STATS_MATH_INL_RE = __re_for_stats.compile(r"\\\(.*?\\\)", __re_for_stats.DOTALL)


def _extract_prose(html: str) -> str:
    """Strip HTML/SVG/scripts and TeX math from a notes page; return the
    plain prose that a reader would actually see (modulo MathJax rendering).
    Used by compute_stats() to give a meaningful word/char count."""
    t = _STATS_SCRIPT_RE.sub(" ", html)
    t = _STATS_MATH_DISP_RE.sub(" ", t)
    t = _STATS_MATH_INL_RE.sub(" ", t)
    t = _STATS_TAG_RE.sub(" ", t)
    t = __html_for_stats.unescape(t)
    t = __re_for_stats.sub(r"\s+", " ", t).strip()
    return t


def compute_stats() -> dict:
    """Walk notes/*.html, return {pages, words, chars}."""
    notes_dir = os.path.join(ROOT, "notes")
    pages = 0
    words = 0
    chars = 0
    for name in sorted(os.listdir(notes_dir)):
        if not name.endswith(".html"):
            continue
        path = os.path.join(notes_dir, name)
        with open(path, encoding="utf-8") as f:
            prose = _extract_prose(f.read())
        pages += 1
        # Count words; len(prose) gives char count (sans collapsed runs of WS).
        words += len(prose.split())
        chars += len(prose)
    return {"pages": pages, "words": words, "chars": chars}


def _fmt(n: int) -> str:
    return f"{n:,}"


def top_index_page(categories: list[dict]) -> str:
    cards = []
    for cat in categories:
        count = cat['body'].count('<li class="catalogue__item">')
        cards.append(f'<a class="subject-link" href="#{cat["slug"]}"><span>{cat["title"]}</span><small>{count} works</small></a>')
    cards_html = "\n".join(cards)
    stats = compute_stats()
    stats_html = f"""
    <ul class="stats" aria-label="Notebook statistics">
      <li><span class="stats__num">{_fmt(stats['pages'])}</span><span class="stats__label">written works</span></li>
      <li><span class="stats__num">{len(categories)}</span><span class="stats__label">subjects</span></li>
      <li><span class="stats__num">2</span><span class="stats__label">formats per work</span></li>
    </ul>"""
    work_sections = []
    for cat in categories:
        count = cat['body'].count('<li class="catalogue__item">')
        work_sections.append(f"""
  <section class="section work-subject" id="{cat['slug']}">
    <div class="work-subject__heading">
      <div><p class="hero__eyebrow">{count} works</p><h2>{cat['title']}</h2></div>
      <a href="notes-{cat['slug']}.html">Subject page →</a>
    </div>
{catalogue_with_formats(cat['body'])}
  </section>""")
    work_sections_html = "\n".join(work_sections)
    return (
        page_chrome_head(
            "Work",
            "A clear archive of solved problems and self-contained derivations in QFT, GR, QM, electrodynamics, and mathematical methods, available in HTML and PDF.",
        )
        + topbar(active="notes")
        + f"""
<main class="page page--index">

  <section class="hero">
    <div class="hero__eyebrow">A working archive</div>
    <h1>Written work</h1>
    <p class="hero__lede">
      48 solved problems and derivations. Read online or download a typeset PDF.
    </p>
    <p class="hero__lede" style="font-style:italic; color:var(--muted);">
      Study write-ups, not original research; every source is credited.
    </p>
{stats_html}

  </section>

  <nav class="subject-index" aria-label="Browse by subject">
{cards_html}
  </nav>

{work_sections_html}

  <p class="archive-disclaimer">Sources are credited on every page. These are my write-ups of coursework, textbook problems, and independent study; corrections are welcome.</p>

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


# Parser used to derive the runtime nav manifest (assets/nav-manifest.json)
# consumed by theme.js to build the site-wide navigator, breadcrumb links,
# and prev/next pager. The category bodies above are the single source of
# truth, so we read them rather than maintaining a parallel list.
_GROUP_RE = _re.compile(
    r'(?:<h3>([^<]+)</h3>\s*)?<ul class="catalogue">(.*?)</ul>',
    _re.DOTALL,
)
_ITEM_RE = _re.compile(
    r'<li class="catalogue__item">\s*'
    r'<span class="catalogue__num">([^<]+)</span>\s*'
    r'<span class="catalogue__main">\s*'
    r'<a href="([^"]+)">(.*?)</a>\s*'
    r'<span class="catalogue__desc">(.*?)</span>\s*'
    r'</span>\s*'
    r'<span class="catalogue__tag">(.*?)</span>\s*'
    r'</li>',
    _re.DOTALL,
)


def _extract_groups(body: str):
    groups = []
    for gm in _GROUP_RE.finditer(body):
        group_title = (gm.group(1) or "").strip()
        notes = []
        for im in _ITEM_RE.finditer(gm.group(2)):
            label, href, title, desc, tag = im.groups()
            notes.append({
                "href":  href.strip(),
                "title": title.strip(),
                "label": label.strip(),
                "desc":  desc.strip(),
                "tag":   tag.strip(),
            })
        if notes:
            groups.append({"title": group_title, "notes": notes})
    return groups


def write_manifest(categories: list[dict]) -> None:
    import json
    data = {
        "categories": [
            {
                "slug":   cat["slug"],
                "title":  cat["title"],
                "blurb":  cat["blurb"],
                "tag":    cat["tag"],
                "groups": _extract_groups(cat["body"]),
            }
            for cat in categories
        ],
    }
    out = os.path.join(ROOT, "assets", "nav-manifest.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  wrote assets/nav-manifest.json ({len(data['categories'])} categories)")


def main():
    # Per-category pages
    rendered = []
    for cat in CATEGORIES:
        cat = {**cat, "body": _renumber_body(cat["body"])}
        rendered.append(cat)
        path = os.path.join(ROOT, f"notes-{cat['slug']}.html")
        with open(path, "w") as f:
            f.write(category_page(cat))
        print(f"  wrote notes-{cat['slug']}.html")

    # Top-level overview
    top = os.path.join(ROOT, "notes.html")
    with open(top, "w") as f:
        f.write(top_index_page(rendered))
    print(f"  wrote notes.html (overview, {len(rendered)} categories)")

    # Runtime nav manifest used by theme.js
    write_manifest(rendered)


if __name__ == "__main__":
    main()
