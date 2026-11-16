# Luca Jin — Theoretical Physics Portfolio

A personal web of some notes and solutions to problems in theoretical physics.

## Homepage development

The homepage uses React, Vite, and TypeScript. The site keeps interaction
deliberately light: a responsive layout, restrained hover states, and direct
HTML/PDF access to each published note.

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

## Blog entries

The Blog is a chronological home for informal thoughts, questions, or short
observations. Entries are plain text; there are no required subjects or headings.

1. Copy `content/blog/_template.json` to `content/blog/your-entry-title.json`.
2. Set the title, date (`YYYY-MM-DD`), short summary, and paragraphs. Each string
   in `paragraphs` becomes one paragraph. Use `\n` for a line break within one.
3. Keep `"draft": true` while writing. Set it to `false` to publish the entry.
4. Run `npm run dev` to preview, or `npm run build` to prepare the site for deployment.

Entries appear newest first at `blog.html`, with their own permanent pages at
`blog/your-entry-title.html`. Maths uses the same MathJax notation as the notes:
`$...$` or `$$...$$`. In JSON strings, write a LaTeX backslash as `\\` and a
quotation mark as `\"`. Text is escaped, so HTML is displayed as text.

For footnotes, add a `footnotes` array of text strings and reference each note
once in the paragraphs with `[^1]`, `[^2]`, etc. Footnotes can include maths.

Draft source files are never included in the production build. Changing an entry
back to a draft removes its generated public page at the next build. Edit the
source JSON files rather than the generated HTML. Refresh the dev server after
running `npm run refresh` when you change entries during a preview session.

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
src/                  React homepage
index.html            Vite application shell
assets/               Shared imagery and legacy scripts
notes/                Generated note pages
tex/                   Original LaTeX sources
build/                 LaTeX-to-HTML and catalogue generators
notes.html             Complete notes archive
output/pdf/            Printable editions of published notes
styles.css             Shared stylesheet for archive pages
vite.config.ts         Homepage build and legacy-route preservation
```

The generated note pages continue to load MathJax and TikZJax as before. The
new homepage does not modify their markup, styling, or scripts.
