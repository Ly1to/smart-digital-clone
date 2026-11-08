import { expect, test } from './fixtures'

test('桌面端创建、筛选、编辑并删除私人时间日程', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', '仅在桌面项目中运行')

  const title = `E2E 日程 ${Date.now()}`
  const updatedTitle = `${title}（已更新）`

  await page.goto('/')
  await expect(page.locator('.fc')).toBeVisible()

  // 创建
  const panel = page.locator('.panel-content')
  await page.locator('.top-bar__new').click()
  await expect(panel.locator('.panel-form')).toBeVisible()
  await panel.getByPlaceholder('例如：项目周会').fill(title)
  await panel.getByRole('radio', { name: /私人时间/ }).click()
  await panel.getByRole('button', { name: '保存' }).click()

  await expect(page.getByText('日程已保存')).toBeVisible()
  await expect(panel.locator('.detail-panel')).toContainText(title)
  const eventItem = page.locator('.fc-event', { hasText: title })
  await expect(eventItem).toBeVisible()

  // 搜索标题，点击结果后跳到对应日期并打开详情
  await page.getByRole('button', { name: '搜索日程' }).click()
  const searchPanel = page.getByRole('dialog', { name: '搜索日程' })
  await searchPanel.getByPlaceholder('搜索标题或描述').fill(title)
  const searchResult = searchPanel.locator('.search-result').filter({ hasText: title })
  await expect(searchResult).toBeVisible()
  await searchResult.click()
  await expect(panel.locator('.detail-panel')).toContainText(title)

  // 分类筛选：只看私人时间时仍然可见
  const categoryFilter = page.locator('.category-filter')
  const workOption = categoryFilter.locator('.category-option').filter({ hasText: '工作' })
  const outingOption = categoryFilter.locator('.category-option').filter({ hasText: '外出' })
  const privateOption = categoryFilter.locator('.category-option').filter({ hasText: '私人时间' })

  await workOption.click()
  await outingOption.click()
  await expect(eventItem).toBeVisible()

  // 只看工作/外出后，私人日程消失
  await workOption.click()
  await privateOption.click()
  await expect(eventItem).toHaveCount(0)

  await page.getByText('显示全部', { exact: true }).click()
  await expect(eventItem).toBeVisible()

  // 编辑
  await eventItem.click()
  await expect(panel.locator('.detail-panel')).toContainText(title)
  await panel.getByRole('button', { name: '编辑' }).click()
  await panel.getByPlaceholder('例如：项目周会').fill(updatedTitle)
  await panel.getByRole('button', { name: '保存' }).click()

  await expect(page.getByText('日程已保存')).toBeVisible()
  await expect(panel.locator('.detail-panel')).toContainText(updatedTitle)
  const updatedEvent = page.locator('.fc-event', { hasText: updatedTitle })
  await expect(updatedEvent).toBeVisible()

  // 删除
  await updatedEvent.click()
  await panel.getByRole('button', { name: '删除这个日程' }).click()
  const confirmBox = page.locator('.el-message-box')
  await expect(confirmBox).toContainText('删除这个日程？')
  await confirmBox.getByRole('button', { name: '删除', exact: true }).click()

  await expect(page.getByText('日程已删除')).toBeVisible()
  await expect(updatedEvent).toHaveCount(0)
})
