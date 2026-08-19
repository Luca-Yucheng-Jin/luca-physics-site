import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';


const root = path.resolve('.');
const siteUrl = 'https://luca-yucheng-jin.github.io/luca-physics-site';


async function publicHtmlFiles() {
  const rootEntries = await readdir(root);
  const rootPages = rootEntries
    .filter((name) => name === 'index.html' || name === 'notes.html' || /^notes-[^.]+\.html$/.test(name))
    .sort();
  const notePages = (await readdir(path.join(root, 'notes')))
    .filter((name) => name.endsWith('.html'))
    .sort()
    .map((name) => path.join('notes', name));
  return [...rootPages, ...notePages];
}


function expectedCanonical(relative) {
  return relative === 'index.html' ? `${siteUrl}/` : `${siteUrl}/${relative}`;
}


test('every public HTML page has unique indexable search metadata', async () => {
  const files = await publicHtmlFiles();
  assert.equal(files.length, 57);
  const canonicals = new Set();

  for (const relative of files) {
    const html = await readFile(path.join(root, relative), 'utf8');
    const title = html.match(/<title>(.*?)<\/title>/s)?.[1];
    const description = html.match(/<meta name="description" content="([^"]+)">?\/?/s)?.[1];
    const canonical = html.match(/<link rel="canonical" href="([^"]+)">?\/?/s)?.[1];
    const schemaText = html.match(/<script type="application\/ld\+json">\s*([\s\S]*?)\s*<\/script>/)?.[1];

    assert.ok(title?.includes('Yucheng (Luca) Jin'), `${relative}: missing descriptive author title`);
    assert.ok(description && description.length >= 70, `${relative}: missing useful description`);
    assert.doesNotMatch(title, /\$|\\(?:frac|text|mathrm)\b/, `${relative}: raw LaTeX in title`);
    assert.doesNotMatch(description, /\$|\\(?:frac|text|mathrm)\b/, `${relative}: raw LaTeX in description`);
    assert.equal(canonical, expectedCanonical(relative), `${relative}: wrong canonical`);
    assert.match(html, /<meta name="robots" content="index, follow,/);
    assert.ok(schemaText, `${relative}: missing JSON-LD`);
    let schema;
    assert.doesNotThrow(() => { schema = JSON.parse(schemaText); }, `${relative}: invalid JSON-LD`);
    const types = (schema['@graph'] || [schema]).map((entry) => entry['@type']);
    if (relative === 'index.html') {
      for (const type of ['WebSite', 'ProfilePage', 'Person']) assert.ok(types.includes(type));
    } else if (relative.startsWith('notes/')) {
      for (const type of ['Article', 'BreadcrumbList']) assert.ok(types.includes(type));
    } else {
      assert.ok(types.includes('CollectionPage'));
    }
    assert.ok(!canonicals.has(canonical), `${relative}: duplicate canonical ${canonical}`);
    canonicals.add(canonical);
  }
});


test('sitemap contains every and only canonical public HTML page', async () => {
  const files = await publicHtmlFiles();
  const expected = files.map(expectedCanonical).sort();
  const xml = await readFile(path.join(root, 'sitemap.xml'), 'utf8');
  const actual = [...xml.matchAll(/<loc>(.*?)<\/loc>/g)].map((match) => match[1]).sort();
  assert.deepEqual(actual, expected);
});


test('robots.txt allows crawling and advertises the canonical sitemap', async () => {
  const robots = await readFile(path.join(root, 'robots.txt'), 'utf8');
  assert.match(robots, /^User-agent: \*$/m);
  assert.match(robots, /^Allow: \/$/m);
  assert.match(robots, new RegExp(`^Sitemap: ${siteUrl.replaceAll('.', '\\.')}/sitemap\\.xml$`, 'm'));
  assert.doesNotMatch(robots, /Disallow:/);
});


test('homepage exposes the name and subject links before JavaScript runs', async () => {
  const html = await readFile(path.join(root, 'index.html'), 'utf8');
  assert.match(html, /<h1>I’m Yucheng <em>\(Luca\) Jin\.<\/em><\/h1>/);
  for (const route of [
    'notes-qft.html',
    'notes-advanced.html',
    'notes-qm.html',
    'notes-ed.html',
    'notes-mm.html',
    'notes-de.html',
    'notes-tdsp.html',
  ]) {
    assert.match(html, new RegExp(`href="${route.replace('.', '\\.')}"`));
  }
});


test('notes overview keeps only the useful archive statistics', async () => {
  const html = await readFile(path.join(root, 'notes.html'), 'utf8');
  const stats = html.match(/<ul class="stats"[\s\S]*?<\/ul>/)?.[0];
  assert.ok(stats, 'notes.html: missing archive statistics');
  assert.equal((stats.match(/<li>/g) || []).length, 2);
  assert.doesNotMatch(stats, /formats per note/i);
  assert.doesNotMatch(
    html,
    /Study notes and coursework write-ups|Unofficial personal notes|Do not submit this work/i,
  );
});


test('every crawlable internal link resolves to a real file', async () => {
  const files = await publicHtmlFiles();
  for (const relative of files) {
    const html = await readFile(path.join(root, relative), 'utf8');
    const hrefs = [...html.matchAll(/href="([^"]+)"/g)].map((match) => match[1]);
    for (const href of hrefs) {
      if (/^(?:https?:|mailto:|#)/.test(href)) continue;
      const clean = decodeURIComponent(href.split(/[?#]/)[0]);
      let target = clean.startsWith('/')
        ? path.join(root, clean.slice(1))
        : path.resolve(root, path.dirname(relative), clean);
      let info;
      try {
        info = await stat(target);
      } catch {
        assert.fail(`${relative}: broken internal link ${href}`);
      }
      if (info.isDirectory()) target = path.join(target, 'index.html');
      await assert.doesNotReject(stat(target), `${relative}: broken internal link ${href}`);
    }
  }
});
