import { expect, test as base } from '@playwright/test'

const E2E_USERNAME = 'e2e-user'
const E2E_PASSWORD = 'e2e-password-123'

export const test = base.extend<{ authToken: string }>({
  authToken: async ({ request }, use) => {
    const response = await request.post('/api/auth/login', {
      data: { username: E2E_USERNAME, password: E2E_PASSWORD },
    })
    if (!response.ok()) {
      throw new Error(`E2E 登录失败：${response.status()} ${await response.text()}`)
    }
    const payload = (await response.json()) as { access_token: string }
    await use(payload.access_token)
  },

  page: async ({ page, authToken }, use) => {
    await page.addInitScript((token: string) => {
      window.localStorage.setItem('digital-clone-auth-token', token)
    }, authToken)
    await use(page)
  },
})

export { expect }
