import dayjs from 'dayjs'

import type { Schedule, ScheduleCategory, ScheduleInput, ScheduleStatus } from '@/types/schedule'

export interface ScheduleFormState {
  title: string
  category: ScheduleCategory | ''
  description: string
  startAt: string
  endAt: string
  startDate: string
  endDate: string
  allDay: boolean
  location: string
  status: ScheduleStatus
}

const DATE_TIME_FORMAT = 'YYYY-MM-DDTHH:mm:ss'
const DATE_FORMAT = 'YYYY-MM-DD'

export function createEmptyFormState(
  initialStart?: string | null,
  initialEnd?: string | null,
): ScheduleFormState {
  const start = initialStart ? dayjs(initialStart) : dayjs().add(1, 'hour').minute(0).second(0)
  const end = initialEnd ? dayjs(initialEnd) : start.add(1, 'hour')

  return {
    title: '',
    category: '',
    description: '',
    startAt: start.format(DATE_TIME_FORMAT),
    endAt: end.format(DATE_TIME_FORMAT),
    startDate: start.format(DATE_FORMAT),
    endDate: end.format(DATE_FORMAT),
    allDay: false,
    location: '',
    status: 'pending',
  }
}

export function formStateFromSchedule(schedule: Schedule): ScheduleFormState {
  const startDate = schedule.start_at.slice(0, 10)
  const endDate = schedule.end_at.slice(0, 10)

  return {
    title: schedule.title,
    category: schedule.category,
    description: schedule.description ?? '',
    startAt: schedule.all_day
      ? `${startDate}T09:00:00`
      : dayjs(schedule.start_at).format(DATE_TIME_FORMAT),
    endAt: schedule.all_day
      ? `${endDate}T10:00:00`
      : dayjs(schedule.end_at).format(DATE_TIME_FORMAT),
    startDate,
    endDate,
    allDay: schedule.all_day,
    location: schedule.location ?? '',
    status: schedule.status,
  }
}

export function isTimeRangeValid(form: ScheduleFormState): boolean {
  if (form.allDay) {
    return Boolean(form.startDate && form.endDate && form.endDate >= form.startDate)
  }
  if (!form.startAt || !form.endAt) {
    return false
  }
  return dayjs(form.endAt).isAfter(dayjs(form.startAt))
}

export function serializeFormState(form: ScheduleFormState): string {
  return JSON.stringify(form)
}

export function buildSchedulePayload(form: ScheduleFormState): ScheduleInput {
  const description = form.description.trim()
  const location = form.location.trim()

  let startAt: string
  let endAt: string
  if (form.allDay) {
    if (!form.startDate || !form.endDate) {
      throw new Error('请选择全天日期范围')
    }
    // 后端会把全天事件规范为开始日 00:00 至结束日 23:59:59.999999（UTC）。
    startAt = `${form.startDate}T00:00:00Z`
    endAt = `${form.endDate}T00:00:00Z`
  } else {
    startAt = dayjs(form.startAt).toISOString()
    endAt = dayjs(form.endAt).toISOString()
  }

  if (!isTimeRangeValid(form)) {
    throw new Error(form.allDay ? '结束日期不能早于开始日期' : '结束时间必须晚于开始时间')
  }

  return {
    title: form.title.trim(),
    category: form.category as ScheduleCategory,
    description: description || null,
    start_at: startAt,
    end_at: endAt,
    all_day: form.allDay,
    location: location || null,
    status: form.status,
  }
}
