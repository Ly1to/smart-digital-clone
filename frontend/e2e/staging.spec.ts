import { expect, test } from './fixtures'

test('暂存区展示 GitHub / Gitee 同步入口和空状态', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', '仅在桌面项目中运行')

  await page.goto('/')
  await page.getByRole('button', { name: '打开暂存区' }).click()

  const drawer = page.locator('.staging-drawer')
  await expect(drawer).toBeVisible()
  await expect(drawer.getByText('待确认日程')).toBeVisible()
  await expect(drawer.getByText('GitHub 仓库更新')).toBeVisible()
  await expect(drawer.getByText('Gitee 仓库更新')).toBeVisible()
  await expect(drawer.getByText('暂存区为空')).toBeVisible()
})
