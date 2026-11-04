export type ScheduleCategory = 'work' | 'outing' | 'private'
export type ScheduleStatus = 'pending' | 'completed' | 'cancelled'
export type CalendarView = 'month' | 'week' | 'day'
export type AppView = CalendarView | 'agenda'

export interface Schedule {
  id: number
  title: string
  category: ScheduleCategory
  description: string | null
  start_at: string
  end_at: string
  all_day: boolean
  location: string | null
  status: ScheduleStatus
  created_at: string
  updated_at: string
}

export interface ScheduleInput {
  title: string
  category: ScheduleCategory
  description: string | null
  start_at: string
  end_at: string
  all_day: boolean
  location: string | null
  status: ScheduleStatus
}

export interface ScheduleQuery {
  start?: string
  end?: string
  categories?: string
  statuses?: string
  keyword?: string
}

export interface ScheduleFilters {
  categories: ScheduleCategory[]
  statuses: ScheduleStatus[]
  dateRange: [string, string] | null
}

export interface CalendarRange {
  start: string
  end: string
}

export interface SearchGroup {
  date: string
  label: string
  items: Schedule[]
}
