import { expect, test } from '@playwright/test'

test('从登录页进入注册页并创建账号', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', '仅在桌面项目中运行')

  const username = `e2e-register-${Date.now()}`

  await page.goto('/login')
  await page.getByRole('link', { name: '没有账号？创建一个' }).click()
  await expect(page).toHaveURL(/\/register$/)
  await expect(page.getByRole('heading', { name: '注册你的日程空间' })).toBeVisible()

  await page.getByPlaceholder('输入用户名').fill(username)
  await page.getByPlaceholder('至少 8 个字符').fill('register-password-123')
  await page.getByPlaceholder('再次输入密码').fill('register-password-123')
  await page.getByRole('button', { name: '创建账号并进入' }).click()

  await expect(page).toHaveURL(/\/$/)
  await expect(page.locator('.fc')).toBeVisible()
  await expect(page.getByText(username)).toBeVisible()
})
