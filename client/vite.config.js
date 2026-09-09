import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Migrated from Create React App (react-scripts 5.0.1, EOL) to Vite 8.
// JSX lives in .jsx files (CRA's .js-with-JSX files were renamed to .jsx),
// which @vitejs/plugin-react handles natively — no loader overrides needed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
  },
  build: {
    outDir: 'build',
    target: 'es2020',
  },
});
