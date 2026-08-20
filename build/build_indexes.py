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
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = "https://luca-yucheng-jin.github.io/luca-physics-site"
AUTHOR_NAME = "Yucheng (Luca) Jin"
WEBSITE_ID = f"{SITE_URL}/#website"
PERSON_ID = f"{SITE_URL}/#person"


# ---------------------------------------------------------------------------
# Shared chrome (header + footer). Rendered once per page.

def page_chrome_head(title: str, description: str, canonical_path: str,
                     schema: dict, css_path: str = "styles.css",
                     theme_path: str = "assets/theme.js",
                     font_path: str = "assets/font-size.js",
                     icon_path: str = "assets/favicon.svg") -> str:
    full_title = f"{title} | {AUTHOR_NAME}"
    canonical = f"{SITE_URL}/{canonical_path.lstrip('/')}"
    escaped_title = html.escape(full_title, quote=True)
    escaped_description = html.escape(description, quote=True)
    escaped_canonical = html.escape(canonical, quote=True)
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escaped_title}</title>
<meta name="description" content="{escaped_description}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="author" content="{AUTHOR_NAME}">
<link rel="canonical" href="{escaped_canonical}">
<meta property="og:type" content="website">
<meta property="og:url" content="{escaped_canonical}">
<meta property="og:site_name" content="Luca Jin Physics">
<meta property="og:title" content="{escaped_title}">
<meta property="og:description" content="{escaped_description}">
<meta property="og:image" content="{SITE_URL}/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escaped_title}">
<meta name="twitter:description" content="{escaped_description}">
<meta name="twitter:image" content="{SITE_URL}/og.png">

<link rel="icon" type="image/svg+xml" href="{icon_path}">

<link rel="stylesheet" href="{css_path}">

<script type="application/ld+json">{schema_json}</script>

<script src="{theme_path}"></script>
<script src="{font_path}"></script>
<script src="assets/mathjax-config.js"></script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>"""


def collection_schema(name: str, description: str, canonical_path: str,
                      subject: str | None = None) -> dict:
    canonical = f"{SITE_URL}/{canonical_path.lstrip('/')}"
    page = {
        "@type": "CollectionPage",
        "@id": f"{canonical}#page",
        "url": canonical,
        "name": name,
        "description": description,
        "inLanguage": "en",
        "isPartOf": {
            "@type": "WebSite",
            "@id": WEBSITE_ID,
            "name": "Luca Jin Physics",
            "url": f"{SITE_URL}/",
        },
        "author": {
            "@type": "Person",
            "@id": PERSON_ID,
            "name": AUTHOR_NAME,
            "url": f"{SITE_URL}/",
        },
    }
    graph: list[dict] = [page]
    if subject:
        page["about"] = {"@type": "Thing", "name": subject}
        graph.append({
            "@type": "BreadcrumbList",
            "@id": f"{canonical}#breadcrumb",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Notes",
                    "item": f"{SITE_URL}/notes.html",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": subject,
                    "item": canonical,
                },
            ],
        })
    return {"@context": "https://schema.org", "@graph": graph}


def topbar(active: str, index_path: str = "./",
           notes_path: str = "notes.html") -> str:
    """`active` ∈ {'about', 'notes'} marks the current nav item."""
    a_about = ' class="is-active"' if active == "about" else ""
    a_notes = ' class="is-active"' if active == "notes" else ""
    return f"""
<header class="topbar">
  <a href="{index_path}" class="topbar__brand">Luca Jin <small>Physics · Imperial</small></a>
  <nav class="topbar__nav" aria-label="Primary navigation">
    <a href="{index_path}"{a_about}>Home</a>
    <a href="{notes_path}"{a_notes}>Notes</a>
    <a href="mailto:luca.jin@outlook.com">Contact</a>
    <button class="font-toggle" type="button" data-font-size="dec" aria-label="Decrease font size" title="Decrease font size">A<span class="font-toggle__small">−</span></button>
    <button class="font-toggle" type="button" data-font-size="inc" aria-label="Increase font size" title="Increase font size">A<span class="font-toggle__large">+</span></button>
    <button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch to dark theme" title="Toggle theme">
      <svg class="icon-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/></svg>
      <svg class="icon-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
    </button>
  </nav>
</header>"""


def footer_html(index_path: str = "./",
                notes_path: str = "notes.html") -> str:
    return f"""
<footer class="footer">
  <span>© 2026 Yucheng (Luca) Jin</span>
  <span>
    <a href="{index_path}">Home</a> ·
    <a href="{notes_path}">Notes</a> ·
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
        "blurb": "Peskin, Tong, PSI, Osborn, and Srednicki solutions, plus an independent φ³ computation.",
        "tag": "13 notes",
        "body": """    <h3 class="catalogue-source">
      <span>Solutions to Peskin &amp; Schroeder’s <em>An Introduction to Quantum Field Theory</em></span>
      <a href="https://www.routledge.com/An-Introduction-To-Quantum-Field-Theory/Peskin-Schroeder/p/book/9780429503559" target="_blank" rel="noopener noreferrer">Publisher page ↗</a>
    </h3>
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
    </ul>

    <h3 class="catalogue-source">
      <span>Solutions to David Tong’s Quantum Field Theory problem sheets</span>
      <a href="https://www.damtp.cam.ac.uk/user/tong/qft.htm" target="_blank" rel="noopener noreferrer">Original course ↗</a>
    </h3>
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
      <li class="catalogue__item">
        <span class="catalogue__num">PS4.</span>
        <span class="catalogue__main">
          <a href="notes/tong-qft-ps4.html">Interactions &amp; Tree-Level Amplitudes</a>
          <span class="catalogue__desc">Wick's theorem at tree level — φ⁴ 3-to-3, vacuum bubbles, Yukawa, Compton, e⁻e⁺ → μ⁻μ⁺.</span>
        </span>
        <span class="catalogue__tag">Tong PS4</span>
      </li>
    </ul>

    <h3>Perimeter Scholars International · Quantum Field Theory II</h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">Ψ1.</span>
        <span class="catalogue__main">
          <a href="notes/psi-correlation-functions-qm.html">Correlation Functions in Quantum Mechanics</a>
          <span class="catalogue__desc">PSI QFT II PS1 — Euclidean / real-time path-integral propagators of the harmonic oscillator at finite temperature.</span>
        </span>
        <span class="catalogue__tag">PSI QFT II</span>
      </li>
    </ul>

    <h3 class="catalogue-source">
      <span>Solutions to Hugh Osborn’s Advanced Quantum Field Theory example sheets</span>
      <a href="https://www.damtp.cam.ac.uk/user/ho/" target="_blank" rel="noopener noreferrer">Course materials ↗</a>
    </h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">O2.</span>
        <span class="catalogue__main">
          <a href="notes/osborn-aqft-ps2.html">Functional Methods &amp; Grassmann Integrals</a>
          <span class="catalogue__desc">Osborn AQFT Example Sheet 2 — Legendre transform, 1PI effective action, Green's-function/vertex relations, Grassmann Gaussian integrals, Pfaffians, fermionic partition function, SUSY QM. (Q1–Q8)</span>
        </span>
        <span class="catalogue__tag">Osborn AQFT · ES2</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">O3.</span>
        <span class="catalogue__main">
          <a href="notes/osborn-aqft-ps3.html">Feynman Graphs &amp; RG Calculations</a>
          <span class="catalogue__desc">Osborn AQFT Example Sheet 3 — superficial divergence, Feynman parameters, position-space loop integrals, φ⁴ counter-terms, two-loop β functions, RG equations, φ³ in d=6. (Q1–Q10)</span>
        </span>
        <span class="catalogue__tag">Osborn AQFT · ES3</span>
      </li>
    </ul>

    <h3 class="catalogue-source">
      <span>Solutions to Mark Srednicki’s Quantum Field Theory</span>
      <a href="https://www.physics.ucsb.edu/~mark/qft.html" target="_blank" rel="noopener noreferrer">Author’s page ↗</a>
    </h3>
    <ul class="catalogue">
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

    <h3>Independent computation</h3>
    <ul class="catalogue">
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
        "title": "General Relativity",
        "blurb": "Manifolds and tensors, connections and curvature, geodesics and Killing vectors, Brans–Dicke scalar-tensor gravity, 11-dimensional supergravity, and linearised gravity / gravitational waves.",
        "tag": "4 notes",
        "body": """    <h3 class="catalogue-source">
      <span>Solutions to David Tong’s General Relativity problem sheets</span>
      <a href="https://www.damtp.cam.ac.uk/user/tong/gr.html" target="_blank" rel="noopener noreferrer">Original course ↗</a>
    </h3>
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
        "body": """    <h3 class="catalogue-source">
      <span>Solutions to Cambridge Quantum Mechanics examples accompanying David Tong’s notes</span>
      <a href="https://www.damtp.cam.ac.uk/user/tong/books/quantum.html" target="_blank" rel="noopener noreferrer">Original exercises ↗</a>
    </h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XI.</span>
        <span class="catalogue__main">
          <a href="notes/qm-bound-states.html">Non-Degeneracy &amp; Reality of Bound States in 1D</a>
          <span class="catalogue__desc">Cambridge Quantum Mechanics, Example Sheet 1, Q4; accompanies David Tong’s notes.</span>
        </span>
        <span class="catalogue__tag">Cambridge QM · ES1</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XII.</span>
        <span class="catalogue__main">
          <a href="notes/qm-shallow-well.html">Absence of Odd-Parity Bound States in a Shallow Square Well</a>
          <span class="catalogue__desc">Cambridge Quantum Mechanics, Example Sheet 1, Q7; accompanies David Tong’s notes.</span>
        </span>
        <span class="catalogue__tag">Cambridge QM · ES1</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XIII.</span>
        <span class="catalogue__main">
          <a href="notes/qm-sech-squared.html">Factorisation Method for the Sech-Squared Potential</a>
          <span class="catalogue__desc">Cambridge Quantum Mechanics, Example Sheet 1, Q8; accompanies David Tong’s notes.</span>
        </span>
        <span class="catalogue__tag">Cambridge QM · ES1</span>
      </li>
    </ul>""",
    },
    {
        "slug": "ed",
        "title": "Electrodynamics",
        "blurb": "Cambridge electromagnetism exercises accompanying David Tong’s notes — radiation, relativity, and dielectric boundaries.",
        "tag": "8 notes",
        "body": """    <h3 class="catalogue-source">
      <span>Solutions to the radiation exercises accompanying David Tong’s <em>Electromagnetism</em></span>
      <a href="https://www.damtp.cam.ac.uk/user/tong/books/electro.html" target="_blank" rel="noopener noreferrer">Original exercises ↗</a>
    </h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XIV.</span>
        <span class="catalogue__main">
          <a href="notes/ed-retarded.html">Retarded Potentials and Far-Field Radiation</a>
          <span class="catalogue__desc"><em>Electromagnetism</em>, Chapter 7 exercises, Q4.</span>
        </span>
        <span class="catalogue__tag">Cambridge EM · Ch. 7</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XV.</span>
        <span class="catalogue__main">
          <a href="notes/ed-lienard-wiechert.html">Liénard–Wiechert Potential and the Field Tensor</a>
          <span class="catalogue__desc"><em>Electromagnetism</em>, Chapter 7 exercises, Q6.</span>
        </span>
        <span class="catalogue__tag">Cambridge EM · Ch. 7</span>
      </li>
    </ul>

    <h3 class="catalogue-source">
      <span>Solutions to Electromagnetism Problem Sheet 3 — Waves and Relativity</span>
      <a href="https://www.damtp.cam.ac.uk/user/tong/em.html" target="_blank" rel="noopener noreferrer">Original course ↗</a>
    </h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XVI.</span>
        <span class="catalogue__main">
          <a href="notes/ed-relativistic-uniform.html">Relativistic Motion in a Uniform Electric Field</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS3 Q9.</span>
        </span>
        <span class="catalogue__tag">Tong EM · PS3</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XVII.</span>
        <span class="catalogue__main">
          <a href="notes/ed-gauge-plane-wave.html">Gauge Transformation of a Plane EM Wave</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS3 Q5.</span>
        </span>
        <span class="catalogue__tag">Tong EM · PS3</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XVIII.</span>
        <span class="catalogue__main">
          <a href="notes/ed-moving-mirror.html">Reflection of an EM Wave from a Moving Mirror</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS3 Q7.</span>
        </span>
        <span class="catalogue__tag">Tong EM · PS3</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XIX.</span>
        <span class="catalogue__main">
          <a href="notes/ed-covariant-ohms.html">Covariant Form of Ohm's Law</a>
          <span class="catalogue__desc">D. Tong, <em>Electromagnetism</em>, PS3 Q10.</span>
        </span>
        <span class="catalogue__tag">Tong EM · PS3</span>
      </li>
    </ul>

    <h3 class="catalogue-source">
      <span>Solutions to the electromagnetism-in-matter exercises accompanying David Tong’s <em>Electromagnetism</em></span>
      <a href="https://www.damtp.cam.ac.uk/user/tong/books/electro.html" target="_blank" rel="noopener noreferrer">Original exercises ↗</a>
    </h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XX.</span>
        <span class="catalogue__main">
          <a href="notes/ed-dielectric-sphere.html">Dielectric Sphere in a Uniform Electric Field</a>
          <span class="catalogue__desc"><em>Electromagnetism</em>, Chapter 8 exercises, Q1.</span>
        </span>
        <span class="catalogue__tag">Cambridge EM · Ch. 8</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXI.</span>
        <span class="catalogue__main">
          <a href="notes/ed-frustrated-tir.html">Frustrated Total Internal Reflection &amp; Evanescent Waves</a>
          <span class="catalogue__desc"><em>Electromagnetism</em>, Chapter 8 exercises, Q3.</span>
        </span>
        <span class="catalogue__tag">Cambridge EM · Ch. 8</span>
      </li>
    </ul>""",
    },
    {
        "slug": "mm",
        "title": "Mathematical Methods",
        "blurb": "Santos complex-methods example sheets, a reference note, and Cambridge variational principles.",
        "tag": "6 notes",
        "body": """    <h3>Standalone reference note</h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XXII.</span>
        <span class="catalogue__main">
          <a href="notes/mm-jordans-lemma.html">Jordan's Lemma</a>
          <span class="catalogue__desc">Standard statement, proof, and applications.</span>
        </span>
        <span class="catalogue__tag">Complex Analysis</span>
      </li>
    </ul>

    <h3 class="catalogue-source">
      <span>Solutions to J. E. Santos’s Cambridge Part IB Complex Methods example sheets</span>
      <a href="https://www.damtp.cam.ac.uk/user/examples/" target="_blank" rel="noopener noreferrer">Cambridge examples ↗</a>
    </h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XXIII.</span>
        <span class="catalogue__main">
          <a href="notes/mm-convolution-fourier.html">Convolution and Fourier Representation of e<sup>-|x|</sup></a>
          <span class="catalogue__desc">J. E. Santos, Cambridge Part IB Complex Methods, Example Sheet 3, Q2.</span>
        </span>
        <span class="catalogue__tag">Santos CM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXIV.</span>
        <span class="catalogue__main">
          <a href="notes/mm-residues.html">Residues at Simple and Higher-Order Poles</a>
          <span class="catalogue__desc">J. E. Santos, Cambridge Part IB Complex Methods, Example Sheet 2, Q7.</span>
        </span>
        <span class="catalogue__tag">Santos CM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXV.</span>
        <span class="catalogue__main">
          <a href="notes/mm-contour-integration.html">Contour Integration via Residues and Cauchy</a>
          <span class="catalogue__desc">J. E. Santos, Cambridge Part IB Complex Methods, Example Sheet 2, Q9.</span>
        </span>
        <span class="catalogue__tag">Santos CM</span>
      </li>
      <li class="catalogue__item">
        <span class="catalogue__num">XXVI.</span>
        <span class="catalogue__main">
          <a href="notes/mm-laplace-bromwich.html">Laplace Transform of t<sup>-1/2</sup> and the Bromwich Contour</a>
          <span class="catalogue__desc">J. E. Santos, Cambridge Part IB Complex Methods, Example Sheet 3, Q12.</span>
        </span>
        <span class="catalogue__tag">Santos CM</span>
      </li>
    </ul>

    <h3 class="catalogue-source">
      <span>Cambridge Mathematical Tripos · Variational Principles</span>
      <a href="https://www.damtp.cam.ac.uk/user/md327/B6b.pdf" target="_blank" rel="noopener noreferrer">Original sheet ↗</a>
    </h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XXVII.</span>
        <span class="catalogue__main">
          <a href="notes/mm-variational-euler.html">Variational Derivation of Euler's Equation for Inviscid Flow</a>
          <span class="catalogue__desc">Variational Principles, Example Sheet 2 (2023), Q9.</span>
        </span>
        <span class="catalogue__tag">VarPrin</span>
      </li>
    </ul>""",
    },
    {
        "slug": "de",
        "title": "Differential Equations",
        "blurb": "Green's identity and the method of images for the half-space.",
        "tag": "1 note",
        "body": """    <h3 class="catalogue-source">
      <span>Unofficial solution to a public Cambridge Mathematical Tripos past paper</span>
      <a href="https://www.maths.cam.ac.uk/undergrad/pastpapers/files/2025/list_ib.pdf" target="_blank" rel="noopener noreferrer">Original paper ↗</a>
    </h3>
    <ul class="catalogue">
      <li class="catalogue__item">
        <span class="catalogue__num">XXX.</span>
        <span class="catalogue__main">
          <a href="notes/de-greens-identity-halfspace.html">Green's Identity &amp; Method of Images for the Half-Space</a>
          <span class="catalogue__desc">Cambridge Mathematical Tripos Part IB 2025, Paper 3, 14D (Methods). Original question linked, not reproduced.</span>
        </span>
        <span class="catalogue__tag">Cambridge IB</span>
      </li>
    </ul>""",
    },
    {
        "slug": "tdsp",
        "title": "Thermodynamics & Statistical Physics",
        "blurb": "Joule–Thomson and spin-system partition functions.",
        "tag": "3 notes",
        "body": """    <h3 class="catalogue-source">
      <span>Solutions to David Tong’s Statistical Physics problem sheets</span>
      <a href="https://www.damtp.cam.ac.uk/user/tong/statphys.html" target="_blank" rel="noopener noreferrer">Original course ↗</a>
    </h3>
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
    canonical_path = f"notes-{cat['slug']}.html"
    page_title = f"{cat['title']} Notes & Solutions"
    description = (
        f"{cat['title']} notes and worked solutions by {AUTHOR_NAME}: "
        f"{cat['blurb']} Every note is available in HTML and PDF."
    )
    return (
        page_chrome_head(
            page_title,
            description,
            canonical_path,
            collection_schema(page_title, description, canonical_path, cat["title"]),
        )
        + topbar(active="notes")
        + f"""
<main class="page page--index">

  <div class="note__breadcrumb">
    <a href="notes.html">Notes</a> &nbsp;·&nbsp; {cat['title']}
  </div>

  <section class="hero">
    <div class="hero__eyebrow">Notes · subject</div>
    <h1>{cat['title']}</h1>
    <p class="hero__lede">{typeset_catalogue_math(cat['blurb'])}</p>
  </section>

  <section class="section" id="{cat['slug']}">
{catalogue_with_formats(cat['body'])}
  </section>

  <hr class="ornament-rule">

  <p style="text-align:center; font-style:italic; color:var(--muted); font-family:var(--display);">
    <a href="notes.html">← Back to all notes</a>
  </p>

</main>
"""
        + footer_html()
    )


_HTML_TAG_RE = _re.compile(r"<[^>]+>") if False else None  # placeholder so import order ok

import re as __re_for_stats
import html as __html_for_stats

_STATS_TAG_RE = __re_for_stats.compile(r"<[^>]+>")
_STATS_NOTE_HREF_RE = __re_for_stats.compile(r'href="notes/([^"/]+)\.html"')
_STATS_ARTICLE_RE = __re_for_stats.compile(
    r'<article class="note__body">(.*?)</article>', __re_for_stats.DOTALL
)
_STATS_DISPLAY_RE = __re_for_stats.compile(r"\\\[.*?\\\]", __re_for_stats.DOTALL)
_STATS_DOLLAR_DISPLAY_RE = __re_for_stats.compile(r"\$\$.*?\$\$", __re_for_stats.DOTALL)
_STATS_EQUATION_ROW_RE = __re_for_stats.compile(r'<div class="equation-row">')
_STATS_WICK_FIGURE_RE = __re_for_stats.compile(r'<figure class="wick-figure">')
_STATS_PDF_PAGE_RE = __re_for_stats.compile(rb"/Type\s*/Page\b")


def compute_stats(categories: list[dict]) -> dict:
    """Derive public archive totals from the catalogue and its editions.

    The values are deliberately calculated from generated note HTML and PDF
    files rather than maintained as copy.  Running the index build after a
    note is added therefore updates the archive counters automatically.
    """
    slugs = []
    for category in categories:
        slugs.extend(_STATS_NOTE_HREF_RE.findall(category["body"]))
    if len(slugs) != len(set(slugs)):
        raise ValueError("Duplicate note href found while calculating archive statistics")

    pdf_pages = 0
    equations = 0
    for slug in slugs:
        note_path = os.path.join(ROOT, "notes", f"{slug}.html")
        with open(note_path, encoding="utf-8") as note_file:
            note_html = note_file.read()
        article_match = _STATS_ARTICLE_RE.search(note_html)
        if not article_match:
            raise ValueError(f"Missing note body in {note_path}")
        article = article_match.group(1)
        equations += len(_STATS_DISPLAY_RE.findall(article))
        equations += len(_STATS_DOLLAR_DISPLAY_RE.findall(article))
        equations += len(_STATS_EQUATION_ROW_RE.findall(article))
        equations += len(_STATS_WICK_FIGURE_RE.findall(article))

        pdf_path = os.path.join(ROOT, "output", "pdf", f"{slug}.pdf")
        if not os.path.exists(pdf_path):
            # Let a newly catalogued note reach nav-manifest.json first: the
            # PDF builder reads that manifest to discover what to render.
            # The production tests still require a PDF for every public note,
            # so an incomplete edition cannot deploy.
            print(f"  warning: missing output/pdf/{slug}.pdf; excluding it from page total")
            continue
        with open(pdf_path, "rb") as pdf_file:
            # Our Chromium/LaTeX PDFs keep Page dictionaries uncompressed.
            # The test suite cross-checks this same build-format invariant.
            page_count = len(_STATS_PDF_PAGE_RE.findall(pdf_file.read()))
        if page_count < 1:
            raise ValueError(f"Could not count pages in {pdf_path}")
        pdf_pages += page_count

    return {"notes": len(slugs), "pdf_pages": pdf_pages, "equations": equations}


def _fmt(n: int) -> str:
    return f"{n:,}"


def top_index_page(categories: list[dict]) -> str:
    cards = []
    for cat in categories:
        count = cat['body'].count('<li class="catalogue__item">')
        cards.append(f'<a class="subject-link" href="#{cat["slug"]}"><span>{cat["title"]}</span><small>{count} notes</small></a>')
    cards_html = "\n".join(cards)
    stats = compute_stats(categories)
    stats_html = f"""
    <ul class="stats" aria-label="Notebook statistics">
      <li aria-label="{_fmt(stats['notes'])} notes"><span class="stats__num" data-count="{stats['notes']}">{_fmt(stats['notes'])}</span><span class="stats__label">notes</span></li>
      <li aria-label="{_fmt(stats['pdf_pages'])} PDF pages"><span class="stats__num" data-count="{stats['pdf_pages']}">{_fmt(stats['pdf_pages'])}</span><span class="stats__label">PDF pages</span></li>
      <li aria-label="{_fmt(stats['equations'])} displayed equations"><span class="stats__num" data-count="{stats['equations']}">{_fmt(stats['equations'])}</span><span class="stats__label">equations</span></li>
    </ul>"""
    work_sections = []
    for cat in categories:
        count = cat['body'].count('<li class="catalogue__item">')
        work_sections.append(f"""
  <section class="section work-subject" id="{cat['slug']}">
    <div class="work-subject__heading">
      <div><p class="hero__eyebrow">{count} notes</p><h2>{cat['title']}</h2></div>
      <a href="notes-{cat['slug']}.html">Subject page →</a>
    </div>
{catalogue_with_formats(cat['body'])}
  </section>""")
    work_sections_html = "\n".join(work_sections)
    page_title = "Theoretical Physics Notes & Worked Solutions"
    description = (
        "Physics notes, solved problems, and self-contained derivations by "
        "Yucheng (Luca) Jin in quantum field theory, general relativity, quantum "
        "mechanics, electrodynamics, and mathematical methods, in HTML and PDF."
    )
    return (
        page_chrome_head(
            page_title,
            description,
            "notes.html",
            collection_schema(page_title, description, "notes.html"),
        )
        + topbar(active="notes")
        + f"""
<main class="page page--index">

  <section class="hero">
    <div class="hero__eyebrow">A working archive</div>
    <h1>Notes</h1>
    <p class="hero__lede">
      {_fmt(stats['notes'])} sets of notes, solved problems, and derivations. Read online or download a typeset PDF.
    </p>
{stats_html}

  </section>

  <nav class="subject-index" aria-label="Browse by subject">
{cards_html}
  </nav>

{work_sections_html}

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
    r'(?:<h3(?:\s+[^>]*)?>(.*?)</h3>\s*)?<ul class="catalogue">(.*?)</ul>',
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
        group_html = (gm.group(1) or "").strip()
        primary_label = _re.search(r'<span>(.*?)</span>', group_html, _re.DOTALL)
        if primary_label:
            group_html = primary_label.group(1)
        group_title = __html_for_stats.unescape(_STATS_TAG_RE.sub("", group_html)).strip()
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
