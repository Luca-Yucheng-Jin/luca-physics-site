# Luca Jin — Theoretical Physics Portfolio

A simple editorial homepage for Yucheng (Luca) Jin, paired with a static,
LaTeX-generated library of theoretical-physics notes, research, and reading.

## Homepage development

The homepage uses React, Vite, and TypeScript. The site keeps interaction
deliberately light: a responsive layout, restrained hover states, and a shared
iris transition that connects the homepage to the static library pages.

```bash
npm install
npm run dev       # local Vite server
npm run build     # production build in dist/
npm run preview   # preview the production build
```

The Vite production step copies every existing static HTML route, the generated
`notes/` catalogue, shared assets, and verification files into `dist/`. The
`base: './'` configuration keeps links and assets compatible with subdirectory
deployments such as GitHub Pages.

## LaTeX note workflow

The original note-generation workflow remains independent of the homepage:

```bash
./build.sh           # convert tex/*.tex and rebuild catalogues
./build.sh --serve   # convert, then serve the static source tree on :8000
./build.sh --watch   # rebuild when LaTeX sources change
```

Drop a TeX file in `tex/`, run `./build.sh`, and a corresponding
`notes/<slug>.html` page is regenerated. Run `npm run build` afterwards when
you want a complete deployable `dist/` containing the new homepage.

## Project structure

```text
src/                  React homepage and page-transition component
index.html            Vite application shell
assets/               Shared imagery and legacy scripts
notes/                Generated note pages
tex/                   Original LaTeX sources
build/                 LaTeX-to-HTML and catalogue generators
research.html          Existing research document
notes.html             Existing note catalogue
reading.html           Existing reading tracker
styles.css             Shared stylesheet for legacy pages
vite.config.ts         Homepage build and legacy-route preservation
```

The generated note pages continue to load MathJax and TikZJax as before. The
new homepage does not modify their markup, styling, or scripts.
