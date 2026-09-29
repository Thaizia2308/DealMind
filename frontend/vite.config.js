import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Read VITE_* variables from the single .env file in the project root (../.env).
export default defineConfig({
  plugins: [react()],
  envDir: '..',
  server: {
    port: 5173,
    // Development convenience only: when VITE_API_URL is empty, /api is proxied to the local backend.
    // This proxy is NOT used by the production build.
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
