/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development the React app runs on :5173 and proxies API calls to the FastAPI
// backend on :8000, so the browser sees a single origin (no CORS needed).
export default defineConfig({
  plugins: [react()],
  // Guarantee a single copy of React across the app and all dependencies (Mantine hooks),
  // avoiding "Invalid hook call" from duplicate React instances.
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  build: {
    rollupOptions: {
      output: {
        // Split rarely-changing library code into stable, separately-cached chunks so an
        // app-code redeploy doesn't invalidate the browser's cached copy of React/Mantine.
        // Recharts is intentionally NOT listed, so it stays in the lazy dashboard chunk.
        manualChunks(id: string) {
          if (/[\\/]node_modules[\\/](react|react-dom|react-router|react-router-dom|scheduler)[\\/]/.test(id)) {
            return 'react-vendor'
          }
          if (/[\\/]node_modules[\\/](@mantine|@tabler)[\\/]/.test(id)) {
            return 'mantine-vendor'
          }
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  preview: {
    port: 4173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    css: false,
  },
})
