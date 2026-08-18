import { cpSync, existsSync, lstatSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { resolve } from 'node:path';
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
        if (existsSync(source)) cpSync(source, resolve(out, name), { recursive: true });
      };

      mkdirSync(out, { recursive: true });
      readdirSync(root)
        .filter((name) => name.endsWith('.html') && name !== 'index.html')
        .forEach(copy);
      ['styles.css', 'assets', 'notes', 'verification', 'output'].forEach(copy);

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
