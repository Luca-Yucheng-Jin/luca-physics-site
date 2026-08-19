import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';


const root = path.resolve('.');


test('compact note navigation keeps Topics in the header flow', async () => {
  const [theme, css] = await Promise.all([
    readFile(path.join(root, 'assets', 'theme.js'), 'utf8'),
    readFile(path.join(root, 'styles.css'), 'utf8'),
  ]);

  assert.match(
    theme,
    /nav\.insertBefore\(btn, nav\.firstChild\)/,
    'Topics should be inserted into the primary navigation cluster',
  );
  assert.doesNotMatch(
    theme,
    /topbar\.insertBefore\(btn/,
    'Topics must not be a separate fixed sibling beside the brand',
  );
  assert.match(
    css,
    /@media \(max-width: 1279\.98px\)[\s\S]*?\.site-nav-toggle\s*\{[^}]*position:\s*static;[^}]*flex:\s*0 0 auto;/,
    'Topics should return to normal header flow throughout the drawer layout',
  );
});
