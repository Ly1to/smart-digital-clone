import { expect, test } from './fixtures'

test('移动端在今日议程中创建、编辑并删除日程', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-chromium', '仅在移动端项目中运行')

  const title = `移动端日程 ${Date.now()}`
  const updatedTitle = `${title}（已更新）`

  await page.goto('/')
  await expect(page.locator('.agenda')).toBeVisible()
  await expect(page.getByText('今日安排')).toBeVisible()

  // 创建
  await page.locator('.fab').click()
  const sheet = page.locator('.mobile-panel')
  await expect(sheet).toBeVisible()
  await sheet.getByPlaceholder('例如：项目周会').fill(title)
  await sheet.getByRole('radio', { name: /私人时间/ }).click()
  await sheet.getByRole('button', { name: '保存' }).click()

  await expect(page.getByText('日程已保存')).toBeVisible()
  await expect(sheet.locator('.detail-panel')).toContainText(title)
  await sheet.getByRole('button', { name: '关闭日程详情' }).click()

  const agendaItem = page.locator('.agenda-item', { hasText: title })
  await expect(agendaItem).toBeVisible()

  // 编辑
  await agendaItem.click()
  await expect(sheet.locator('.detail-panel')).toContainText(title)
  await sheet.getByRole('button', { name: '编辑' }).click()
  await sheet.getByPlaceholder('例如：项目周会').fill(updatedTitle)
  await sheet.getByRole('button', { name: '保存' }).click()

  await expect(page.getByText('日程已保存')).toBeVisible()
  await expect(sheet.locator('.detail-panel')).toContainText(updatedTitle)
  await sheet.getByRole('button', { name: '关闭日程详情' }).click()

  const updatedItem = page.locator('.agenda-item', { hasText: updatedTitle })
  await expect(updatedItem).toBeVisible()

  // 删除
  await updatedItem.click()
  await sheet.getByRole('button', { name: '删除这个日程' }).click()
  const confirmBox = page.locator('.el-message-box')
  await expect(confirmBox).toContainText('删除这个日程？')
  await confirmBox.getByRole('button', { name: '删除', exact: true }).click()

  await expect(page.getByText('日程已删除')).toBeVisible()
  await expect(updatedItem).toHaveCount(0)
})
