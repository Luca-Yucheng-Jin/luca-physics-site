# Luca Jin — Personal Physics Site

A scholarly editorial-style static site for theoretical-physics notes,
solved problems, and a CV-style about page.

Built as a draft scaffold to be continued in Claude Code.

---

## Folder layout

```
luca-physics-site/
├── index.html             # Home / about (built from your CV)
├── notes.html             # Index of all physics notes
├── research.html          # Research projects
├── styles.css             # The single source of design truth
├── notes/
│   └── peskin-6-2.html    # Worked example — Peskin Problem 6.2 (template)
├── tex/                   # Original LaTeX source files (read-only reference)
│   ├── main__1_.tex       # Peskin solutions
│   ├── DE.tex
│   ├── ED.tex
│   ├── MM.tex
│   ├── QM.tex
│   └── TDSP.tex
├── assets/                # Empty — for any images / PDFs you want to add later
└── README.md              # This file
```

## Design system (in `styles.css`)

The CSS variables at the top of the file define everything visual.
Change them once and the whole site updates.

- **Palette:** warm paper `#f7f2e7`, deep ink `#1a1612`, oxblood accent `#6b1f1f`,
  old-gold highlight `#c69b3d`. Subtle paper grain via two radial gradients on `body`.
- **Typography:** Cormorant Garamond (display, italic for hero), EB Garamond (body),
  JetBrains Mono (code). All from Google Fonts, no build step required.
- **Layout:** single column, max-width `68ch`, generous gutter that scales with viewport.
  `§` glyph in front of every `<h2>` as a scholarly marker.

## How to view it

This is plain static HTML — no build tools.

```bash
# from the project root
python3 -m http.server 8000
# then open http://localhost:8000
```

(or `npx serve`, or just open `index.html` in a browser — though MathJax wants
a real http origin to render reliably).

## Deployment

This site is deploy-ready as-is. Drop the folder onto:
- **GitHub Pages** — push to a repo, enable Pages on `main`.
- **Vercel / Netlify** — drag-and-drop the folder, done.
- **Cloudflare Pages** — same.

No backend, no build, no env vars.

---

## How math rendering works

The notes pages load **MathJax 3** from a CDN. You write LaTeX exactly the way
you do in your `.tex` files:

```html
<p>The Lagrangian is \[ \mathcal{L} = -\tfrac{1}{4} F_{\mu\nu} F^{\mu\nu} \] etc.</p>
```

Inline math: `$...$` or `\(...\)`. Display: `$$...$$` or `\[...\]`.
The `physics`, `boldsymbol`, and `cancel` packages are pre-loaded for things
like `\bra{\psi}`, `\boldsymbol{p}`, and `\cancel{...}` — you'll need these for
Peskin and Tong notes.

## Converting your `.tex` files into note pages

Three reasonable options, in order of effort:

1. **Manual paste (fastest, recommended for the first 1–2 pages).**
   Copy the relevant `\section{}` / `\subsection{}` block from `tex/*.tex` into
   a new `notes/<slug>.html` modelled on `notes/peskin-6-2.html`. Strip
   `\begin{equation}...\end{equation}` to `\[...\]` and the rest is mostly
   copy-paste — MathJax handles `boxed`, `aligned`, `pmatrix`, etc.

2. **Pandoc (one-shot, decent quality).**
   ```bash
   pandoc -f latex -t html --mathjax tex/QM.tex -o notes/qm.html
   ```
   Then wrap the body in your nav/footer template. Pandoc handles environments
   well but macros like `\Cdot` need defining. Add a `--lua-filter` if you want
   to be precise.

3. **Build a tiny generator (worth it if you have ≥ 5 notes).**
   A ~50-line Python script reading each `\subsection{...}` block from
   `main__1_.tex`, slugifying the title, and writing a templated HTML file.
   Probably what to do in Claude Code.

## What I'd do next in Claude Code

Pasted in priority order:

1. **Convert the rest of `main__1_.tex` (Peskin solutions) into individual pages.**
   One page per `\subsection{}`. Use `notes/peskin-6-2.html` as the template.
   Update `notes.html` catalogue entries to point at them.

2. **Convert `QM.tex`, `ED.tex`, `MM.tex`, `DE.tex`, `TDSP.tex`** the same way.
   Each `.tex` is one section, so it can be one or two HTML pages each.

3. **Add a `/cv.html`** mirroring the resume (or just link the PDF in the topbar).

4. **Add a tags / search overlay** on `notes.html`. Vanilla JS, ~30 lines.
   Filter on the `data-tags` attribute you'll add to each `<li class="catalogue__item">`.

5. **Add a "Last updated" date** on each note page, generated from `git log -1 --format=%cs`
   at build time, or just a `<time>` element you set by hand.

6. **(Optional)** A dark-mode toggle. Cleanest path: a `data-theme="dark"` on
   `<html>`, a second `:root[data-theme="dark"] { ... }` block in `styles.css`,
   and a 10-line JS toggle in the topbar. Keep the paper theme as default —
   it's the whole point of the design.

7. **(Optional)** OpenGraph / Twitter meta tags + a favicon. There's a
   placeholder Feynman-vertex SVG in `index.html` you could refine into a favicon.

## Things I deliberately didn't do

- No JS framework, no bundler. The site is ~5 files. Keep it that way.
- No client-side router. Each page is a real `.html`. This makes "view source"
  a useful learning tool for anyone reading.
- No CSS framework (Tailwind / Bootstrap). The CSS variables system is the
  whole design token layer; that's all you need.
- No tracking / analytics. Add Plausible or GoatCounter if you ever care.

---

— Drafted 26 April 2026
