import { expect, test } from './fixtures'

test('切换主题色并在刷新后保持', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', '仅在桌面项目中运行')

  await page.goto('/')
  const switcher = page.locator('.theme-switcher')
  await expect(switcher).toBeVisible()

  await switcher.getByRole('radio', { name: /苔绿/ }).click()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'moss')

  const focusColor = await page.evaluate(() =>
    getComputedStyle(document.documentElement).getPropertyValue('--color-focus').trim(),
  )
  expect(focusColor).toBe('#4f6b52')

  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'moss')
})

test('旧版本保存的主题会重置为新的默认主题', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', '仅在桌面项目中运行')

  await page.addInitScript(() => {
    window.localStorage.setItem('digital-clone-theme', 'teal')
    window.localStorage.removeItem('digital-clone-theme-version')
  })

  await page.goto('/')

  await expect(page.locator('html')).toHaveAttribute('data-theme', 'ochre')
})
