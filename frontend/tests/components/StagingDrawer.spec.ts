import { flushPromises, mount } from '@vue/test-utils'
import dayjs from 'dayjs'
import ElementPlus from 'element-plus'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import StagingDrawer from '@/components/staging/StagingDrawer.vue'
import * as scheduleApi from '@/api/schedules'
import * as stagingApi from '@/api/staging'
import { useScheduleStore } from '@/stores/schedule'
import type { Schedule, StagedSchedule } from '@/types/schedule'

vi.mock('@/api/schedules', () => ({
  fetchSchedules: vi.fn(),
  fetchSchedule: vi.fn(),
  createSchedule: vi.fn(),
  updateSchedule: vi.fn(),
  deleteSchedule: vi.fn(),
}))

vi.mock('@/api/staging', () => ({
  fetchStagedSchedules: vi.fn(),
  updateStagedSchedule: vi.fn(),
  approveStagedSchedule: vi.fn(),
  rejectStagedSchedule: vi.fn(),
  approveAllStagedSchedules: vi.fn(),
  fetchGithubStatus: vi.fn(),
  syncGithub: vi.fn(),
  fetchGiteeStatus: vi.fn(),
  syncGitee: vi.fn(),
}))

const fetchSchedulesMock = vi.mocked(scheduleApi.fetchSchedules)
const fetchStagedMock = vi.mocked(stagingApi.fetchStagedSchedules)
const fetchGithubStatusMock = vi.mocked(stagingApi.fetchGithubStatus)
const fetchGiteeStatusMock = vi.mocked(stagingApi.fetchGiteeStatus)
const syncGithubMock = vi.mocked(stagingApi.syncGithub)
const approveStagedMock = vi.mocked(stagingApi.approveStagedSchedule)

function makeStaged(overrides: Partial<StagedSchedule> = {}): StagedSchedule {
  return {
    id: 11,
    source: 'github',
    source_ref: 'github:octo/demo:abc123',
    source_url: 'https://github.com/octo/demo',
    source_meta: { repo: 'octo/demo' },
    title: 'GitHub 更新：octo/demo',
    category: 'work',
    description: '2 次提交',
    start_at: '2026-11-08T02:00:00Z',
    end_at: '2026-11-08T02:30:00Z',
    all_day: false,
    location: null,
    status: 'pending',
    schedule_id: null,
    created_at: '2026-11-08T01:00:00Z',
    updated_at: '2026-11-08T01:00:00Z',
    approved_at: null,
    ...overrides,
  }
}

function makeSchedule(): Schedule {
  return {
    id: 7,
    title: 'GitHub 更新：octo/demo',
    category: 'work',
    description: '2 次提交',
    start_at: '2026-11-08T02:00:00Z',
    end_at: '2026-11-08T02:30:00Z',
    all_day: false,
    location: null,
    status: 'pending',
    source: 'github',
    created_at: '2026-11-08T01:00:00Z',
    updated_at: '2026-11-08T01:00:00Z',
  }
}

function mountDrawer() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(StagingDrawer, {
    props: { modelValue: true },
    global: {
      plugins: [pinia, ElementPlus],
      stubs: {
        teleport: true,
        transition: false,
      },
    },
  })
  return { wrapper, store: useScheduleStore(), pinia }
}

describe('StagingDrawer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fetchSchedulesMock.mockResolvedValue([])
    fetchStagedMock.mockResolvedValue([makeStaged()])
    fetchGithubStatusMock.mockResolvedValue({
      configured: true,
      username: 'octo',
      lookback_days: 14,
      token_configured: false,
    })
    fetchGiteeStatusMock.mockResolvedValue({
      configured: true,
      username: 'oschina',
      lookback_days: 14,
      token_configured: true,
    })
  })

  it('renders pending GitHub updates with suggested time', async () => {
    const { wrapper } = mountDrawer()
    await flushPromises()

    expect(wrapper.text()).toContain('待确认日程')
    expect(wrapper.text()).toContain('GitHub 仓库更新')
    expect(wrapper.text()).toContain('Gitee 仓库更新')
    expect(wrapper.text()).toContain('GitHub 更新：octo/demo')
    expect(wrapper.text()).toContain(
      `建议 ${dayjs('2026-11-08T02:00:00Z').format('HH:mm')}–${dayjs('2026-11-08T02:30:00Z').format(
        'HH:mm',
      )}`,
    )
    expect(wrapper.text()).toContain('1 条待确认')
  })

  it('syncs GitHub and shows the result message', async () => {
    const { wrapper } = mountDrawer()
    await flushPromises()
    syncGithubMock.mockResolvedValue({
      configured: true,
      scanned_events: 3,
      created: 1,
      updated: 0,
      skipped: 0,
      no_slot: 0,
      message: '已扫描 3 条 GitHub 动态：新增 1 条，更新 0 条',
    })

    const syncButton = wrapper.findAll('button').find((button) => button.text() === '同步')
    expect(syncButton).toBeTruthy()
    await syncButton!.trigger('click')
    await flushPromises()

    expect(syncGithubMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('新增 1 条')
  })

  it('approves a staged item', async () => {
    const { wrapper } = mountDrawer()
    await flushPromises()
    approveStagedMock.mockResolvedValue({
      staged: makeStaged({ status: 'approved', schedule_id: 7 }),
      schedule: makeSchedule(),
    })

    const approveButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('插入日程'))
    expect(approveButton).toBeTruthy()
    await approveButton!.trigger('click')
    await flushPromises()

    expect(approveStagedMock).toHaveBeenCalledWith(11)
  })

  it('shows an empty state when nothing is staged', async () => {
    fetchStagedMock.mockResolvedValue([])
    const { wrapper } = mountDrawer()
    await flushPromises()

    expect(wrapper.text()).toContain('暂存区为空')
  })
})
