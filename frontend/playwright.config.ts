import { defineConfig, devices } from '@playwright/test'

const venvBin = process.platform === 'win32' ? '.venv/Scripts' : '.venv/bin'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  reporter: 'list',
  timeout: 120_000,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `${venvBin}/uvicorn monopoly.main:app --port 8000`,
      cwd: '../backend',
      url: 'http://localhost:8000/api/health',
      reuseExistingServer: true,
    },
    {
      command: 'npm run dev -- --port 5173 --strictPort',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
    },
  ],
})
