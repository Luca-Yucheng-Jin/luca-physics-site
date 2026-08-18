#!/usr/bin/env node

import { existsSync } from 'node:fs';
import { mkdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright-core';

const ROOT = path.resolve(import.meta.dirname, '..');
const OUTPUT = path.join(ROOT, 'output', 'pdf');
const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const PRINT_CSS = `
  :root,
  [data-theme="dark"] {
    color-scheme: light !important;
    --paper: #ffffff !important;
    --paper-deep: #f5f1e7 !important;
    --paper-shade: #ebe4d6 !important;
    --ink: #17130f !important;
    --ink-soft: #3e372f !important;
    --muted: #71675a !important;
    --rule: #cfc5b4 !important;
    --rule-soft: #e4dccf !important;
    --accent: #792d2d !important;
  }
  *, *::before, *::after { animation: none !important; transition: none !important; }
  html, body { background: #fff !important; background-image: none !important; }
  body { font-family: Georgia, "Times New Roman", Times, serif !important; }
  .topbar, .footer, .page-controls, .site-nav, .site-nav-toggle,
  .note__formats, .catalogue__formats, .ornament-rule,
  main.note > p:last-of-type { display: none !important; }
  main.note, main.page { width: 100% !important; max-width: none !important; margin: 0 !important; padding: 0 !important; }
  .note__title { max-width: 100% !important; margin-top: 0 !important; }
  mjx-container { overflow: visible !important; }
`;

async function loadWorks() {
  const manifest = JSON.parse(await readFile(path.join(ROOT, 'assets', 'nav-manifest.json'), 'utf8'));
  const notes = manifest.categories.flatMap((category) =>
    category.groups.flatMap((group) =>
      group.notes.map((note) => ({
        slug: path.basename(note.href, '.html'),
        source: path.join(ROOT, note.href),
      })),
    ),
  );

  return notes;
}

async function renderWork(browser, work) {
  const page = await browser.newPage({ colorScheme: 'light' });
  const output = path.join(OUTPUT, `${work.slug}.pdf`);
  try {
    await page.goto(pathToFileURL(work.source).href, { waitUntil: 'networkidle', timeout: 90_000 });
    await page.evaluate(async () => {
      document.documentElement.dataset.theme = 'light';
      if (window.MathJax?.startup?.promise) await window.MathJax.startup.promise;
      await document.fonts.ready;
      await Promise.all(Array.from(document.images).map((image) => image.decode().catch(() => undefined)));
    });

    const mathErrors = await page.locator('mjx-merror, .mjx-merror').count();
    if (mathErrors) throw new Error(`${mathErrors} MathJax rendering error(s)`);

    await page.addStyleTag({ content: PRINT_CSS });
    await page.emulateMedia({ media: 'print', colorScheme: 'light' });
    await page.pdf({
      path: output,
      format: 'A4',
      printBackground: true,
      preferCSSPageSize: true,
      displayHeaderFooter: false,
      tagged: true,
    });
    process.stdout.write(`  wrote ${path.relative(ROOT, output)}\n`);
  } finally {
    await page.close();
  }
}

async function main() {
  if (!existsSync(CHROME)) throw new Error(`Chrome executable not found: ${CHROME}`);
  await mkdir(OUTPUT, { recursive: true });

  const requested = process.argv.slice(2);
  const allWorks = await loadWorks();
  const works = requested.length ? allWorks.filter((work) => requested.includes(work.slug)) : allWorks;
  if (!works.length) throw new Error('No matching work slugs were found.');

  const browser = await chromium.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--allow-file-access-from-files'],
  });

  try {
    for (const work of works) await renderWork(browser, work);
  } finally {
    await browser.close();
  }

  process.stdout.write(`Generated ${works.length} PDF edition${works.length === 1 ? '' : 's'}.\n`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
