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
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
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

test('supports extensionless html routes', async () => {
  const response = await worker.fetch(new Request('https://example.test/research'), env);
  assert.equal(response.status, 200);
  assert.match(await response.text(), /Research/);
});

test('keeps missing assets as 404', async () => {
  const response = await worker.fetch(new Request('https://example.test/assets/missing.css'), env);
  assert.equal(response.status, 404);
});
