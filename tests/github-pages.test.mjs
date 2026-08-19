import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';


const clientRoot = path.resolve('dist/client');


test('GitHub Pages receives the compiled homepage rather than the source entry', async () => {
  const html = await readFile(path.join(clientRoot, 'index.html'), 'utf8');

  assert.doesNotMatch(html, /\/src\/main\.tsx/);

  const script = html.match(/<script type="module"[^>]* src="([^"]+)"/i)?.[1];
  const stylesheet = html.match(/<link rel="stylesheet"[^>]* href="([^"]+)"/i)?.[1];
  assert.ok(script, 'compiled homepage is missing its JavaScript bundle');
  assert.ok(stylesheet, 'compiled homepage is missing its stylesheet bundle');

  for (const asset of [script, stylesheet]) {
    assert.match(asset, /^\.\/assets\//);
    await assert.doesNotReject(
      stat(path.join(clientRoot, asset.replace(/^\.\//, ''))),
      `compiled asset does not exist: ${asset}`,
    );
  }
});


test('GitHub Pages artifact retains the notes and PDF editions', async () => {
  for (const relative of [
    'notes.html',
    'notes/osborn-aqft-ps3.html',
    'output/pdf/osborn-aqft-ps3.pdf',
    'robots.txt',
    'sitemap.xml',
  ]) {
    await assert.doesNotReject(stat(path.join(clientRoot, relative)), `missing ${relative}`);
  }
});
