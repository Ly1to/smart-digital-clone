import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CategoryFilter from '@/components/filters/CategoryFilter.vue'
import * as scheduleApi from '@/api/schedules'
import { useScheduleStore } from '@/stores/schedule'

vi.mock('@/api/schedules', () => ({
  fetchSchedules: vi.fn(),
  fetchSchedule: vi.fn(),
  createSchedule: vi.fn(),
  updateSchedule: vi.fn(),
  deleteSchedule: vi.fn(),
}))

const fetchMock = vi.mocked(scheduleApi.fetchSchedules)

function mountFilter() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(CategoryFilter, {
    props: { dayDate: '2026-11-05' },
    global: {
      plugins: [pinia, ElementPlus],
    },
  })
  return { wrapper, store: useScheduleStore() }
}

describe('CategoryFilter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fetchMock.mockResolvedValue([])
  })

  it('shows all three categories with counts and color dots', () => {
    const { wrapper } = mountFilter()

    expect(wrapper.findAll('.category-option')).toHaveLength(3)
    expect(wrapper.findAll('.category-option__dot')).toHaveLength(3)
    expect(wrapper.text()).toContain('工作')
    expect(wrapper.text()).toContain('外出')
    expect(wrapper.text()).toContain('私人时间')
  })

  it('toggles a category and applies filters immediately', async () => {
    const { wrapper, store } = mountFilter()

    const workOption = wrapper
      .findAll('.category-option')
      .find((item) => item.text().includes('工作'))
    expect(workOption).toBeTruthy()
    await workOption!.trigger('click')
    await flushPromises()

    expect(store.filters.categories).toEqual(['outing', 'private'])
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('restores every category with the show-all action', async () => {
    const { wrapper, store } = mountFilter()
    store.filters.categories = ['work']
    await flushPromises()

    const showAll = wrapper.findAll('button').find((item) => item.text() === '显示全部')
    expect(showAll).toBeTruthy()
    await showAll!.trigger('click')
    await flushPromises()

    expect(store.filters.categories).toEqual(['work', 'outing', 'private'])
    expect(store.hasActiveFilters).toBe(false)
  })

  it('explains that an empty selection shows everything', async () => {
    const { wrapper, store } = mountFilter()
    store.filters.categories = []
    await flushPromises()

    expect(wrapper.text()).toContain('未选择分类时显示全部日程')
  })
})
