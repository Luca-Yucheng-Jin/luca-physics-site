import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';


const root = path.resolve('.');
const clientRoot = path.join(root, 'dist', 'client');
const privateSlugs = [
  'path-integral',
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


test('private note sources are absent from the public repository surface', async () => {
  for (const relative of [
    'audit.md',
    'tex/QFTschwartz.tex',
    'tex-served/QFTschwartz.tex',
    'tex/quantumEssay.tex',
    'tex-served/quantumEssay.tex',
    'verification/build_wick.py',
    'verification/wick/index.html',
    ...Array.from({ length: 5 }, (_, index) => `assets/path-integral-fig${index + 1}${[
      '-spacetime.png', '-slits.png', '-paths.png', '-wick.png', '-cylinder.png',
    ][index]}`),
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
    /QFTschwartz|quantumEssay|de-greens-function|de-images-laplace|tdsp-adiabatic-water|schwartz-(?:classical|second|spin|qed|path)/i,
  );
});
