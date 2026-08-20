import { cpSync, existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { basename, dirname, resolve } from 'node:path';
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';

function preserveLegacySite(): Plugin {
  return {
    name: 'preserve-legacy-physics-site',
    buildStart() {
      const buildRoot = resolve(process.cwd(), 'dist');
      if (!existsSync(buildRoot)) return;
      if (lstatSync(buildRoot).isSymbolicLink()) {
        throw new Error('Refusing to clean a symlinked dist directory.');
      }
      rmSync(buildRoot, { recursive: true, force: true });
    },
    closeBundle() {
      const root = process.cwd();
      const buildRoot = resolve(root, 'dist');
      const out = resolve(buildRoot, 'client');
      const copy = (name: string) => {
        const source = resolve(root, name);
        if (!existsSync(source)) throw new Error(`Missing public site input: ${name}`);
        const destination = resolve(out, name);
        mkdirSync(dirname(destination), { recursive: true });
        cpSync(source, destination, { recursive: true });
      };

      const manifest = JSON.parse(
        readFileSync(resolve(root, 'assets/nav-manifest.json'), 'utf8'),
      ) as {
        categories: Array<{
          groups: Array<{ notes: Array<{ href: string }> }>;
        }>;
      };
      const publicNotes = manifest.categories.flatMap((category) =>
        category.groups.flatMap((group) => group.notes.map((note) => note.href)),
      );

      mkdirSync(out, { recursive: true });
      readdirSync(root)
        .filter((name) => name.endsWith('.html') && name !== 'index.html')
        .forEach(copy);
      ['styles.css', 'assets', 'robots.txt', 'sitemap.xml'].forEach(copy);
      publicNotes.forEach((note) => {
        copy(note);
        copy(`output/pdf/${basename(note, '.html')}.pdf`);
      });

      const workerSource = resolve(root, 'worker/index.js');
      const serverOut = resolve(buildRoot, 'server');
      mkdirSync(serverOut, { recursive: true });
      cpSync(workerSource, resolve(serverOut, 'index.js'));
    },
  };
}

export default defineConfig({
  base: './',
  plugins: [react(), preserveLegacySite()],
  build: {
    outDir: 'dist/client',
    emptyOutDir: true,
  },
});
