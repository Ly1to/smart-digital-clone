import { expect, test } from '@playwright/test'

test('全天日程按首尾日期都包含展示', async ({ page, request }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', '仅在桌面项目中运行')

  const title = `全天日程 ${Date.now()}`
  const startDate = new Date().toISOString().slice(0, 10)
  const endDate = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().slice(0, 10)

  const created = await request.post('/api/schedules', {
    data: {
      title,
      category: 'outing',
      start_at: `${startDate}T00:00:00Z`,
      end_at: `${endDate}T00:00:00Z`,
      all_day: true,
    },
  })
  expect(created.ok()).toBeTruthy()
  const schedule = await created.json()

  try {
    await page.goto('/')
    await expect(page.locator('.fc')).toBeVisible()
    await page.getByRole('button', { name: '月', exact: true }).click()

    const eventItem = page.locator('.fc-event', { hasText: title })
    await expect(eventItem).toBeVisible()
    await eventItem.click()

    const detail = page.locator('.detail-panel')
    await expect(detail).toContainText(startDate)
    await expect(detail).toContainText(endDate)
    await expect(detail).toContainText('全天')
  } finally {
    await request.delete(`/api/schedules/${schedule.id}`)
  }
})
