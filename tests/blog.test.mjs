import assert from 'node:assert/strict';
import { execFile as execFileCallback } from 'node:child_process';
import { readFile, readdir, stat } from 'node:fs/promises';
import { promisify } from 'node:util';
import test from 'node:test';

const execFile = promisify(execFileCallback);

test('blog generation orders entries, escapes prose, and withdraws drafts', async () => {
  const script = String.raw`
import json, pathlib, sys, tempfile
sys.path.insert(0, 'build')
from build_blog import build

with tempfile.TemporaryDirectory() as temporary:
    root = pathlib.Path(temporary)
    source = root / 'content'
    source.mkdir()
    def entry(slug, day, draft=False):
        (source / (slug + '.json')).write_text(json.dumps({
            'title': '</script><script>alert(2)</script>', 'date': day, 'summary': 'An open question.',
            'paragraphs': ['First paragraph.[^1]', '<script>alert(1)</script>', r'Maths: $E = mc^2$.'],
            'footnotes': ['A note with <escaped> text.'],
            'draft': draft,
        }))
    entry('older', '2026-01-01')
    entry('newer', '2026-02-01')
    entry('private-draft', '2026-03-01', True)
    build(source, root)
    archive = (root / 'blog.html').read_text()
    article = (root / 'blog/newer.html').read_text()
    assert archive.index('blog/newer.html') < archive.index('blog/older.html')
    assert 'private-draft' not in archive
    assert not (root / 'blog/private-draft.html').exists()
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in article
    assert '<p><script>' not in article
    assert '</script><script>alert(2)</script>' not in article
    assert 'src="../assets/mathjax-config.js"' in article
    assert 'src="../assets/blog-math.js"' in article
    assert 'href="../blog.html"' in article
    assert '$E = mc^2$' in article
    assert 'href="#fn-1"' in article and 'id="fn-1"' in article
    assert 'href="#fnref-1"' in article
    assert 'A note with &lt;escaped&gt; text.' in article
    entry('newer', '2026-02-01', True)
    build(source, root)
    assert not (root / 'blog/newer.html').exists()
    assert 'blog/newer.html' not in (root / 'blog.html').read_text()
`;
  await execFile('python3', ['-c', script]);
});

test('production blog includes its styles and keeps authoring drafts out', async () => {
  const archive = await readFile('dist/client/blog.html', 'utf8');
  const article = await readFile('dist/client/blog/electron-and-hole-density.html', 'utf8');
  const blogStyles = await readFile('assets/blog.css', 'utf8');
  const theme = await readFile('assets/theme.js', 'utf8');
  assert.match(archive, /<h1>Blog<\/h1>/);
  assert.match(archive, /href="blog.html" class="is-active" aria-current="page"/);
  assert.match(archive, /<body class="blog-page">/);
  assert.match(article, /<body class="blog-page">/);
  assert.doesNotMatch(archive, /A thought to come back to/);
  assert.match(blogStyles, /width: min\(78ch, calc\(100vw - 2 \* var\(--gutter\)\)\)/);
  assert.match(blogStyles, /font-size: clamp\(2\.4rem, 4\.5vw, 4rem\)/);
  assert.match(blogStyles, /@media \(max-width: 720px\)[\s\S]*grid-template-columns: minmax\(0, 1fr\)/);
  assert.match(theme, /body\.classList\.contains\("blog-page"\)/);
  await stat('dist/client/assets/blog.css');
  await assert.rejects(stat('dist/client/content'), { code: 'ENOENT' });
  assert.ok(!(await readdir('dist/client/blog')).includes('_template.json'));
});
