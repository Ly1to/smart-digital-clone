import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  timeout: 45000,
  expect: { timeout: 10000 },
  retries: process.env.CI ? 2 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile-chromium',
      use: { ...devices['Pixel 7'] },
    },
  ],
  webServer: [
    {
      command:
        'rm -f /tmp/digital-clone-e2e.db && uv run alembic upgrade head && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000',
      cwd: '../backend',
      url: 'http://127.0.0.1:8000/api/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
      env: {
        DATABASE_URL: 'sqlite:////tmp/digital-clone-e2e.db',
        GITHUB_USERNAME: '',
        GITHUB_TOKEN: '',
        GITHUB_AUTO_SYNC_MINUTES: '0',
        GITEE_USERNAME: '',
        GITEE_ACCESS_TOKEN: '',
        GITEE_AUTO_SYNC_MINUTES: '0',
        JWT_SECRET: 'e2e-jwt-secret-at-least-32-bytes-long',
        AUTH_BOOTSTRAP_USERNAME: 'e2e-user',
        AUTH_BOOTSTRAP_PASSWORD: 'e2e-password-123',
      },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  ],
})
