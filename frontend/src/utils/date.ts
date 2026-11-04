import dayjs, { type Dayjs } from 'dayjs'

import type { CalendarRange, Schedule, ScheduleFilters, SearchGroup } from '@/types/schedule'

const WEEKDAYS = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']

/** 将本地时间字符串转换为 UTC ISO 字符串。 */
export function toUtcIso(localDateTime: string): string {
  return dayjs(localDateTime).toISOString()
}

export function formatLocalDateTime(iso: string): string {
  return dayjs(iso).format('YYYY-MM-DD HH:mm')
}

/** 全天事件日期按后端的 UTC 日期分量读取，避免时区换算跨天。 */
export function allDayDate(iso: string): string {
  return iso.slice(0, 10)
}

export function formatMonthTitle(date: string | Dayjs): string {
  return dayjs(date).format('YYYY 年 M 月')
}

export function formatDayTitle(date: string | Dayjs): string {
  const value = dayjs(date)
  return `${value.format('M 月 D 日')} ${WEEKDAYS[value.day()]}`
}

export function formatShortDate(date: string | Dayjs): string {
  return dayjs(date).format('M 月 D 日')
}

export function formatScheduleDate(
  schedule: Pick<Schedule, 'start_at' | 'end_at' | 'all_day'>,
): string {
  if (schedule.all_day) {
    const startDate = allDayDate(schedule.start_at)
    const endDate = allDayDate(schedule.end_at)
    return startDate === endDate ? startDate : `${startDate} 至 ${endDate}`
  }
  return dayjs(schedule.start_at).format('YYYY-MM-DD')
}

export function formatScheduleTime(
  schedule: Pick<Schedule, 'start_at' | 'end_at' | 'all_day'>,
): string {
  if (schedule.all_day) {
    return '全天'
  }

  const start = dayjs(schedule.start_at)
  const end = dayjs(schedule.end_at)
  if (start.isSame(end, 'day')) {
    return `${start.format('HH:mm')}–${end.format('HH:mm')}`
  }
  return `${start.format('YYYY-MM-DD HH:mm')} – ${end.format('YYYY-MM-DD HH:mm')}`
}

export function formatAgendaTime(
  schedule: Pick<Schedule, 'start_at' | 'end_at' | 'all_day'>,
): string {
  return schedule.all_day ? '全天' : dayjs(schedule.start_at).format('HH:mm')
}

export function scheduleDateKey(schedule: Pick<Schedule, 'start_at' | 'all_day'>): string {
  return schedule.all_day
    ? allDayDate(schedule.start_at)
    : dayjs(schedule.start_at).format('YYYY-MM-DD')
}

export function compareSchedules(a: Schedule, b: Schedule): number {
  if (a.all_day !== b.all_day) {
    return a.all_day ? -1 : 1
  }
  const startDiff = dayjs(a.start_at).valueOf() - dayjs(b.start_at).valueOf()
  return startDiff !== 0 ? startDiff : a.id - b.id
}

export function groupSchedulesByDate(schedules: Schedule[]): SearchGroup[] {
  const groups = new Map<string, Schedule[]>()
  for (const schedule of schedules) {
    const key = scheduleDateKey(schedule)
    const existing = groups.get(key) ?? []
    existing.push(schedule)
    groups.set(key, existing)
  }

  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([date, items]) => ({
      date,
      label: formatDayTitle(date),
      items: items.sort(compareSchedules),
    }))
}

/** 本地整天范围，转换为 UTC 后用于接口查询。 */
export function localDayRange(date: string | Dayjs): CalendarRange {
  const start = dayjs(date).startOf('day')
  return {
    start: start.toISOString(),
    end: start.add(1, 'day').toISOString(),
  }
}

/** 本地一周范围（周一到周日），开始和结束都转换为 UTC ISO。 */
export function localWeekRange(date: string | Dayjs = dayjs()): CalendarRange {
  const value = dayjs(date)
  const offset = value.day() === 0 ? 6 : value.day() - 1
  const start = value.subtract(offset, 'day').startOf('day')
  return {
    start: start.toISOString(),
    end: start.add(7, 'day').toISOString(),
  }
}

/** 查询窗口：显式日期筛选优先，否则使用日历当前可见范围。 */
export function buildQueryWindow(
  filters: ScheduleFilters,
  visibleRange: CalendarRange | null,
): { start?: string; end?: string } {
  if (filters.dateRange) {
    const [start, end] = filters.dateRange
    return {
      start: dayjs(start).startOf('day').toISOString(),
      end: dayjs(end).add(1, 'day').startOf('day').toISOString(),
    }
  }
  if (!visibleRange) {
    return {}
  }
  return {
    start: dayjs(visibleRange.start).toISOString(),
    end: dayjs(visibleRange.end).toISOString(),
  }
}
