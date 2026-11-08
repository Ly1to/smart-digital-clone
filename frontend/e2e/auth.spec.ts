import { expect, test } from '@playwright/test'

test('未登录时进入登录页并可登录退出', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', '仅在桌面项目中运行')

  await page.goto('/')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: '登录你的日程' })).toBeVisible()

  await page.getByPlaceholder('输入用户名').fill('e2e-user')
  await page.getByPlaceholder('输入密码').fill('e2e-password-123')
  await page.getByRole('button', { name: '登录', exact: true }).click()

  await expect(page).toHaveURL(/\/$/)
  await expect(page.locator('.fc')).toBeVisible()
  await expect(page.getByText('e2e-user')).toBeVisible()

  await page.getByRole('button', { name: '退出登录' }).click()
  await expect(page).toHaveURL(/\/login$/)
})
