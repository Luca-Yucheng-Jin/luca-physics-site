import assert from 'node:assert/strict';
import { execFile as execFileCallback } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import test from 'node:test';


const execFile = promisify(execFileCallback);
const root = path.resolve('.');


function attribute(attrs, name) {
  return attrs.match(new RegExp(`(?:^|\\s)${name}="([^"]+)"`))?.[1];
}


function structuralHeadings(html) {
  return [...html.matchAll(/<h([234])(\s[^>]*)?>([\s\S]*?)<\/h\1>/g)]
    .filter((match) => match[2]?.includes('data-section-heading'))
    .map((match) => ({
      level: Number(match[1]),
      attrs: match[2],
      id: attribute(match[2], 'id'),
      number: attribute(match[2], 'data-section-number'),
      visibleNumber: match[3].match(/<span class="note__heading-number">([^<]+)<\/span>/)?.[1],
      title: match[3].match(/<span class="note__heading-title">([\s\S]*?)<\/span>/)?.[1],
      unnumbered: match[2].includes('data-section-unnumbered'),
    }));
}


function tocEntries(html) {
  return [...html.matchAll(
    /<li class="toc-h([234])"><a href="#([^"]+)"><span class="note__toc-number">([^<]+)<\/span>\s*<span class="note__toc-title">([\s\S]*?)<\/span><\/a><\/li>/g,
  )].map((match) => ({
    level: Number(match[1]),
    id: match[2],
    number: match[3],
    title: match[4],
  }));
}


function expectedNumberedHeadings(headings) {
  const counters = { 2: 0, 3: 0, 4: 0 };
  const expected = [];
  for (const heading of headings) {
    if (heading.unnumbered) continue;
    counters[heading.level] += 1;
    for (let deeper = heading.level + 1; deeper <= 4; deeper += 1) counters[deeper] = 0;
    expected.push({
      level: heading.level,
      id: heading.id,
      number: Array.from(
        { length: heading.level - 1 },
        (_, index) => counters[index + 2],
      ).join('.'),
      title: heading.title,
    });
  }
  return expected;
}


test('section builder reproduces LaTeX 1, 1.1, and 1.1.1 numbering', async () => {
  const python = String.raw`
import json
from build.tex_to_html import build_toc_and_inject_ids

body = '''
<h2 data-section-heading data-section-unnumbered>Abstract</h2>
<h2 data-section-heading>Alpha</h2>
<h3 data-section-heading>Beta</h3>
<h4 data-section-heading>Gamma</h4>
<h3 data-section-heading>Delta</h3>
<h4 data-section-heading>Epsilon</h4>
<h2 data-section-heading>Omega</h2>
<h3 data-section-heading>Zeta</h3>
<h4 data-section-heading>Eta</h4>
'''
rendered, toc = build_toc_and_inject_ids(body)
print(json.dumps({'body': rendered, 'toc': toc}))
`;
  const { stdout } = await execFile('python3', ['-c', python], { cwd: root });
  const rendered = JSON.parse(stdout);
  const headings = structuralHeadings(rendered.body);
  const numbered = headings.filter((heading) => !heading.unnumbered);

  assert.deepEqual(numbered.map((heading) => heading.number), [
    '1', '1.1', '1.1.1', '1.2', '1.2.1', '2', '2.1', '2.1.1',
  ]);
  assert.deepEqual(numbered.map((heading) => heading.visibleNumber), numbered.map((heading) => heading.number));
  assert.equal(headings[0].number, undefined);
  assert.equal(headings[0].visibleNumber, undefined);
  assert.doesNotMatch(rendered.toc, /Abstract/);
  assert.match(rendered.toc, /<div class="note__toc-label">Contents<\/div>/);
  assert.deepEqual(tocEntries(rendered.toc), expectedNumberedHeadings(headings));
});


test('starred LaTeX sections stay outside Contents and do not advance equations', async () => {
  const python = String.raw`
import contextlib
import io
import json
import pathlib
import tempfile
import build.tex_to_html as converter

source = r'''
\begin{document}
\section{Alpha}
\begin{equation} a = 1 \end{equation}
\section*{Bridge}
\begin{equation} b = 2 \end{equation}
\section{Omega}
\begin{equation} c = 3 \end{equation}
\end{document}
'''
with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    tex_path = root / 'numbering.tex'
    tex_path.write_text(source)
    converter.OUT = str(root)
    with contextlib.redirect_stdout(io.StringIO()):
        converter.write_whole_file_page(
            str(tex_path),
            'numbering',
            'Numbering',
            'Synthetic numbering check',
            'Synthetic numbering check.',
        )
    print(json.dumps({'html': (root / 'numbering.html').read_text()}))
`;
  const { stdout } = await execFile('python3', ['-c', python], { cwd: root });
  const { html } = JSON.parse(stdout);
  const headings = structuralHeadings(html);

  assert.deepEqual(headings.map((heading) => heading.number), ['1', undefined, '2']);
  assert.deepEqual(tocEntries(html).map((entry) => entry.title), ['Alpha', 'Omega']);
  assert.doesNotMatch(html.match(/<nav class="note__toc[\s\S]*?<\/nav>/)?.[0] || '', /Bridge/);
  assert.deepEqual([...html.matchAll(/\\tag\{([^}]+)\}/g)].map((match) => match[1]), [
    '1.1', '1.2', '2.1',
  ]);
});


test('every generated public note keeps heading and Contents labels in sync', async () => {
  const manifest = JSON.parse(
    await readFile(path.join(root, 'assets', 'nav-manifest.json'), 'utf8'),
  );
  const publicHrefs = manifest.categories.flatMap((category) =>
    category.groups.flatMap((group) => group.notes.map((note) => note.href)),
  );

  let checked = 0;
  for (const relative of publicHrefs) {
    const page = await readFile(path.join(root, relative), 'utf8');
    const article = page.match(/<article class="note__body">([\s\S]*?)<\/article>/)?.[1];
    assert.ok(article, `${relative}: missing note body`);
    const headings = structuralHeadings(article);
    if (!headings.length) continue;
    checked += 1;

    const expected = expectedNumberedHeadings(headings);
    for (const heading of headings) {
      if (heading.unnumbered) {
        assert.equal(heading.number, undefined, `${relative}: starred heading was numbered`);
        assert.equal(heading.visibleNumber, undefined, `${relative}: starred heading shows a number`);
        continue;
      }
      assert.ok(heading.id, `${relative}: numbered heading lacks an anchor`);
      assert.ok(heading.title, `${relative}: numbered heading lacks title markup`);
      assert.equal(heading.visibleNumber, heading.number, `${relative}: heading number is not visible text`);
    }

    const actualToc = tocEntries(page);
    if (expected.length >= 2) {
      assert.match(page, /<div class="note__toc-label">Contents<\/div>/, `${relative}: missing Contents label`);
      assert.deepEqual(actualToc, expected, `${relative}: Contents does not match article headings`);
    } else {
      assert.deepEqual(actualToc, [], `${relative}: single-heading note should not have a redundant Contents list`);
    }
  }

  assert.ok(checked >= 1, 'no generated public note contained a structural heading');
});
