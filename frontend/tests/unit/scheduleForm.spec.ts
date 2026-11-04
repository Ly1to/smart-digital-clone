import dayjs from 'dayjs'
import { describe, expect, it } from 'vitest'

import type { Schedule } from '@/types/schedule'
import {
  buildSchedulePayload,
  createEmptyFormState,
  formStateFromSchedule,
  isTimeRangeValid,
  serializeFormState,
} from '@/utils/scheduleForm'

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

describe('schedule form utils', () => {
  it('creates a valid empty form with a one-hour default range', () => {
    const form = createEmptyFormState()

    expect(form.title).toBe('')
    expect(form.category).toBe('')
    expect(form.status).toBe('pending')
    expect(form.allDay).toBe(false)
    expect(form.startDate).toBe(form.endDate)
    expect(isTimeRangeValid(form)).toBe(true)
  })

  it('uses the provided create range', () => {
    const form = createEmptyFormState('2026-11-05T09:00:00', '2026-11-05T10:30:00')

    expect(form.startAt).toBe('2026-11-05T09:00:00')
    expect(form.endAt).toBe('2026-11-05T10:30:00')
    expect(form.startDate).toBe('2026-11-05')
    expect(form.endDate).toBe('2026-11-05')
  })

  it('prefills a timed schedule in local time', () => {
    const form = formStateFromSchedule(makeSchedule())

    expect(form.title).toBe('项目周会')
    expect(form.category).toBe('work')
    expect(form.startAt).toBe(dayjs('2026-11-05T06:00:00Z').format('YYYY-MM-DDTHH:mm:ss'))
    expect(form.endAt).toBe(dayjs('2026-11-05T07:00:00Z').format('YYYY-MM-DDTHH:mm:ss'))
  })

  it('prefills an all-day schedule as inclusive UTC dates', () => {
    const form = formStateFromSchedule(
      makeSchedule({
        all_day: true,
        start_at: '2026-11-05T00:00:00Z',
        end_at: '2026-11-06T23:59:59.999999Z',
      }),
    )

    expect(form.allDay).toBe(true)
    expect(form.startDate).toBe('2026-11-05')
    expect(form.endDate).toBe('2026-11-06')
  })

  it('rejects equal and reversed timed ranges but allows same-day all-day events', () => {
    const form = createEmptyFormState('2026-11-05T09:00:00', '2026-11-05T09:00:00')
    expect(isTimeRangeValid(form)).toBe(false)

    form.endAt = '2026-11-05T08:00:00'
    expect(isTimeRangeValid(form)).toBe(false)

    form.allDay = true
    form.startDate = '2026-11-05'
    form.endDate = '2026-11-05'
    expect(isTimeRangeValid(form)).toBe(true)

    form.endDate = '2026-11-04'
    expect(isTimeRangeValid(form)).toBe(false)
  })

  it('builds a trimmed payload with UTC times and nullable optionals', () => {
    const form = createEmptyFormState('2026-11-05T09:00:00', '2026-11-05T10:00:00')
    form.title = '  自主学习  '
    form.category = 'private'
    form.description = '  '
    form.location = ' 图书馆 '

    const payload = buildSchedulePayload(form)

    expect(payload).toMatchObject({
      title: '自主学习',
      category: 'private',
      description: null,
      location: '图书馆',
      all_day: false,
      status: 'pending',
      start_at: dayjs('2026-11-05T09:00:00').toISOString(),
      end_at: dayjs('2026-11-05T10:00:00').toISOString(),
    })
  })

  it('sends all-day events as UTC date anchors', () => {
    const form = createEmptyFormState()
    form.title = '旅行'
    form.category = 'outing'
    form.allDay = true
    form.startDate = '2026-11-05'
    form.endDate = '2026-11-06'

    const payload = buildSchedulePayload(form)

    expect(payload.start_at).toBe('2026-11-05T00:00:00Z')
    expect(payload.end_at).toBe('2026-11-06T00:00:00Z')
    expect(payload.all_day).toBe(true)
  })

  it('refuses to build an invalid range', () => {
    const form = createEmptyFormState('2026-11-05T10:00:00', '2026-11-05T09:00:00')
    form.title = '错误'
    form.category = 'work'

    expect(() => buildSchedulePayload(form)).toThrow('结束时间必须晚于开始时间')
  })

  it('serializes form state for dirty comparison', () => {
    const form = createEmptyFormState('2026-11-05T09:00:00', '2026-11-05T10:00:00')
    const snapshot = serializeFormState(form)
    form.title = '改动'

    expect(serializeFormState(form)).not.toBe(snapshot)
  })
})
