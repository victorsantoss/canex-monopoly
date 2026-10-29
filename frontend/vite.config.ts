/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const backendUrl = 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    // Same-origin in development: no CORS configuration needed on the backend.
    proxy: {
      '/api': backendUrl,
      '/ws': { target: backendUrl.replace('http', 'ws'), ws: true },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
  },
})
