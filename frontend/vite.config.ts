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
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
