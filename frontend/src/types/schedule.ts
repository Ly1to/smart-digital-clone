export type ScheduleCategory = 'work' | 'outing' | 'private'
export type ScheduleStatus = 'pending' | 'completed' | 'cancelled'
export type StagedStatus = 'pending' | 'approved' | 'rejected'
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
  source?: string
  source_ref?: string | null
  source_url?: string | null
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

export interface StagedSchedule {
  id: number
  source: string
  source_ref: string
  source_url: string | null
  source_meta: Record<string, unknown> | null
  title: string
  category: ScheduleCategory
  description: string | null
  start_at: string | null
  end_at: string | null
  all_day: boolean
  location: string | null
  status: StagedStatus
  schedule_id: number | null
  created_at: string
  updated_at: string
  approved_at: string | null
}

export interface StagedScheduleInput {
  title?: string
  category?: ScheduleCategory
  description?: string | null
  start_at?: string | null
  end_at?: string | null
  all_day?: boolean
  location?: string | null
}

export interface GithubStatus {
  configured: boolean
  username: string
  lookback_days: number
  token_configured: boolean
}

export interface GithubSyncResult {
  configured: boolean
  scanned_events: number
  created: number
  updated: number
  skipped: number
  no_slot: number
  message: string
}

export interface StagedApproveResult {
  staged: StagedSchedule
  schedule: Schedule
}

export interface StagedApproveAllResult {
  approved: Schedule[]
  skipped: StagedSchedule[]
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
