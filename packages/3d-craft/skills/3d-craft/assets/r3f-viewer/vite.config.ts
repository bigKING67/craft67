import os from 'node:os'
import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  cacheDir: path.join(os.tmpdir(), '3d-craft-vite-cache'),
  plugins: [react()],
  build: {
    outDir: process.env.VITE_OUT_DIR || path.join(os.tmpdir(), '3d-craft-viewer-dist'),
    emptyOutDir: true,
    // Three.js is intentionally isolated as an async runtime chunk. Keep the
    // warning ceiling just above the pinned r185 build so dependency growth is
    // still surfaced without treating the known engine boundary as accidental.
    chunkSizeWarningLimit: 800,
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: 'react-runtime',
              test: /node_modules[\\/](?:react|react-dom|scheduler)[\\/]/,
              priority: 30,
            },
            {
              name: 'three-runtime',
              test: /node_modules[\\/]three[\\/]/,
              priority: 20,
            },
            {
              name: 'r3f-runtime',
              test: /node_modules[\\/]@react-three[\\/]/,
              priority: 20,
            },
            {
              name: 'vendor',
              test: /node_modules[\\/]/,
              priority: 10,
            },
          ],
        },
      },
    },
  },
  server: {
    host: '127.0.0.1',
    port: 41767,
    strictPort: true,
  },
  preview: {
    host: '127.0.0.1',
    port: 41767,
    strictPort: true,
  },
})
