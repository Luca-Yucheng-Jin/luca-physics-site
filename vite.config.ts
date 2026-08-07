import { cpSync, existsSync, mkdirSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';

function preserveLegacySite(): Plugin {
  return {
    name: 'preserve-legacy-physics-site',
    closeBundle() {
      const root = process.cwd();
      const out = resolve(root, 'dist');
      const copy = (name: string) => {
        const source = resolve(root, name);
        if (existsSync(source)) cpSync(source, resolve(out, name), { recursive: true });
      };

      mkdirSync(out, { recursive: true });
      readdirSync(root)
        .filter((name) => name.endsWith('.html') && name !== 'index.html')
        .forEach(copy);
      ['styles.css', 'assets', 'notes', 'verification'].forEach(copy);
    },
  };
}

export default defineConfig({
  base: './',
  plugins: [react(), preserveLegacySite()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
