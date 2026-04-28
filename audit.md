# Audit

Status: read-only. **No source or template files have been edited yet.**
Phase 1 done (§1–§6). Phase 2 batch 1 done (§7). Batch 2 + Phase 3 still
pending your sign-off on the open questions in §6 / §7.

---

## 1. Stack

### Static-site generator
There is no third-party SSG. The site is plain static HTML produced by a
**custom Python pipeline**:

- [build.sh](build.sh) — thin shell wrapper. `./build.sh` runs the converter once;
  `./build.sh --serve` adds `python3 -m http.server 8000`; `./build.sh --watch`
  polls `tex/` (or `fswatch` if available).
- [build/tex_to_html.py](build/tex_to_html.py) (1433 LOC) — the actual `.tex → .html`
  converter. Hand-rolled regex/brace-matcher LaTeX parser. Owns:
  paragraphisation, math-stashing, theorem/proof environments, lists,
  tables, figures, equation numbering, label/`\eqref` resolution, TOC
  injection.
- [build/feynman_convert.py](build/feynman_convert.py) (593 LOC) — converts
  `tikz-feynman` (`\feynmandiagram`, `\begin{feynman}`) blocks to **plain
  TikZ** that TikZJax can render client-side. This is bespoke; it does
  not invoke `lualatex`.

The HTML page template lives inline at [build/tex_to_html.py:948](build/tex_to_html.py:948)
(`PAGE_TEMPLATE`). All notes share that single template; the index pages
(`index.html`, `notes.html`, `research.html`) are hand-written.

### Math renderer
**MathJax 3** loaded from CDN (`tex-mml-chtml.js`). Configured at
[build/tex_to_html.py:967-997](build/tex_to_html.py:967):

- Inline delimiters: `$…$`, `\(…\)`. Display: `$$…$$`, `\[…\]`.
- Loaded TeX extensions: `physics`, `boldsymbol`, `cancel`, `ams`,
  `configmacros`. (No `mathtools`. No `mathrsfs` — see §3.)
- Output is CHTML; on-screen math uses MathJax's own MJX-TEX font
  (Computer-Modern–like). Body type is EB Garamond / Cormorant
  Garamond ([styles.css:30-31](styles.css:30)). MathJax does not inherit body font;
  this is a **deliberate two-font design**, not an inconsistency.
- Macro register (each is hard-coded into the page template):

  | Macro | Definition | Notes |
  |---|---|---|
  | `\R \C \Z \N \Q \A` | `\mathbb{R}`, …, `\mathcal{A}` | matches `tex/QFTsoln.tex:57-62` |
  | `\Lagrangian` | `\mathcal{L}` | matches preamble |
  | `\Cdot` | `\boldsymbol{\cdot}` | matches preamble |
  | `\Tr` | `\operatorname{Tr}` | not in any preamble; used in QFTschwartz body |
  | `\slashed{x}` | `\not{#1}` | polyfill for `slashed.sty` (see §3) |
  | `\wick{x}` | `\overbrace{#1}^{\!\!}` | **lossy polyfill** for `simpler-wick` (see §3 / §6) |
  | `\c{x}` | `{#1}` | swallows `\c\phi` and `\c1`-style markers from `simpler-wick` |
  | `\mathds{x}` | `\mathbb{#1}` | polyfill for `dsfont` |
  | `\Tilde{x}` | `\tilde{#1}` | matches the source's `\Tilde` (capital-T) usage |
  | `\tensor{a}{b}` | `{#1{#2}}` | polyfill for `tensor.sty` — drops the index/anchor distinction |

  No macros for: `\bra`, `\ket`, `\braket`, `\dv`, `\pdv`, `\comm`,
  `\anticomm`, `\abs`, `\norm` — these come "free" from the loaded
  `physics` MathJax extension.

### TikZ / Feynman diagrams
**Two-stage client-side render via TikZJax v1**:

1. At build time, every `\begin{tikzpicture}…\end{tikzpicture}` and
   every `\feynmandiagram[…]{…};` is extracted by
   [tex_to_html.py:441](build/tex_to_html.py:441). If it is a `tikz-feynman`
   block, [feynman_convert.py](build/feynman_convert.py) tries to translate
   it into plain TikZ.
2. The translated source is dropped into the page as
   `<script type="text/tikz">…</script>`. TikZJax (loaded from CDN)
   converts it to inline SVG in the browser. SVGs are then resized by
   [assets/resize-tikz.js](assets/resize-tikz.js).

If the converter cannot parse a `tikz-feynman` block, the LaTeX source
is shown verbatim inside `<figure class="tikz-source"><pre>…</pre></figure>`
with a "automatic conversion failed" caption.

**Critical constraint**: TikZJax preloads only
`decorations.markings` + `arrows.meta`. It does **not** load
`decorations.pathmorphing`. Consequently, the converter cannot draw
wavy photons or coiled gluons; instead it substitutes:

- photon → `dash pattern=on 2pt off 2pt, line width=0.7pt` (short-dash)
- gluon → `loosely dotted, line width=1.4pt`
- scalar → `dashed`
- ghost → `dotted`
- fermion / anti-fermion → solid line + mid-arrow marker

These are visually distinct from a real `tikz-feynman` render. See §6.

### Page chrome / progressive enhancement
- [assets/theme.js](assets/theme.js) — light/dark toggle, persisted via
  `localStorage`, applied synchronously from `<head>`.
- [assets/font-size.js](assets/font-size.js) — A−/A+ control.
- [assets/resize-tikz.js](assets/resize-tikz.js) — post-process TikZJax SVGs
  so they display at a readable size and inherit `currentColor`.
- Dark-mode patch in [styles.css:912-923](styles.css:912) overrides hard-coded
  `#000` strokes/fills baked into TikZJax SVG output.

---

## 2. File map (`.tex` ↔ rendered page)

The build script handles three flavours of conversion:

1. **`JOBS`** — extract one `\subsection{…}` per page from a multi-section
   `.tex` file. Mapping is hard-coded at
   [tex_to_html.py:21-119](build/tex_to_html.py:21).
2. **`SCHWARTZ_GROUPS`** — bundle several Schwartz-QFT subsections per page
   ([tex_to_html.py:1096-1138](build/tex_to_html.py:1096)).
3. **`WHOLE_FILE_PAGES`** — convert one `.tex` document to one HTML page
   ([tex_to_html.py:1067-1093](build/tex_to_html.py:1067)).

Plus two one-offs: the `path-integral` essay (`quantumEssay.tex`) via
`write_essay_page`, and the Peskin Final Project (`QFTsoln.tex`'s
`\section{Final Project}`) via `write_final_project`.

### `tex/` source → `notes/` page (40 pages, 14 `.tex` files)

| `.tex` source | → `notes/<slug>.html` (subsection / section anchor) |
|---|---|
| [tex/QM.tex](tex/QM.tex) | `qm-bound-states`, `qm-shallow-well`, `qm-sech-squared` |
| [tex/ED.tex](tex/ED.tex) | `ed-retarded`, `ed-lienard-wiechert`, `ed-relativistic-uniform`, `ed-gauge-plane-wave`, `ed-moving-mirror`, `ed-covariant-ohms`, `ed-dielectric-sphere`, `ed-frustrated-tir` |
| [tex/MM.tex](tex/MM.tex) | `mm-jordans-lemma`, `mm-convolution-fourier`, `mm-residues`, `mm-contour-integration`, `mm-laplace-bromwich`, `mm-variational-euler` |
| [tex/DE.tex](tex/DE.tex) | `de-greens-function`, `de-images-laplace`, `de-greens-identity-halfspace` |
| [tex/TDSP.tex](tex/TDSP.tex) | `tdsp-joule-thomson`, `tdsp-adiabatic-water`, `tdsp-spin-half`, `tdsp-interacting-spin` |
| [tex/QFTsoln.tex](tex/QFTsoln.tex) | `peskin-6-2`, `peskin-7`, `peskin-final` (final-project section) |
| [tex/QFTschwartz.tex](tex/QFTschwartz.tex) | `schwartz-classical-field`, `schwartz-second-quantization`, `schwartz-spin-1`, `schwartz-spinors`, `schwartz-qed-tree`, `schwartz-path-integrals` |
| [tex/quantumEssay.tex](tex/quantumEssay.tex) | `path-integral` |
| [tex/11dsupergravity.tex](tex/11dsupergravity.tex) | `psi-11d-supergravity` |
| [tex/BransDicke.tex](tex/BransDicke.tex) | `gr-brans-dicke` |
| [tex/Correlation_functions_in_QM.tex](tex/Correlation_functions_in_QM.tex) | `psi-correlation-functions-qm` |
| [tex/DTQFTPS1.tex](tex/DTQFTPS1.tex) | `tong-qft-ps1` |
| [tex/DTQFTPS2.tex](tex/DTQFTPS2.tex) | `tong-qft-ps2` |
| [tex/DTQFTPS3.tex](tex/DTQFTPS3.tex) | `tong-qft-ps3` |

- Total HTML notes built: **40**, all linked from `notes.html`. No orphans
  in either direction (verified by `comm` between catalogue links and
  `notes/`).
- Catalogue → page links checked: zero dead links; zero pages outside
  the catalogue.

### Orphan/redundant directory
- **[tex-served/](tex-served/)** contains a partial older copy of `tex/`
  (8 of the 14 source files, byte-identical to `tex/`). Nothing in the
  site references it — no HTML, no CSS, no script, no `.gitignore` rule.
  **Recommendation:** delete `tex-served/` after you've confirmed it's
  unused. Will not touch it without your sign-off.

### Diagram / figure asset map
The Path-Integral essay references images by Chinese-encoded filenames
in the source; the converter has a hard-coded translation table at
[tex_to_html.py:672-679](build/tex_to_html.py:672) mapping them to
[assets/path-integral-fig{1..5}-*.png](assets/). All five referenced
PNGs exist in `assets/`. No missing-image references found.

---

## 3. Package inventory

Most `tex/*.tex` files are **fragments** with no preamble (e.g. `QM.tex`,
`DE.tex`, `ED.tex`, `MM.tex`, `TDSP.tex`, `BransDicke.tex`,
`11dsupergravity.tex`, `Correlation_functions_in_QM.tex`,
`DTQFTPS{1,2,3}.tex`). They presumably get `\input`'d into a parent
document with the QFT preamble. Only `QFTschwartz.tex`, `QFTsoln.tex`
and `quantumEssay.tex` carry a full preamble.

The packages that actually appear in any preamble across `tex/`:

| Package | Used by | Web stack support | Status |
|---|---|---|---|
| `inputenc` (`utf8`) | Schwartz, Peskin, essay | n/a — HTML is UTF-8 by default | OK |
| `amsmath`, `amssymb`, `amsthm`, `amsfonts`, `amscd` | Schwartz, Peskin, essay | MathJax `ams` extension (loaded) | OK |
| `cancel` | Schwartz, Peskin | MathJax `cancel` extension (loaded) | OK |
| `physics` | Schwartz, Peskin, essay | MathJax `physics` extension (loaded) | OK |
| `boldsymbol` | (loaded by `physics`) | MathJax `boldsymbol` extension (loaded) | OK |
| `mathtools` | not used | not loaded | n/a (could enable defensively) |
| `slashed` | Schwartz, Peskin | **none** — replaced by `\slashed{x} → \not{#1}` polyfill | **glyph mismatch** — see §6 |
| `simpler-wick` | Schwartz, Peskin | **none** — replaced by `\wick{x} → \overbrace{#1}^{\!\!}` polyfill | **lossy** — see §6 |
| `dsfont` | Schwartz, Peskin | **none** — replaced by `\mathds{x} → \mathbb{#1}` polyfill | acceptable (MathJax's `\mathbb{1}` differs from real `\mathds{1}` glyph; flag for review) |
| `mathrsfs` | Schwartz, Peskin | **not registered** — `\mathscr{…}` would render as plain text | not currently triggered (no `\mathscr` in source body — verified by grep), but should be polyfilled defensively |
| `tikz`, `tikz-feynman` | Schwartz, Peskin | TikZJax + custom converter | **partial** — see §1 / §6 |
| `tikz-cd` | not used (no `\begin{tikzcd}` anywhere) | not loaded | n/a |
| `geometry`, `fullpage`, `setspace`, `multicol`, `wrapfig`, `fancyhdr`, `lastpage`, `titlesec`, `titlepage`, `framed`, `IEEEtrantools`, `multirow`, `booktabs`, `xcolor`, `enumitem`, `empheq`, `tcolorbox`, `calc`, `hyperref`, `graphicx`, `cite` | various | typesetting / page-layout / bibliography — no semantic meaning on web | safe to ignore (the converter strips them along with `\setlength`, `\title`, `\maketitle`, etc.) |

### Custom `\newcommand`s in source (only `tex/QFTsoln.tex` has them — see [tex/QFTsoln.tex:57-64](tex/QFTsoln.tex:57))

- `\R \C \Z \N \Q \A` — registered in MathJax ✓
- `\Lagrangian`, `\Cdot` — registered ✓

`tex/quantumEssay.tex` defines a few `\newcommand`s for student-info
strings (`\StudentName`, `\EssayTitle`, …) — none are referenced from
note bodies, so no polyfill is needed. They are stripped along with the
title-page block.

### Theorem environments declared in `QFTschwartz.tex`/`QFTsoln.tex`
`thm`, `defn`, `reg`, `exer`, `note`, `conv`, `rem`, `lem`, `cor`, `ex`.
**Currently unused in any `.tex` body** — verified by grep across all
`tex/*.tex`. The converter at [tex_to_html.py:419-428](build/tex_to_html.py:419)
maps the *standard* names (`theorem`, `lemma`, `proposition`, `proof`,
`definition`, `remark`, `example`, `corollary`) to `<h4>Label.</h4>`.
Worth pointing out: if a future note ever uses `\begin{thm}` or
`\begin{lem}` it will leak through unconverted. **Recommendation**: add
the short-form aliases to the converter when convenient. Flag only — no
fix needed today.

### Equation numbering scheme
- `\numberwithin{equation}{section}` is **not** present in any source.
  Default LaTeX numbering is per-document: `(1), (2), …`.
- The converter resets the counter at every "topic" boundary
  ([tex_to_html.py:196-199](build/tex_to_html.py:196)) — i.e. every Schwartz
  subsection, every Tong-PS subsection, every essay section. This is
  *not* what `pdflatex` does on the original `.tex`; `pdflatex` would
  produce monotonically increasing numbers across the whole document.
  **Need your call**: keep the per-topic reset (current behaviour, easier
  to read on the web) or restore monotonic numbering to match the
  pdfTeX render. I suspect you want per-topic — confirm.

---

## 4. Build pipeline (preprocessing path)

```
tex/*.tex
   │
   │   build.sh  (one-shot, --serve, or --watch)
   ▼
build/tex_to_html.py
   │   1. Extract subsection / section / whole-file body (regex + brace match)
   │   2. stash_tikz()   — pull tikzpicture / feynmandiagram blocks aside,
   │                       run feynman_convert.py over tikz-feynman ones
   │   3. strip_tex_only_constructs() — drop \vspace, \setlength,
   │                       turn tcolorbox/solution/center/etc. into HTML
   │   4. stash_math()   — pull \[...\], $...$, equation/align/gather/multline
   │                       into a stash; assign equation numbers; capture \label
   │   5. transform_text() — \textbf, lists, sections, \href, \cite-strip,
   │                       \footnote → "(...)", paragraphisation
   │   6. stash.restore() — replay math placeholders into the HTML
   │   7. render_tikz_one() — substitute TikZ markers with <script type="text/tikz">
   │   8. resolve \eqref / \ref against captured labels
   │   9. build_toc_and_inject_ids() — generate <nav class="note__toc">
   │  10. render_page() — substitute @@TITLE@@, @@BODY@@, etc. into PAGE_TEMPLATE
   ▼
notes/<slug>.html
   │
   │   browser
   ▼
   ┌──────────────────────────────────────┐
   │  MathJax 3 typesets all $..$ / \[..\] │
   │  TikZJax compiles <script text/tikz>  │
   │  resize-tikz.js scales each SVG       │
   │  theme.js / font-size.js (chrome)     │
   └──────────────────────────────────────┘
```

No node, no bundler, no PDF compilation, no `lualatex`. Everything is
either Python at build time or vanilla JS at view time.

---

## 5. Things I noticed in passing (NOT yet acted on)

These will be the starting points for the Phase 2 systematic per-page
diff. Listed here so you can see what to expect; none of them have been
edited yet.

### a. Photons & gluons render as dashes / dots, not waves / coils
TikZJax doesn't load `decorations.pathmorphing`. The converter
substitutes a short-dash for photon and a dotted line for gluon. Affects
**6 pages** with TikZ figures: `peskin-6-2`, `peskin-final`,
`schwartz-second-quantization`, `schwartz-qed-tree`, `schwartz-spin-1`,
`tong-qft-ps2`. This is the largest visual mismatch with the LaTeX
render. (Also: `\vertex [blob]` markers are emitted as empty nodes — the
filled circle/blob from `tikz-feynman` is not drawn.)

Recommended fix is the one you proposed in §3b: **pre-render each
`\begin{tikzpicture}` to standalone SVG via `lualatex` + `dvisvgm`**,
inline the SVG with `currentColor`, drop TikZJax. I'll wait for the
green light before scripting that.

### b. Wick contractions: multi-pair contractions render as one big overbrace
The current `\wick{…}` polyfill draws **one** `\overbrace` over the
entire argument and `\c{x}` reduces to `{x}`. For single-pair contractions
this is acceptable. For multi-pair contractions like
[tex/QFTschwartz.tex:1247](tex/QFTschwartz.tex:1247):

```latex
\wick{\c1 \phi_0(x_1)\c2 \phi_0(x_2)\c1 \phi_0(x)\c3 \phi_0(x)\c4 \phi_0(x)\c2 \phi_0(y)\c3 \phi_0(y)\c4 \phi_0(y)}
```

the four numbered contractions collapse to one indistinct overbrace —
the pair structure is lost. There are **6 occurrences** in
`schwartz-second-quantization`+`schwartz-qed-tree`. Per your §3d
preference: pre-render every Wick equation as inline SVG. Will list the
exact equations once you've green-lit the SVG pipeline.

### c. `equation-row` HTML is malformed
At [tex_to_html.py:577-617](build/tex_to_html.py:577) the converter emits
display equations that contain TikZ figures as a `<div class="equation-row">…</div>`.
The paragraphizer that follows (which splits on blank lines) sometimes
splits the div across multiple `<p>` paragraphs and ends up emitting
e.g. `<p><span …>(1)</span></div></p>` — `<div>` closing inside an
already-closed `<p>`. Visible in `peskin-6-2.html` and `peskin-final.html`.
This is invalid HTML; browsers fix it up but it's a real bug. Fix is a
small change to the paragraphizer logic.

### d. Inline math next to/inside diagrams
You flagged that captions render in a different math font. I haven't yet
located a *failing* example in the current notes (`figcaption`s contain
no math in the rendered HTML I sampled). I will look for and document
specific failing cases in Phase 2 before reaching for `processClass` /
`ignoreClass` knobs.

### e. `tex-served/` is unused
Redundant copy of 8 of the 14 source files. Recommend deletion (with
your OK).

### f. `\mathds{1}` glyph fidelity
The polyfill maps `\mathds{1}` → `\mathbb{1}`. MathJax's `\mathbb{1}`
glyph differs from the real `\mathds{1}` from `dsfont`. Used in
`schwartz-spinors`. May or may not be a problem you care about — flag
only.

---

## 6. Phase 2 / Phase 3 plan (for your review)

### Phase 2 — per-page diff
For each of the 40 `(notes/<slug>.html, tex source body)` pairs:

1. Read the source body.
2. Open the rendered page in a headless browser (or inspect the HTML
   directly) and walk every display equation, every inline equation,
   every `<figure>`, every theorem/proof block.
3. Diff character-by-character against the source body, allowing for
   legitimate macro expansion.
4. Log discrepancies in a per-page table appended to this `audit.md`,
   one row per discrepancy: source line / rendered location / type / fix.

I'd like to do this in **two batches** (so the report stays
reviewable):

- Batch 1: short pages — QM (3), DE (3), MM (6), TDSP (4),
  ED (8), Tong PS (3). All prose+algebra, no tikz-feynman.
- Batch 2: long QFT pages — Schwartz (6), Peskin (3),
  PSI (2), Brans–Dicke, 11d sugra, path-integral essay. Diagrams and
  Wick.

### Phase 3 — fixes, in commit-sized chunks
Tentative order, each line is one commit:

1. Fix malformed `equation-row` paragraph wrapping (§5c) — pure HTML bug.
2. Add `\mathscr` polyfill + the missing `physics` macros that `physics`
   doesn't already cover (§3 inventory) — config-only.
3. Caption-math scope, once a real failing example is in hand (§5d).
4. Pre-render `tikz-feynman` → SVG via `lualatex` + `dvisvgm` (§5a).
   Replace TikZJax for those blocks. Will need your OK to invoke
   `lualatex` (likely already on your machine — I'll check
   `which lualatex` once you say go).
5. Pre-render Wick-contraction equations to SVG (§5b). Same pipeline.
6. Display-equation overflow audit (long integrands). Per your §3a, if
   the source provides line-breaks I'll honour them; for any equation
   that overflows without source-level breaks I'll **stop and ask** rather
   than choose a strategy.
7. Sweep for remaining macro mismatches identified in Phase 2.

I will **not** start any of these until you've reviewed this report.

---

## Decisions taken (recorded in chat)

1. **Equation-numbering**: per-topic reset, but format `(n.eq)` where
   `n` = current `<h2>` topic index on the page, `eq` = counter
   resetting at each `<h2>`. Implementation deferred to Phase 3.
2. **`tex-served/`**: recommend delete; awaiting OK.
3. **`lualatex` + `dvisvgm`**: OK if installed; will check + ask before
   any install.
4. **Wick contractions**: pre-render to SVG (more robust + consistent).
5. **Fonts**: keep current (EB Garamond prose + MathJax CM math); ensure
   *consistency* across all pages (caption math, table math, sidebar
   math, theorem-box math all reach MathJax with the same scope; same
   body-font fallback chain on every page).

---

## 7. Phase 2 — Batch 1 (27 short prose pages)

Audited: QM (3) · DE (3) · MM (6) · TDSP (4) · ED (8) · Tong QFT PS (3).
**No diagrams, no Wick contractions in this batch** — those land in
batch 2.

Results: every page renders the prose, lists, and inline math correctly.
Theorem/`\eqref`/`\ref` resolution works. The discrepancies are
**five recurring bugs**, each affecting many pages — fixing them is a
small set of changes to `build/tex_to_html.py` + the page template.

### Bug 1 — Figures with TikZ/pgfplots only (no `\includegraphics`) are silently dropped

[build/tex_to_html.py:660](build/tex_to_html.py:660) — `_early_figure_repl`
returns `""` whenever the `\begin{figure}…\end{figure}` body has no
`\includegraphics`. Every figure whose body is a `tikzpicture` / `axis`
plot drops out *with its caption and label*. The `\x00TIKZ%d\x00`
placeholder that `stash_tikz()` already created is also stranded
(orphaned in `stash["tikz"]` but never restored).

**Affected pages and figures (8 figures, 7 pages):**

| Page | `.tex` line | Figure content | Caption (lost) |
|---|---|---|---|
| `qm-shallow-well` | [tex/QM.tex:88](tex/QM.tex:88) | pgfplots `axis`: graphical solution `k cot ka = -κ(k)` with two semicircles + intersection dot | "Graphical solution of the odd-parity bound-state equation…" |
| `qm-sech-squared` | [tex/QM.tex:210](tex/QM.tex:210) | pgfplots `axis`: sech² potential well | "The sech-squared potential…" |
| `qm-sech-squared` | [tex/QM.tex:276](tex/QM.tex:276) | pgfplots `axis`: ground-state wavefunction `1/cosh x` | "Ground state wavefunction χ₀(x) = N sech x…" |
| `tdsp-joule-thomson` | [tex/TDSP.tex:16](tex/TDSP.tex:16) | plain TikZ pipe schematic with pistons / porous barrier | "Joule-Thomson process: gas is pushed…" |
| `tdsp-adiabatic-water` | [tex/TDSP.tex:207](tex/TDSP.tex:207) | TikZ PT phase diagram for water | "Schematic PT phase diagram for water…" |
| `ed-lienard-wiechert` | [tex/ED.tex:243](tex/ED.tex:243) | plain TikZ light-cone diagram (`x⁰` vs `x`) | (untitled) |
| `ed-relativistic-uniform` | [tex/ED.tex:439](tex/ED.tex:439) | pgfplots `axis` figure | (untitled) |
| `ed-dielectric-sphere` | [tex/ED.tex:773](tex/ED.tex:773) | plain TikZ sphere diagram | (untitled) |

**Fix path** (Phase 3): use the same `lualatex` + `dvisvgm` pre-render
pipeline that we'll set up for `tikz-feynman`. These figures don't have
the wave/coil-line problem, so they're cleaner targets — pgfplots and
plain TikZ both compile fine. The figure handler should keep the figure
block when there's no `\includegraphics` and emit the pre-rendered SVG.

### Bug 2 — Equation numbering out of document order when `align` mixes with `equation`

[build/tex_to_html.py:553-624](build/tex_to_html.py:553) — `stash_math`
processes the `DISPLAY_ENVS` list in *type order*, not document order:
all `equation` envs are numbered first (1, 2, …), *then* `equation*`,
*then* `align`, etc. Result: in any subsection that mixes `equation` and
`align`, the align blocks are pushed to the end of the numbering range.

**Example** ([tex/ED.tex] subsection "Liénard–Wiechert"): there are
22 `\begin{equation}` blocks and 5 `\begin{align}` blocks interleaved.
Document order would number them 1, 2, …, 27. Current rendering on
[notes/ed-lienard-wiechert.html](notes/ed-lienard-wiechert.html) tags
them in this order:

```
1, 23, 2, 3, 4, 5, 6, 24, 7, 8, 25, 9, 10, …, 16, 26, 27, 17, …, 22
```

**Pages affected** (all subsections that mix `equation` with `align`):

| Page | eq envs | align envs |
|---|---|---|
| `qm-sech-squared` | 11 | 1 |
| `de-greens-function` | 19 | 4 |
| `de-images-laplace` | 10 | 3 |
| `de-greens-identity-halfspace` | 10 | 1 |
| `mm-jordans-lemma` | 8 | 1 |
| `mm-convolution-fourier` | 6 | 2 |
| `mm-contour-integration` | 11 | 3 |
| `ed-retarded` | 23 | 2 |
| `ed-lienard-wiechert` | 22 | 5 |
| `ed-moving-mirror` | 9 | 1 |
| `ed-frustrated-tir` | 21 | 1 |
| `tong-qft-ps2` | 18 | 4 |
| `tong-qft-ps3` | 22 | 9 |

**13 of 27 pages** affected. (The 14 unaffected pages contain only
`equation` envs — no align, no gather.)

**Additional sub-issue**: pdflatex numbers each row of an `align` block
separately (1 row → 1 number unless `\notag` / `\nonumber`). The
converter currently assigns **one** number to the whole align block and
wraps it in `\begin{aligned}…\end{aligned}`. So even after the
ordering bug is fixed, multi-row aligns will still under-number compared
to pdflatex.

For batch 1 most aligns are fully marked `\notag` per row (so they
*should* have one number for the whole block), but not all are. Need to
audit per-align in Phase 3 — easier once we switch to `(n.eq)`
numbering anyway.

**Fix path** (Phase 3): rewrite `stash_math` to walk the document
linearly, assigning numbers in source order. Same change naturally
supports the `(n.eq)` format — track current topic index as we go and
emit `\tag{n.eq}`.

### Bug 3 — `equation-row` HTML (already noted in §5c)

Reconfirmed by inspection on `peskin-6-2.html` and `peskin-final.html`.
This belongs to batch 2 (those are diagram pages) — flagged here only
because the same paragraphizer logic runs on every page. The 27 pages
in batch 1 are unaffected because none of them contain a TikZ figure
embedded inside an `equation` env.

### Bug 4 — `\Tr{X}` macro polyfill drops the parentheses

Page template [build/tex_to_html.py:984](build/tex_to_html.py:984)
defines `Tr: '\\operatorname{Tr}'` (zero-arg). In source the user writes
`\Tr{γ^μγ^ν}` expecting `Tr(γ^μγ^ν)` with parens. With the current
0-arg macro, the `{γ^μγ^ν}` is a math group following the `\operatorname{Tr}`
operator, so MathJax renders it as `Tr γ^μγ^ν` — operator and operand
are juxtaposed with no fence.

`\Tr{...}` occurs **12 times** in `tex/DTQFTPS3.tex` (page
`tong-qft-ps3`). Also appears in `tex/QFTsoln.tex` (page `peskin-final`
— that's batch 2). Source-side definition isn't in the QFTsoln preamble
either, so it presumably comes from a parent file the user `\input`s.
For our purposes the polyfill should be:

```js
Tr: ['\\operatorname{Tr}\\!\\left(#1\\right)', 1]
```

(or `\\bigl(\\bigr)` if you want the parens to grow with the
operand). **Need your call** on the paren style for the polyfill.

### Bug 5 — Solution-marker style is inconsistent across pages

The `.tex` source uses two different conventions to mark a solution:

| Source | Files | Renders as |
|---|---|---|
| `\begin{solution}…\end{solution}` | `DTQFTPS1.tex`, `DTQFTPS2.tex`, `DTQFTPS3.tex` | `<aside class="solution"><div class="solution__label">Solution.</div>…</aside>` (boxed sidebar with header) |
| `\underline{\textbf{Solution}}` | `QM.tex`, `DE.tex`, `MM.tex`, `TDSP.tex`, `ED.tex` | inline `<u><strong>Solution</strong></u>` (no box, no styled marker) |
| `\textbf{Solution:}` | same files (mixed within) | inline `<strong>Solution:</strong>` |

So Tong-PS pages have a clean styled solution box; QM/DE/MM/TDSP/ED
pages just have an underlined "Solution" inline. **This is the §3f
"site-wide consistency" gap on its own.**

Two ways to unify:
- (a) leave source untouched; add a converter pass that recognises
  `\underline{\textbf{Solution}}` and `\textbf{Solution:}` at the start
  of a paragraph and rewrites them to the styled `<aside>` form.
  Touches no `.tex` source.
- (b) edit the 5 source files to use `\begin{solution}…\end{solution}`
  consistently. Edits the source. Per your hard constraints — "Do not
  modify the mathematics or prose" — this is structural not prose, so
  it might be allowed; **need your call**.

**Recommendation**: option (a). It keeps `tex/*.tex` exactly as you
have them and lets the converter normalise on the way out.

### Other observations from batch 1 (informational only — not bugs)

- **`enumerate[label=…]` labels are dropped**. e.g.
  `\begin{enumerate}[label=\roman*.]` (Roman-numeral list) renders as
  a default `<ol>` (1, 2, 3…). The visual hierarchy of i / ii / iii /
  iv is lost. Affects `tong-qft-ps1/2/3` and the PSI / Brans-Dicke
  pages (batch 2). Easy fix — convert `\roman*`, `\alph*`, etc. to the
  matching `<ol type="i">` / `<ol type="a">`.
- **`<u><strong>Solution</strong></u>` directly attached to the
  preceding equation** (e.g. `qm-shallow-well`, line 96 of rendered
  HTML). Caused by no blank line between `\end{equation}` and
  `\underline{\textbf{Solution}}` in the source. pdflatex would render
  the same way (continuation of the same paragraph), so this is
  faithful — *not* a bug. Listed here only so you know I considered
  it. If solution-marker rewriting (Bug 5) lands as option (a), this
  goes away naturally because the marker becomes a block-level
  `<aside>`.
- **Macro-expansion artefacts in some HTML**: `\Tilde{q}` (capital-T,
  user's source) appears literally in `peskin-6-2.html` (batch 2) —
  resolved by the global `Tilde: ['\\tilde{#1}', 1]` macro. Verified
  rendering: works correctly.
- **`\dd x`**, **`\notag`**, **`\boxed{…}`** all render correctly via
  the loaded MathJax extensions. No action.
- **`\Lagrangian`, `\Cdot`** — defined globally, render correctly. No
  action.
- **HTML validity**: `notes/qm-bound-states.html` and similar batch 1
  pages all pass the eyeball "looks like well-formed HTML" check. The
  `<p><div></div></p>` malformation noted in §5c is exclusive to
  pages with `equation-row` blocks, all of which are in batch 2.

### Phase 2 batch 1 — verdict

The 27 short pages have **two structural bugs (1 + 2)** that need fixes
in the converter, **two cosmetic bugs (4 + 5)** that need either macro
or converter tweaks, and **one carry-over (3)** that gets fixed during
batch 2. None of the prose or maths content has been corrupted by the
converter — what's there is faithful to the source. The systemic gaps
are dropped figures and out-of-order numbering.

---

## 8. Style reference: `elegantphys.sty`

User supplied [`elegantphys.sty`](file:///Users/lucajin/Downloads/elegantphys.sty)
(used in another LaTeX project) as the canonical style for tcolorbox
environments and equation numbering. **Treat this as the truth source
for visual/structural decisions on the web.** Key directives extracted:

- **`\numberwithin{equation}{section}`** (line 195) — confirms `(n.eq)`
  numbering matches the user's pdflatex render.
- **`\begin{solution}`** (lines 183–194) — `tcolorbox` with
  `colback=lightblue`, `colframe=lightblue`, no border-rule,
  `borderline west={3pt}{0pt}{darkgray}` (3pt dark-gray left bar),
  inline `\textbf{Solution.}\quad` label (no separate header line).
  - Colours: `darkgray = RGB(60, 60, 60)`,
    `lightblue = RGB(225, 235, 248)`,
    `rulecolor = RGB(160, 160, 160)`.
  - **Web target for `aside.solution`**: light-blue background, 3 px
    dark-gray left bar, **inline** bold "Solution." label. Drop the
    current `<div class="solution__label">Solution.</div>` standalone
    header — `elegantphys.sty` puts the label inline.
- **`theorem`** — lightgray bg, black left bar (3pt), no rule.
- **`definition`** / **`lemma`** / **`proposition`** / **`corollary`** —
  lightgray bg, dark-gray left bar (3pt), no rule.
- **`remark`** / **`note`** — white bg, light-rule left bar (2pt), no
  rule.
- **Theorem numbering** is `[section]` and shared across
  theorem/definition/lemma/proposition/corollary (one counter reset per
  section). `remark` and `note` are unnumbered (`\newtheorem*`).
- **`\boxedeq{X}`** — `tcolorbox` containing one numbered
  `\begin{equation}{X}\end{equation}`, lightgray bg, black frame,
  0.8 pt rule. Treat as a single boxed display equation.
- **`mathtools`** is in the preamble — should be enabled in MathJax
  (`packages: '[+]': [..., 'mathtools']` + `loader.load`).
- **`\usepackage{lmodern}`** — confirms math+body in pdflatex render is
  Latin Modern. Doesn't affect the web (we keep EB Garamond + MathJax
  CHTML, per your decision).

These mappings are not currently triggered by anything in `tex/*.tex`
(the existing sources use `\begin{tcolorbox}` and `\boxed{…}` directly,
not the `elegantphys.sty` envs), but future notes that use this style
file will expect them, so I'll wire it up once.

## 9. Decisions for Phase 3 (chat answers, recorded)

In addition to §6:

1. **`\Tr{X}`** → auto-sizing parens:
   `Tr: ['\\operatorname{Tr}\\!\\left(#1\\right)', 1]`.
2. **Solution markers** — standardise on the web per `elegantphys.sty`
   (§8). Converter will normalise three source forms — `\begin{solution}`,
   `\underline{\textbf{Solution}}`, `\textbf{Solution:}` — onto a single
   styled `<aside class="solution">`. **No `.tex` source edits.**
3. **`enumerate[label=…]`** — keep as-is (default `<ol>`, custom label
   specs ignored).

## 10. Still open before Phase 3 starts

From §6:

1. **`tex-served/`**: delete (recommended) or keep?
2. **`lualatex` + `dvisvgm`**: OK to invoke from the build script if
   already installed? (I'll `which lualatex` once you say go and ask
   before any install.)

Both blockers for Phase 3 only — batch 2 (audit) is read-only and
doesn't need either answer to proceed.

---

## 11. Phase 2 — Batch 2 (13 QFT pages with diagrams + Wicks)

Audited: Schwartz (×6 — `schwartz-classical-field`, `schwartz-second-quantization`,
`schwartz-spin-1`, `schwartz-spinors`, `schwartz-qed-tree`,
`schwartz-path-integrals`) · Peskin (×3 — `peskin-6-2`, `peskin-7`,
`peskin-final`) · `path-integral` (essay) · `gr-brans-dicke` ·
`psi-11d-supergravity` · `psi-correlation-functions-qm`.

Source-volume context (for scale):

| File | Pages | Eqs | Aligns | TikZ pic | Feynman | Wicks | `[blob]` |
|---|---|---|---|---|---|---|---|
| QFTschwartz.tex | 6 | 737 | 5 | 42 | 39 | 7 | 4 |
| QFTsoln.tex | 3 | 102 | 0 | 5 | 5 | 0 | 1 |
| quantumEssay.tex | 1 | 70 | 0 | 0 | 0 | 0 | 0 |
| BransDicke.tex | 1 | 26 | 3 | 0 | 0 | 0 | 0 |
| Correlation…QM | 1 | 41 | 6 | 0 | 0 | 0 | 0 |
| 11dsupergravity | 1 | 13 | 0 | 0 | 0 | 0 | 0 |

### Bug 6 — Photons render as dashes, gluons as dots (no wave / coil)

`build/feynman_convert.py:466-475` substitutes:
- photon → `dash pattern=on 2pt off 2pt` (short-dash horizontal)
- gluon → `loosely dotted, line width=1.4pt`

…because TikZJax doesn't load `decorations.pathmorphing`. Affects every
Feynman diagram on **6 pages**:

| Page | Diagrams | Sample issues |
|---|---|---|
| `peskin-6-2` | 1 | photon to blob target → dashed line + missing blob |
| `peskin-final` | 4 | photons + loop diagrams |
| `tong-qft-ps2` | 2 | plain TikZ schematics — render OK |
| `schwartz-second-quantization` | 8 | scalar lines (already dashed in source — these render correctly), photon propagator |
| `schwartz-qed-tree` | 20 | every QED rule + loop / Møller / Compton diagrams |
| `schwartz-spin-1` | 13 | photon propagators + scalar QED diagrams |

**Fix**: pre-render every `\begin{tikzpicture}…\end{tikzpicture}` and
every `\feynmandiagram[…]{…};` to standalone SVG via `lualatex` +
`dvisvgm`, inline the SVG, drop TikZJax. SVG inherits `currentColor`
so dark-mode keeps working without the per-attribute overrides at
`styles.css:912-923`.

### Bug 7 — `[blob]` markers render as empty nodes

`feynman_convert.py` parses `\vertex [blob] (a) {};` and `b [blob]`
but doesn't emit any styled node — just `\node (b) at (x,y) {};`. The
filled circle that `tikz-feynman` draws for "complicated coupling" is
gone.

**Affected**: 4 blob declarations in QFTschwartz, 1 in QFTsoln — pages
`peskin-6-2` (1), `schwartz-spin-1` (≥3), `schwartz-qed-tree` (≥1).
Will be fixed by the SVG pre-render (Bug 6) — `lualatex` renders blobs
natively.

### Bug 8 — Wick contractions: pair structure lost, multi-pair shows raw digits

The current MathJax polyfills:

```js
wick: ['{\\overbrace{#1}^{\\!\\!}}', 1],
c:    ['{#1}', 1]
```

draw **one** overbrace over the entire `\wick{…}` argument and consume
the next token after `\c`. For multi-pair contractions like
[QFTschwartz.tex:1247](tex/QFTschwartz.tex:1247):

```latex
\wick{\c1 \phi_0(x_1)\c2 \phi_0(x_2)\c1 \phi_0(x)\c3 \phi_0(x)\c4 \phi_0(x)\c2 \phi_0(y)\c3 \phi_0(y)\c4 \phi_0(y)}
```

`\c1` consumes `1` as the argument (literal digit), `\c2` consumes `2`,
… so the rendered output is **`overbrace{1 φ₀(x₁) 2 φ₀(x₂) 1 φ₀(x) 3 φ₀(x) 4 φ₀(x) 2 φ₀(y) 3 φ₀(y) 4 φ₀(y)}`** — the pair labels appear as bare digits inside the math, and the four contraction arcs collapse to one giant overbrace. Catastrophic.

**Wick locations** (6 equations across 2 pages):
- `schwartz-second-quantization`:
  - eq (40), eq (41), eq (46), eq (47), eq (49) — single-pair `\c\phi`
    examples in the Wick-theorem derivation.
- `schwartz-qed-tree`:
  - eq (49) Wick-contraction of two-point function.

**Fix**: pre-render each `\wick{…}` equation to inline SVG via
`lualatex` (with the `simpler-wick` package, which is already in the
source preamble). Per your decision in §6 → option 1.

### Bug 9 — `\begin{shaded}` is silently stripped (boxed-equation style lost)

`build/tex_to_html.py:357-358` removes `\begin{shaded}` / `\end{shaded}`
but the inner `\begin{equation}` survives **without the boxed visual
emphasis the user wanted**.

**Source usage (54 occurrences in QFTschwartz.tex)** — example
[QFTschwartz.tex:107](tex/QFTschwartz.tex:107) wraps the Euler–Lagrange
equation; line 121 wraps the Noether current. Rendered: indistinguishable
from any other display equation.

**Fix path**: map `\begin{shaded}{\begin{equation}X\end{equation}}\end{shaded}`
to a styled `<aside class="boxed-equation">` matching the
`elegantphys.sty:\boxedeq` style (lightgray bg, black frame, 0.8 px
rule). One CSS class + one converter handler.

### Bug 10 — `equation-row` HTML malformation (carry-over from §5c)

Confirmed visible in:
- [peskin-6-2.html:91-106](notes/peskin-6-2.html:91)
- [peskin-final.html:101-122](notes/peskin-final.html:101) (and 3 more)
- [schwartz-qed-tree.html:104-115](notes/schwartz-qed-tree.html:104)
  (and ~19 more on this page)
- [schwartz-second-quantization.html](notes/schwartz-second-quantization.html), `schwartz-spin-1.html`, `tong-qft-ps2.html`

Pattern (from `peskin-6-2.html:106`):

```html
<p><span class="equation-num">(1)</span></div></p>
```

`<div class="equation-row">` opens with no surrounding `<p>`, then the
following blank line in source flips the paragraphizer back into
"wrap in `<p>`" mode, so the `</div>` closer ends up inside a `<p>`.
Browsers auto-correct, but it's malformed HTML and validates poorly.

**Fix**: in `build/tex_to_html.py:794-802`, mark `<div class="equation-row">`
as block-level so the paragraphizer doesn't wrap its contents.

### Bug 11 — `\Tr{X}` should be auto-sized parens; `\Tr[X]` should stay literal brackets

User's source uses BOTH:
- `\Tr{γ^μγ^ν}` — wants parens (per chat answer §9).
- `\Tr[\slashed{p}_2γ^μ\slashed{p}_1γ^ν]` — literal brackets.

`\Tr{X}` count: 56 occurrences across QFTschwartz/QFTsoln/DTQFTPS3.
`\Tr[X]` count: 30+ occurrences in QFTsoln.tex (peskin-final). Both
forms appear in the same equations.

A 1-arg MathJax macro `Tr: ['\\operatorname{Tr}\\!\\left(#1\\right)', 1]`
won't match `\Tr[X]` (MathJax doesn't accept `[…]` as macro argument
syntax). Conversely, the current 0-arg `Tr: '\\operatorname{Tr}'`
preserves both forms but drops parens for the curly form.

**Fix**: pre-process math regions in the converter — substitute
`\Tr{...}` (balanced braces) with `\operatorname{Tr}\!\left(...\right)`
*before* MathJax sees it; leave `\Tr[...]` alone. Don't change the
runtime macro at all. This keeps `\Tr` purely 0-arg from MathJax's
perspective and gives the user both notations without conflict.

### Bug 12 — `\ref{...}` to non-equation, non-figure labels leaks raw key

Labels are captured only from `\begin{equation}…\end{equation}` (and
nested) bodies and from `\begin{figure}` blocks. `\section`,
`\subsection`, and free-standing `\label{wick}` (used as appendix
markers) are never captured. Result: `\ref{wick}` falls through to
`_clean_unmapped` and emits `wick`.

**Visible**: [path-integral.html:398](notes/path-integral.html:398) —
"see Appendix wick for derivation" (should be "see Appendix B" or
similar).

**Fix**: extend the label-collector to capture
`\section{…}\label{X}` and `\subsection{…}\label{X}` and assign them
the `<h2>` / `<h3>` index. Easy.

### Bug 13 — `enumerate` label spec dropped (carried from batch 1)

Per your decision in §9 — leave as-is. **No fix.** Mentioned in this
batch's listing because it's heavily used in `psi-11d-supergravity`
([tex/11dsupergravity.tex:13](tex/11dsupergravity.tex:13)
`\begin{enumerate}[label=\textbf{\roman*)}]`) and
`Correlation_functions_in_QM.tex`. Default `<ol>` numbering will be
used.

### Other observations — informational only

- **Theorem-like environments unused in the body**: the
  `\newtheorem{thm}…` declarations in QFTschwartz.tex never trigger;
  no `\begin{thm}` etc. anywhere in the body. The converter handles
  the standard names (`theorem`, `lemma`, `proposition`, …) but not
  the short forms (`thm`, `lem`, `cor`). When you do start using them,
  we'll need to extend the converter — flagged for the future, not now.
- **`\Lagrangian`, `\Cdot`** — render correctly. No action.
- **`\Tilde{q}`** (capital T) — renders correctly via the
  `Tilde: ['\\tilde{#1}', 1]` macro. Verified on
  `peskin-6-2` (eqs 5, 6).
- **`\tensor{R}{^μ_νρσ}`** — polyfilled as `{R{^μ_νρσ}}` which MathJax
  reads as `R^μ_{νρσ}`. Visually identical to standard mixed-index
  tensor notation. Acceptable. 34 uses in `gr-brans-dicke`. No action.
- **`\mathds{1}`** — currently `\mathbb{1}` (different glyph from
  real `\mathds{1}` from `dsfont`). 29 uses in
  `schwartz-second-quantization` / `schwartz-qed-tree`. Cosmetic only;
  most readers will see "𝟙" in either case. Could pre-render but
  probably overkill — flag, defer.
- **`\notag`**, **`\boxed{X}`** — render correctly. No action.
- **Path-integral essay images**: 5 figures with `\includegraphics`
  render correctly; captions render with inline math; alt text strips
  the math (cosmetic, not user-visible).
- **Numbering bug (Bug 2) in batch 2**: also affects
  `gr-brans-dicke` (`1..14, 27, 15, 28, 29, 16..26` — 3 aligns out
  of order) and `psi-correlation-functions-qm` (6 aligns mixed with
  41 equations). Schwartz pages are mostly unaffected because they
  use `align` very rarely (5 across 737 equations).

### Phase 2 batch 2 — verdict

Three structural bugs (6 photon/gluon glyphs, 7 blobs, 9 shaded blocks)
all dissolve into one fix: pre-render TikZ + `tikz-feynman` to SVG via
`lualatex`. One math-rendering bug (8 Wicks) uses the same pipeline.
Two converter bugs (10 equation-row HTML, 12 section labels) are
small. One macro pre-process (11 `\Tr{X}`) is small.

Combined with batch 1, the Phase 3 work splits into:

1. **Converter rewrite — equation numbering**: linear walk in source
   order; `(n.eq)` format; restart `eq` per `<h2>`.
2. **Converter — figure handler**: keep `\begin{figure}` body when no
   `\includegraphics`, route through SVG pipeline. Recover dropped
   captions.
3. **SVG pipeline (new file)**: `build/svg_render.py` (or shell). Cache
   per content hash so we don't re-compile on every build. Inline as
   `<figure class="tikz-figure"><svg …/></figure>` with
   `currentColor`.
4. **Converter — `\Tr{X}` pre-rewrite** in math regions.
5. **Converter — solution-marker normalisation** (from Bug 5).
6. **Converter — `equation-row` block-level marker** (Bug 10).
7. **Converter — section/subsection labels** (Bug 12).
8. **MathJax config** — add `mathtools` package to loader; add
   `Tr` polyfill (or rely on the math pre-rewrite).
9. **CSS** — restyle `aside.solution`, add `aside.boxed-equation`,
   add `aside.theorem` / `aside.definition` / `aside.lemma` /
   `aside.remark` / `aside.note` per `elegantphys.sty`.
10. **Phase-3 cleanup**: delete `tex-served/` (pending your OK).

Each is a small, reviewable commit.

---

## 12. Decisions taken (Apr 27 2026 chat)

1. **`tex-served/`** — keep (unused but doesn't slow anything).
2. **`lualatex` + `dvisvgm`** — installed via Homebrew on Apr 27 2026.

## 13. Verified toolchain (Apr 27 2026)

- `lualatex`: `/opt/homebrew/bin/lualatex` → Homebrew TeXLive 2026
  (LuaHBTeX 1.24.0). 4.6 GB. All polyfill packages bundled
  (`tikz-feynman`, `simpler-wick`, `slashed`, `dsfont`, `mathrsfs`,
  `tensor`, `physics`, `mathtools`, `pgfplots`, `cleveref`, `preview`,
  `standalone`).
- `dvisvgm`: `/opt/homebrew/bin/dvisvgm` 3.6.
- BasicTeX (`/Library/TeX/texbin/`) was also installed but the
  Homebrew TeXLive provides everything; the build script uses the
  Homebrew prefix.

**Required env vars** (the build script will set these automatically;
recorded here for reference). Without them, `dvisvgm` can't locate
`tex.pro` etc. and PostScript-special-using diagrams (blobs, momentum
labels) fail:

```bash
TEXLIVE=/opt/homebrew/Cellar/texlive/20260301
export TEXMFCNF="$TEXLIVE/share/texmf-dist/web2c"
export TEXMF="$TEXLIVE/share/texmf-dist"
export TEXMFDIST="$TEXLIVE/share/texmf-dist"
export TEXMFROOT="$TEXLIVE/share"
```

**Verified outputs** (saved at `/tmp/sample-*.svg`, regenerable):
- `wick.svg` — multi-pair `\wick{\c1 ϕ\c2 ϕ\c1 ϕ\c3 ϕ\c4 ϕ\c2 ϕ\c3 ϕ\c4 ϕ}` with all four overhead contraction arcs distinct. 14 KB, 15 paths.
- `feyn.svg` — `e⁻ → fermion → photon → blob` with wavy photon (zigzag lineTo segments) and hatched blob (`fill='url(#pat0-0)'`). 6.2 KB, 14 paths.
- `loop.svg` — full one-loop self-energy with `half left` arcs and momentum labels. 11 KB, 21 paths.

All three have `--no-fonts` (text rendered as paths) → reproducible
across browsers, no font-license issues, dark-mode safe via a
post-process step that swaps hardcoded `stroke='#000'` / `fill='#000'`
for `currentColor`.

## 14. Phase 3 — Resolution status

All 13 catalogued bugs landed across 7 commits. Each was rebuilt and
spot-checked in the preview server before committing.

| # | Bug (audit ref) | Commit | Status |
|---|---|---|---|
| 1 | `\begin{figure}` with TikZ-only body silently dropped (§7 / §11) | `357506f` | ✅ resolved — 8 figures recovered with captions |
| 2 | Equation numbering out of source order (§7 Bug 2) | `9665b33` | ✅ resolved — linear walk, `(n.eq)` format |
| 3 | Photon = dashed, gluon = dotted via TikZJax (§11 Bug 6) | `d36c775` | ✅ resolved — pre-rendered SVG, real wavy/coil glyphs |
| 4 | `[blob]` markers render as empty nodes (§11 Bug 7) | `d36c775` | ✅ resolved — tikz-feynman blob renders as hatched circle |
| 5 | Wick contractions: pair structure lost, multi-pair shows raw digits (§11 Bug 8) | `6502ed0` | ✅ resolved — pre-rendered SVG matches simpler-wick pdfLaTeX output |
| 6 | `\begin{shaded}` silently stripped (§11 Bug 9) | `d00c5ca` | ✅ resolved — `<aside class="boxed-equation">` per `elegantphys.sty:\boxedeq` |
| 7 | `equation-row` HTML malformation `<p>...</div></p>` (§5c / §11 Bug 10) | `d00c5ca` | ✅ resolved — placeholders inside equation-rows stay inline |
| 8 | `\Tr{X}` drops parens (§11 Bug 11) | `e5bd00c` | ✅ resolved — pre-rewrite to `\operatorname{Tr}\!\left(X\right)`; `\Tr[X]` left as-is |
| 9 | Solution markers inconsistent across pages (§7 Bug 5) | `a622498` | ✅ resolved — normalised to `<aside class="solution">` per `elegantphys.sty` style |
| 10 | `\ref{wick}` to section labels leaks raw key (§11 Bug 12) | — | ⏸️ deferred — minor cosmetic, single occurrence; would need section-numbering scheme to fix properly |
| 11 | `\mathds{1}` glyph differs from real `dsfont` (§11 informational) | — | ⏸️ deferred — MathJax `\mathbb{1}` is acceptable approximation; could pre-render those equations to SVG if you want |
| 12 | `enumerate[label=\roman*.]` drops the label spec (§7) | — | ⏸️ deferred per your decision (§9) — kept as default `<ol>` |
| 13 | `tex-served/` redundant copy (§11) | — | ⏸️ kept per your decision (§12) — doesn't slow anything |

### Final-build stats (Apr 27 2026, post-Phase 3)

- 40 HTML pages built
- 63 inline-SVG diagrams (50 from `\begin{tikzpicture}`/`\feynmandiagram`, 8 from `\begin{figure}` recovery, 5 from path-integral essay images)
- 6 Wick-contraction equations as inline SVG
- 45 boxed-equations (from `\begin{shaded}`)
- 63 styled solution asides
- 0 compile failures (no `tikz-source` source-listing fallbacks used)
- 0 residual TikZJax `<script type="text/tikz">` blocks
- 0 malformed `<p>...</div></p>` HTML
- Cold build: ~68s (62 lualatex+dvisvgm compiles)
- Warm build: ~0.1s (everything cache-hit)
- SVG cache: 884 KB across 62 files

### Remaining items for the user

- **Performance**: cold build is 68s, warm is sub-second. The
  `build/svg-cache/` directory is gitignored — anyone cloning fresh
  needs ~1 minute on first build. CI would too.
- **Deferred items** (Bugs 10, 11, 12 above): all minor cosmetic. Can
  be addressed if/when they bite.
- **CI**: if you want pushes to trigger a fresh build on Vercel /
  GitHub Pages, the runner needs `apt-get install texlive-luatex
  texlive-pictures texlive-science dvisvgm` (or the platform's
  equivalent). Right now `notes/*.html` is checked in so the deployed
  site uses the locally-built artifacts.

---

## 15. Follow-up #3 — Wick & Tensor (Apr 28 2026)

Two issues from a follow-up review, both now resolved.

### Bug 14 — Wick contraction arcs missing (was deferred from Phase 3)

**Failure mode:** SVGs had only the vertical "tick stubs" at each
`\c<n>` mark — the connecting bracket bars never rendered.

**Root cause:** `simpler-wick.sty:169-173` draws the bracket arcs via
`\tikz[remember picture, overlay]` — a *two-pass* mechanism. First
pass writes node coordinates to AUX, second pass uses them to draw
the connecting lines. `build/svg_render.py` ran `lualatex` once.

**Fix (commit `e461854`):** detect two-pass triggers in the snippet
(`\wick`, `remember picture`, `\pageref`, `\ref`) and run lualatex
twice for those. Plain TikZ keeps the cheap single-pass path.

**Verification:** [verification/wick/index.html](verification/wick/index.html)
shows web SVG ↔ pdfLaTeX side-by-side for all 6 Wick equations
(eq 8.40, 8.41, 8.46, 8.47, 8.49, 13.49). User-confirmed match
Apr 28 2026.

### Bug 15 — `\tensor{}{}` indices stacked instead of separated

**Failure mode:** MathJax was rendering `R^μ_{νρσ}` with μ stacked
DIRECTLY above ν (same horizontal column). Real `tensor.sty` puts μ
above-LEFT, νρσ below-RIGHT — distinct columns.

**Root cause:** the page-template polyfill `tensor: ['{#1{#2}}', 2]`
expanded `\tensor{R}{^μ_{νρσ}}` to `{R{^μ_{νρσ}}}`. MathJax stacks
consecutive `^...` and `_...` operators in one column unless an empty
group `{}` separates them.

**Fix (commit `b30e105`):**
[`build/tex_to_html.py:_rewrite_tensor`](build/tex_to_html.py:218)
walks math regions with balanced-brace matching and rewrites every
`\tensor{base}{indices}` to `base + indices` with `{}` inserted
between consecutive script operators. Removed the broken polyfill from
the MathJax config — no runtime macro needed. Source is never edited.

| Source form | Rewritten |
|---|---|
| `\tensor{R}{^\mu_{\nu\rho\sigma}}` | `R^\mu{}_{\nu\rho\sigma}` |
| `\tensor{G}{_\nu^{\beta\rho\sigma}}` | `G_\nu{}^{\beta\rho\sigma}` |
| `\tensor{T}{^{\mu\nu}_{\rho\sigma}}` | `T^{\mu\nu}{}_{\rho\sigma}` |
| `\tensor{R}{_{\mu\nu\rho\sigma}}` (no transition) | `R_{\mu\nu\rho\sigma}` (pass-through) |

Composes correctly with `\bar`, `\hat`, `\tilde` accents.

**Verification:** [verification/tensors/index.html](verification/tensors/index.html)
shows live MathJax ↔ pdfLaTeX for all **42** tensor expressions across
BransDicke.tex (38), 11dsupergravity.tex (2), DTQFTPS1.tex (4). The
audit's earlier count of 26 missed cases with nested braces in the
indices argument — same regex bug as the old polyfill; fixed in the
collection script.

10-case unit test in `_rewrite_tensor` confirms the algorithm handles
mixed-script transitions (`^a_b^c_d`), accent compositions, and
multiple expressions on one line.
