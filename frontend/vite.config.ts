import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { configDefaults } from 'vitest/config'

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
    // Browser tests run under Playwright, not Vitest.
    exclude: [...configDefaults.exclude, 'e2e/**'],
  },
})
