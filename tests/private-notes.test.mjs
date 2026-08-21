import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';


const root = path.resolve('.');
const clientRoot = path.join(root, 'dist', 'client');
const privateSlugs = [
  'de-greens-function',
  'de-images-laplace',
  'tdsp-adiabatic-water',
  'schwartz-classical-field',
  'schwartz-second-quantization',
  'schwartz-spin-1',
  'schwartz-spinors',
  'schwartz-qed-tree',
  'schwartz-path-integrals',
];


async function assertMissing(relative) {
  await assert.rejects(
    stat(path.join(root, relative)),
    (error) => error?.code === 'ENOENT',
    `private route input is still present: ${relative}`,
  );
}


test('private Imperial and Schwartz notes are absent from every public index', async () => {
  const manifest = JSON.parse(
    await readFile(path.join(root, 'assets', 'nav-manifest.json'), 'utf8'),
  );
  const publicHrefs = manifest.categories.flatMap((category) =>
    category.groups.flatMap((group) => group.notes.map((note) => note.href)),
  );
  assert.equal(new Set(publicHrefs).size, publicHrefs.length, 'public manifest has duplicate note routes');

  const rootPages = (await readdir(root))
    .filter((name) => name === 'notes.html' || /^notes-[^.]+\.html$/.test(name))
    .sort();
  const publicIndexes = [
    ...rootPages,
    'assets/nav-manifest.json',
    'sitemap.xml',
  ];
  const indexedText = (await Promise.all(
    publicIndexes.map(async (relative) => [relative, await readFile(path.join(root, relative), 'utf8')]),
  ));

  for (const slug of privateSlugs) {
    assert.ok(!publicHrefs.includes(`notes/${slug}.html`), `${slug} remains in the public manifest`);
    for (const [relative, contents] of indexedText) {
      for (const route of [`notes/${slug}.html`, `output/pdf/${slug}.pdf`]) {
        assert.ok(!contents.includes(route), `${relative} still exposes private route ${route}`);
      }
    }
  }

  const qftIndexes = indexedText
    .filter(([relative]) => relative === 'notes.html'
      || relative === 'notes-qft.html'
      || relative === 'assets/nav-manifest.json')
    .map(([, contents]) => contents)
    .join('\n');
  assert.doesNotMatch(qftIndexes, /Matthew D\. Schwartz|Schwartz chapter notes/i);
});


test('private notes have no direct HTML or PDF route in source or deployment', async () => {
  for (const slug of privateSlugs) {
    for (const relative of [
      path.join('notes', `${slug}.html`),
      path.join('output', 'pdf', `${slug}.pdf`),
      path.join('dist', 'client', 'notes', `${slug}.html`),
      path.join('dist', 'client', 'output', 'pdf', `${slug}.pdf`),
    ]) {
      await assertMissing(relative);
    }
  }

  await assert.doesNotReject(stat(clientRoot), 'production artifact must exist before privacy checks');
});


test('completed Schwartz solutions are collected into one public file per chapter', async () => {
  const completed = ['29.1', '29.2', '29.3', '29.6', '29.7', '29.8', '29.9'];
  const chapterSlug = 'schwartz-qft-chapter-29';
  const manifest = JSON.parse(
    await readFile(path.join(root, 'assets', 'nav-manifest.json'), 'utf8'),
  );
  const importManifest = JSON.parse(
    await readFile(path.join(root, 'assets', 'schwartz-qft-manifest.json'), 'utf8'),
  );
  const publicHrefs = manifest.categories.flatMap((category) =>
    category.groups.flatMap((group) => group.notes.map((note) => note.href)),
  );

  assert.equal(importManifest.chapters.length, 1);
  assert.equal(importManifest.chapters[0].chapter, '29');
  assert.equal(importManifest.chapters[0].title, 'Weak interactions');
  assert.equal(importManifest.chapters[0].slug, chapterSlug);
  assert.deepEqual(
    importManifest.chapters[0].completedProblems.map((problem) => problem.problem),
    completed,
  );
  assert.match(importManifest.sourceCommit, /^[0-9a-f]{40}$/);

  assert.ok(publicHrefs.includes(`notes/${chapterSlug}.html`), 'Chapter 29 is not indexed');
  for (const relative of [
    `notes/${chapterSlug}.html`,
    `output/pdf/${chapterSlug}.pdf`,
    `tex/${chapterSlug}.tex`,
    `dist/client/notes/${chapterSlug}.html`,
    `dist/client/output/pdf/${chapterSlug}.pdf`,
  ]) {
    await assert.doesNotReject(stat(path.join(root, relative)), `missing ${relative}`);
  }

  const html = await readFile(path.join(root, 'notes', `${chapterSlug}.html`), 'utf8');
  for (const problem of completed) {
    assert.match(html, new RegExp(`Problem ${problem.replace('.', '\\.')}`));
  }
  assert.doesNotMatch(
    html,
    /Problem 29\.[45]|solutionplaceholder|solution to be written|compile failed|\\begin\{(?:tikzpicture|feynman)\}/i,
    'Chapter 29 exposes unfinished or unrendered source',
  );

  for (const problem of ['1', '2', '3', '4', '5', '6', '7', '8', '9']) {
    const oldSlug = `schwartz-qft-29-${problem}`;
    assert.ok(!publicHrefs.includes(`notes/${oldSlug}.html`), `${oldSlug} should be retired`);
    for (const relative of [
      `notes/${oldSlug}.html`,
      `output/pdf/${oldSlug}.pdf`,
      `dist/client/notes/${oldSlug}.html`,
      `dist/client/output/pdf/${oldSlug}.pdf`,
    ]) {
      await assertMissing(relative);
    }
  }

  const importedSource = await readFile(
    path.join(root, 'tex', `${chapterSlug}.tex`),
    'utf8',
  );
  assert.doesNotMatch(importedSource, /solutionplaceholder|solution to be written|\bTODO\b|\bTBD\b/i);
});


test('the path-integral essay remains public with its source, figures, HTML, and PDF', async () => {
  const manifest = JSON.parse(
    await readFile(path.join(root, 'assets', 'nav-manifest.json'), 'utf8'),
  );
  const publicHrefs = manifest.categories.flatMap((category) =>
    category.groups.flatMap((group) => group.notes.map((note) => note.href)),
  );
  assert.ok(publicHrefs.includes('notes/path-integral.html'), 'essay is missing from public navigation');

  const publicIndexes = await Promise.all([
    'notes.html',
    'notes-qft.html',
    'assets/nav-manifest.json',
    'sitemap.xml',
  ].map((relative) => readFile(path.join(root, relative), 'utf8')));
  for (const contents of publicIndexes) {
    assert.match(contents, /notes\/path-integral\.html/, 'essay is missing from a public index');
  }
  assert.match(publicIndexes[0], /output\/pdf\/path-integral\.pdf/);
  assert.match(publicIndexes[1], /output\/pdf\/path-integral\.pdf/);

  for (const relative of [
    'notes/path-integral.html',
    'output/pdf/path-integral.pdf',
    'tex/path-integral.tex',
    'dist/client/notes/path-integral.html',
    'dist/client/output/pdf/path-integral.pdf',
    ...Array.from({ length: 5 }, (_, index) => `assets/path-integral-fig${index + 1}${[
      '-spacetime.png', '-slits.png', '-paths.png', '-wick.png', '-cylinder.png',
    ][index]}`),
    ...Array.from({ length: 5 }, (_, index) => `dist/client/assets/path-integral-fig${index + 1}${[
      '-spacetime.png', '-slits.png', '-paths.png', '-wick.png', '-cylinder.png',
    ][index]}`),
  ]) {
    await assert.doesNotReject(stat(path.join(root, relative)), `missing public essay asset: ${relative}`);
  }

  await assertMissing('tex/quantumEssay.tex');
  await assertMissing('tex-served/quantumEssay.tex');

  const source = await readFile(path.join(root, 'tex', 'path-integral.tex'), 'utf8');
  const html = await readFile(path.join(root, 'notes', 'path-integral.html'), 'utf8');
  const citedKeys = new Set(
    [...source.matchAll(/\\cite\*?\{([^}]+)\}/g)]
      .flatMap((match) => match[1].split(',').map((key) => key.trim())),
  );
  const bibliographyKeys = [...source.matchAll(/\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}/g)]
    .map((match) => match[1]);
  assert.deepEqual([...citedKeys].sort(), [...bibliographyKeys].sort());
  assert.deepEqual(bibliographyKeys, [
    'Feynman1948', 'Sakurai', 'TongQM', 'Peskin', 'Schwartz', 'Kibble',
  ]);
  for (const key of citedKeys) {
    assert.match(html, new RegExp(`href="#ref-${key}"`), `citation ${key} is not linked`);
  }
  assert.doesNotMatch(
    `${source}\n${html}`,
    /02556257|StudentCID|Research\s*&\s*Writing Methods|Generative AI was used/i,
    'sanitized public essay exposes private assessment metadata',
  );
  assert.match(html, /data-section-number="A"/);
  assert.match(html, /\\tag\{A\.1\}/);
  assert.match(html, /\\tag\{A\.6\}/);
  assert.doesNotMatch(html, /\\appendix|Section (?:LC|Sec:Bra-ket|HS)|Appendix wick/);
  assert.equal((html.match(/class="note__figure-number">Figure \d+\.<\/span>/g) || []).length, 5);
  assert.equal((html.match(/<li id="ref-[^"]+"/g) || []).length, 6);
  assert.match(html, /<section class="note__references" aria-labelledby="references">/);
  assert.doesNotMatch(html.match(/<nav class="note__toc[\s\S]*?<\/nav>/)?.[0] || '', /References/);
  assert.doesNotMatch(html, /\\cite|\\bibitem|\\begin\{thebibliography\}/);
  assert.doesNotMatch(html, /e\^{-S_E\[[^\]]+\]\}\\oint|},,/);
});


test('private note sources are absent from the public repository surface', async () => {
  for (const relative of [
    'audit.md',
    'tex/QFTschwartz.tex',
    'tex-served/QFTschwartz.tex',
    'verification/build_wick.py',
    'verification/wick/index.html',
  ]) {
    await assertMissing(relative);
  }

  const publicSources = await Promise.all([
    'build/build_indexes.py',
    'build/tex_to_html.py',
    'tex/DE.tex',
    'tex-served/DE.tex',
    'tex/TDSP.tex',
    'tex-served/TDSP.tex',
  ].map((relative) => readFile(path.join(root, relative), 'utf8')));
  assert.doesNotMatch(
    publicSources.join('\n'),
    /QFTschwartz|de-greens-function|de-images-laplace|tdsp-adiabatic-water|schwartz-(?:classical|second|spin|qed|path)/i,
  );
});
