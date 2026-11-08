import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import dayjs from 'dayjs'

import * as scheduleApi from '@/api/schedules'
import * as stagingApi from '@/api/staging'
import { createDefaultFilters, useScheduleStore } from '@/stores/schedule'
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

const fetchMock = vi.mocked(scheduleApi.fetchSchedules)
const createMock = vi.mocked(scheduleApi.createSchedule)
const updateMock = vi.mocked(scheduleApi.updateSchedule)
const deleteMock = vi.mocked(scheduleApi.deleteSchedule)
const fetchStagedMock = vi.mocked(stagingApi.fetchStagedSchedules)
const syncGithubMock = vi.mocked(stagingApi.syncGithub)
const syncGiteeMock = vi.mocked(stagingApi.syncGitee)
const approveStagedMock = vi.mocked(stagingApi.approveStagedSchedule)
const rejectStagedMock = vi.mocked(stagingApi.rejectStagedSchedule)

function makeSchedule(overrides: Partial<Schedule> = {}): Schedule {
  return {
    id: 1,
    title: '项目周会',
    category: 'work',
    description: null,
    start_at: '2026-11-05T06:00:00Z',
    end_at: '2026-11-05T07:00:00Z',
    all_day: false,
    location: null,
    status: 'pending',
    created_at: '2026-11-01T00:00:00Z',
    updated_at: '2026-11-01T00:00:00Z',
    ...overrides,
  }
}

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

describe('schedule store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    fetchMock.mockResolvedValue([])
    fetchStagedMock.mockResolvedValue([])
  })

  it('starts with every category and status selected', () => {
    const store = useScheduleStore()

    expect(store.filters).toEqual(createDefaultFilters())
    expect(store.hasActiveFilters).toBe(false)
  })

  it('queries the visible range with category and status filters', async () => {
    const store = useScheduleStore()
    const range = {
      start: '2026-11-01T00:00:00+08:00',
      end: '2026-12-01T00:00:00+08:00',
    }
    store.visibleRange = range
    store.filters.categories = ['work']
    store.filters.statuses = ['pending']

    await store.fetchSchedules()

    expect(fetchMock).toHaveBeenCalledWith({
      start: new Date(range.start).toISOString(),
      end: new Date(range.end).toISOString(),
      categories: 'work',
      statuses: 'pending',
    })
  })

  it('lets an explicit date filter override the visible range', async () => {
    const store = useScheduleStore()
    store.visibleRange = {
      start: '2026-11-01T00:00:00Z',
      end: '2026-12-01T00:00:00Z',
    }
    store.filters.dateRange = ['2026-11-05', '2026-11-06']

    await store.fetchSchedules()

    expect(fetchMock).toHaveBeenCalledWith(
      expect.objectContaining({
        start: dayjs('2026-11-05').startOf('day').toISOString(),
        end: dayjs('2026-11-07').startOf('day').toISOString(),
      }),
    )
  })

  it('treats an empty category selection as no category filter', async () => {
    const store = useScheduleStore()
    store.filters.categories = []

    await store.fetchSchedules()

    expect(fetchMock).toHaveBeenCalledWith(
      expect.objectContaining({
        categories: undefined,
        statuses: 'pending,completed,cancelled',
      }),
    )
  })

  it('stores loaded schedules and marks the first load complete', async () => {
    const store = useScheduleStore()
    fetchMock.mockResolvedValue([makeSchedule()])

    await store.fetchSchedules()

    expect(store.schedules).toHaveLength(1)
    expect(store.loading).toBe(false)
    expect(store.initialized).toBe(true)
    expect(store.error).toBe('')
  })

  it('exposes a readable error and clears stale schedules on failure', async () => {
    const store = useScheduleStore()
    store.schedules = [makeSchedule()]
    fetchMock.mockRejectedValue(new Error('无法连接后端服务'))

    await store.fetchSchedules()

    expect(store.error).toBe('无法连接后端服务')
    expect(store.schedules).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.initialized).toBe(true)
  })

  it('loads one day using the local day window and sorts it', async () => {
    const store = useScheduleStore()
    fetchMock.mockResolvedValue([
      makeSchedule({ id: 2, start_at: '2026-11-05T08:00:00Z' }),
      makeSchedule({ id: 1, start_at: '2026-11-05T01:00:00Z' }),
    ])

    await store.fetchDaySchedules('2026-11-05')

    expect(fetchMock).toHaveBeenCalledWith({
      start: dayjs('2026-11-05').startOf('day').toISOString(),
      end: dayjs('2026-11-06').startOf('day').toISOString(),
      categories: 'work,outing,private',
      statuses: 'pending,completed,cancelled',
    })
    expect(store.daySchedules.map((item) => item.id)).toEqual([1, 2])
  })

  it('exposes a readable error for a failed day load', async () => {
    const store = useScheduleStore()
    fetchMock.mockRejectedValue(new Error('当天加载失败'))

    await store.fetchDaySchedules('2026-11-05')

    expect(store.dayError).toBe('当天加载失败')
    expect(store.daySchedules).toEqual([])
    expect(store.dayLoading).toBe(false)
  })

  it('copies filters and refreshes both views', async () => {
    const store = useScheduleStore()
    const categories: ('work' | 'outing' | 'private')[] = ['work']

    await store.applyFilters(
      {
        categories,
        statuses: ['pending'],
        dateRange: null,
      },
      '2026-11-05',
    )
    categories.push('outing')

    expect(store.filters.categories).toEqual(['work'])
    expect(store.hasActiveFilters).toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('resets all filters and reloads', async () => {
    const store = useScheduleStore()
    store.filters = {
      categories: ['private'],
      statuses: ['completed'],
      dateRange: ['2026-11-05', '2026-11-06'],
    }

    await store.resetFilters('2026-11-05')

    expect(store.filters).toEqual(createDefaultFilters())
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('creates a schedule then refreshes and bumps the revision', async () => {
    const store = useScheduleStore()
    const schedule = makeSchedule()
    createMock.mockResolvedValue(schedule)

    const result = await store.createSchedule(
      {
        title: '项目周会',
        category: 'work',
        description: null,
        start_at: '2026-11-05T06:00:00Z',
        end_at: '2026-11-05T07:00:00Z',
        all_day: false,
        location: null,
        status: 'pending',
      },
      '2026-11-05',
    )

    expect(result).toEqual(schedule)
    expect(createMock).toHaveBeenCalledTimes(1)
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(store.revision).toBe(1)
  })

  it('updates a schedule then refreshes', async () => {
    const store = useScheduleStore()
    const schedule = makeSchedule({ title: '已更新' })
    updateMock.mockResolvedValue(schedule)

    const result = await store.updateSchedule(
      1,
      {
        title: '已更新',
        category: 'work',
        description: null,
        start_at: '2026-11-05T06:00:00Z',
        end_at: '2026-11-05T07:00:00Z',
        all_day: false,
        location: null,
        status: 'completed',
      },
      '2026-11-05',
    )

    expect(result.title).toBe('已更新')
    expect(updateMock).toHaveBeenCalledWith(1, expect.objectContaining({ title: '已更新' }))
    expect(store.revision).toBe(1)
  })

  it('removes a deleted schedule from both lists', async () => {
    const store = useScheduleStore()
    store.schedules = [makeSchedule(), makeSchedule({ id: 2, title: '第二个' })]
    store.daySchedules = [makeSchedule()]
    deleteMock.mockResolvedValue()

    await store.removeSchedule(1)

    expect(deleteMock).toHaveBeenCalledWith(1)
    expect(store.schedules.map((item) => item.id)).toEqual([2])
    expect(store.daySchedules).toEqual([])
    expect(store.revision).toBe(1)
  })

  it('builds category counts and a readable active filter summary', () => {
    const store = useScheduleStore()
    store.countSchedules = [
      makeSchedule({ id: 1, category: 'work' }),
      makeSchedule({ id: 2, category: 'work' }),
      makeSchedule({ id: 3, category: 'private' }),
    ]
    store.filters = {
      categories: ['work', 'private'],
      statuses: ['pending'],
      dateRange: null,
    }

    expect(store.categoryCounts).toEqual({ work: 2, outing: 0, private: 1 })
    expect(store.activeFilterSummary).toBe('工作、私人时间 · 待进行')
  })

  it('loads staged schedules and counts pending items', async () => {
    const store = useScheduleStore()
    fetchStagedMock.mockResolvedValue([makeStaged(), makeStaged({ id: 12, status: 'approved' })])

    await store.fetchStaging()

    expect(store.stagedSchedules).toHaveLength(2)
    expect(store.pendingStagingCount).toBe(1)
    expect(store.stagingLoading).toBe(false)
    expect(store.stagingError).toBe('')
  })

  it('syncs GitHub and reloads the staging area', async () => {
    const store = useScheduleStore()
    const staged = makeStaged()
    syncGithubMock.mockResolvedValue({
      configured: true,
      scanned_events: 4,
      created: 1,
      updated: 0,
      skipped: 0,
      no_slot: 0,
      message: '已扫描 4 条 GitHub 动态：新增 1 条，更新 0 条',
    })
    fetchStagedMock.mockResolvedValue([staged])

    const result = await store.syncGithub()

    expect(result.created).toBe(1)
    expect(syncGithubMock).toHaveBeenCalledTimes(1)
    expect(store.stagedSchedules).toEqual([staged])
    expect(store.syncingGithub).toBe(false)
  })

  it('syncs Gitee and reloads the staging area', async () => {
    const store = useScheduleStore()
    syncGiteeMock.mockResolvedValue({
      configured: true,
      scanned_events: 2,
      created: 1,
      updated: 0,
      skipped: 0,
      no_slot: 0,
      message: '已扫描 2 条 Gitee 动态：新增 1 条，更新 0 条',
    })
    fetchStagedMock.mockResolvedValue([])

    const result = await store.syncGitee()

    expect(result.created).toBe(1)
    expect(syncGiteeMock).toHaveBeenCalledTimes(1)
    expect(store.syncingGitee).toBe(false)
  })

  it('approves a staged schedule and refreshes the calendar', async () => {
    const store = useScheduleStore()
    const staged = makeStaged()
    const schedule = makeSchedule({ id: 7, title: staged.title, source: 'github' })
    approveStagedMock.mockResolvedValue({ staged: { ...staged, status: 'approved' }, schedule })
    fetchStagedMock.mockResolvedValue([])

    const result = await store.approveStaged(staged.id, '2026-11-08')

    expect(result.schedule).toEqual(schedule)
    expect(approveStagedMock).toHaveBeenCalledWith(staged.id)
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(store.revision).toBe(1)
    expect(store.stagedSchedules).toEqual([])
  })

  it('rejects and updates staged schedules', async () => {
    const store = useScheduleStore()
    const staged = makeStaged()
    rejectStagedMock.mockResolvedValue({ ...staged, status: 'rejected' })
    vi.mocked(stagingApi.updateStagedSchedule).mockResolvedValue({
      ...staged,
      title: '改过的标题',
    })

    await store.rejectStaged(staged.id)
    const updated = await store.updateStaged(staged.id, { title: '改过的标题' })

    expect(rejectStagedMock).toHaveBeenCalledWith(staged.id)
    expect(updated.title).toBe('改过的标题')
    expect(fetchStagedMock).toHaveBeenCalledTimes(2)
  })
})
