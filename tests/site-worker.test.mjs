import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import worker from '../worker/index.js';

const clientRoot = path.resolve('dist/client');

const contentTypes = {
  '.css': 'text/css',
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.pdf': 'application/pdf',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain',
  '.xml': 'application/xml',
};

const env = {
  ASSETS: {
    async fetch(request) {
      const url = new URL(request.url);
      const relative = decodeURIComponent(url.pathname).replace(/^\/+/, '');
      if (!relative || relative.includes('..')) return new Response('Not found', { status: 404 });

      try {
        const body = await readFile(path.join(clientRoot, relative));
        return new Response(body, {
          status: 200,
          headers: { 'content-type': contentTypes[path.extname(relative)] || 'application/octet-stream' },
        });
      } catch {
        return new Response('Not found', { status: 404 });
      }
    },
  },
};

test('serves the homepage for /', async () => {
  const response = await worker.fetch(new Request('https://example.test/'), env);
  assert.equal(response.status, 200);
  assert.match(await response.text(), /Yucheng \(Luca\) Jin/);
});

test('serves static html routes directly', async () => {
  const response = await worker.fetch(new Request('https://example.test/notes.html'), env);
  assert.equal(response.status, 200);
  assert.match(await response.text(), /<h1>Notes<\/h1>/);
});

test('redirects duplicate html routes to their canonical URLs', async () => {
  const routes = [
    ['/index.html', '/'],
    ['/notes', '/notes.html'],
    ['/notes/osborn-aqft-ps3', '/notes/osborn-aqft-ps3.html'],
  ];
  for (const [route, canonical] of routes) {
    const response = await worker.fetch(new Request(`https://example.test${route}`), env);
    assert.equal(response.status, 308);
    assert.equal(response.headers.get('location'), `https://example.test${canonical}`);
  }
});

test('keeps missing assets as 404', async () => {
  const response = await worker.fetch(new Request('https://example.test/assets/missing.css'), env);
  assert.equal(response.status, 404);
});

test('keeps unknown extensionless routes as 404', async () => {
  const response = await worker.fetch(new Request('https://example.test/not-a-page'), env);
  assert.equal(response.status, 404);
});

test('serves crawler directives', async () => {
  const robots = await worker.fetch(new Request('https://example.test/robots.txt'), env);
  assert.equal(robots.status, 200);
  assert.match(await robots.text(), /Sitemap: https:\/\/luca-physics-observatory\.jinluca3\.chatgpt\.site\/sitemap\.xml/);

  const sitemap = await worker.fetch(new Request('https://example.test/sitemap.xml'), env);
  assert.equal(sitemap.status, 200);
  assert.match(await sitemap.text(), /<urlset/);
});

test('points PDF search signals to the corresponding HTML note', async () => {
  const response = await worker.fetch(
    new Request('https://example.test/output/pdf/osborn-aqft-ps3.pdf'),
    env,
  );
  assert.equal(response.status, 200);
  assert.equal(
    response.headers.get('link'),
    '<https://example.test/notes/osborn-aqft-ps3.html>; rel="canonical"',
  );
});

test('redirects the retired reading-list routes to the notes archive', async () => {
  for (const route of ['/reading', '/reading.html']) {
    const response = await worker.fetch(new Request(`https://example.test${route}`), env);
    assert.equal(response.status, 308);
    assert.equal(response.headers.get('location'), 'https://example.test/notes.html');
  }
});

test('redirects retired research routes to the homepage', async () => {
  const routes = [
    '/research',
    '/research.html',
    '/research/',
    '/research/perovskite-devices',
    '/research/perovskite-devices.html',
    '/research/higgs-validation.html',
    '/research/kelvin-water-dropper.html',
    '/output/pdf/research-perovskite-devices.pdf',
    '/output/pdf/research-higgs-validation.pdf',
    '/output/pdf/research-kelvin-water-dropper.pdf',
  ];

  for (const route of routes) {
    const response = await worker.fetch(new Request(`https://example.test${route}`), env);
    assert.equal(response.status, 308);
    assert.equal(response.headers.get('location'), 'https://example.test/');
  }
});
