import dayjs from 'dayjs'
import { describe, expect, it } from 'vitest'

import { createDefaultFilters } from '@/stores/schedule'
import type { Schedule } from '@/types/schedule'
import {
  allDayDate,
  buildQueryWindow,
  formatAgendaTime,
  formatDayTitle,
  formatScheduleDate,
  formatScheduleTime,
  groupSchedulesByDate,
  localDayRange,
  localWeekRange,
  scheduleDateKey,
  toUtcIso,
} from '@/utils/date'

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

describe('date utils', () => {
  it('converts local date time to UTC ISO', () => {
    expect(toUtcIso('2026-11-05T14:00:00')).toBe(new Date('2026-11-05T14:00:00').toISOString())
  })

  it('formats all-day dates without timezone shifting', () => {
    expect(
      formatScheduleDate({
        all_day: true,
        start_at: '2026-11-05T00:00:00Z',
        end_at: '2026-11-05T23:59:59.999999Z',
      }),
    ).toBe('2026-11-05')
    expect(
      formatScheduleDate({
        all_day: true,
        start_at: '2026-11-05T00:00:00Z',
        end_at: '2026-11-06T23:59:59.999999Z',
      }),
    ).toBe('2026-11-05 至 2026-11-06')
  })

  it('formats all-day time as the whole day', () => {
    expect(
      formatScheduleTime({
        all_day: true,
        start_at: '2026-11-05T00:00:00Z',
        end_at: '2026-11-05T23:59:59.999999Z',
      }),
    ).toBe('全天')
  })

  it('formats same-day timed events with a short end time', () => {
    const start = dayjs('2026-11-05T09:00:00')
    const end = dayjs('2026-11-05T10:30:00')
    expect(
      formatScheduleTime({
        all_day: false,
        start_at: start.toISOString(),
        end_at: end.toISOString(),
      }),
    ).toBe('09:00–10:30')
  })

  it('keeps full dates on cross-day timed events', () => {
    const start = dayjs('2026-11-05T23:00:00')
    const end = dayjs('2026-11-06T01:00:00')
    expect(
      formatScheduleTime({
        all_day: false,
        start_at: start.toISOString(),
        end_at: end.toISOString(),
      }),
    ).toBe(`${start.format('YYYY-MM-DD HH:mm')} – ${end.format('YYYY-MM-DD HH:mm')}`)
  })

  it('formats agenda time as start time or all-day', () => {
    const schedule = makeSchedule()
    expect(formatAgendaTime(schedule)).toBe(dayjs(schedule.start_at).format('HH:mm'))
    expect(formatAgendaTime({ ...schedule, all_day: true })).toBe('全天')
  })

  it('uses the inclusive local date filter as an exclusive API window', () => {
    const window = buildQueryWindow(
      { ...createDefaultFilters(), dateRange: ['2026-11-05', '2026-11-06'] },
      null,
    )

    expect(window.start).toBe(dayjs('2026-11-05').startOf('day').toISOString())
    expect(window.end).toBe(dayjs('2026-11-06').add(1, 'day').startOf('day').toISOString())
  })

  it('falls back to the visible calendar range', () => {
    const window = buildQueryWindow(createDefaultFilters(), {
      start: '2026-11-01T00:00:00+08:00',
      end: '2026-12-01T00:00:00+08:00',
    })

    expect(window.start).toBe(new Date('2026-11-01T00:00:00+08:00').toISOString())
    expect(window.end).toBe(new Date('2026-12-01T00:00:00+08:00').toISOString())
  })

  it('returns an empty window before the calendar reports a range', () => {
    expect(buildQueryWindow(createDefaultFilters(), null)).toEqual({})
  })

  it('builds local day and Monday-first week ranges', () => {
    const day = localDayRange('2026-11-05')
    expect(day.start).toBe(dayjs('2026-11-05').startOf('day').toISOString())
    expect(day.end).toBe(dayjs('2026-11-06').startOf('day').toISOString())

    const week = localWeekRange('2026-11-05')
    expect(week.start).toBe(dayjs('2026-11-02').startOf('day').toISOString())
    expect(week.end).toBe(dayjs('2026-11-09').startOf('day').toISOString())
  })

  it('extracts all-day dates from UTC strings', () => {
    expect(allDayDate('2026-11-05T00:00:00Z')).toBe('2026-11-05')
    expect(
      scheduleDateKey({
        all_day: true,
        start_at: '2026-11-05T00:00:00Z',
      }),
    ).toBe('2026-11-05')
  })

  it('groups search results by local date and sorts items', () => {
    const first = makeSchedule({ id: 1, title: '上午', start_at: '2026-11-05T01:00:00Z' })
    const second = makeSchedule({ id: 2, title: '下午', start_at: '2026-11-05T08:00:00Z' })
    const allDay = makeSchedule({
      id: 3,
      title: '全天',
      all_day: true,
      start_at: '2026-11-05T00:00:00Z',
      end_at: '2026-11-05T23:59:59.999999Z',
    })

    const groups = groupSchedulesByDate([second, allDay, first])

    expect(groups).toHaveLength(1)
    expect(groups[0].items.map((item) => item.title)).toEqual(['全天', '上午', '下午'])
    expect(groups[0].label).toBe(formatDayTitle('2026-11-05'))
  })
})
