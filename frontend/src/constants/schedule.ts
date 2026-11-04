import type { ScheduleCategory, ScheduleStatus } from '@/types/schedule'

export interface CategoryMeta {
  label: string
  shortLabel: string
  color: string
  softColor: string
}

export const ALL_CATEGORIES: ScheduleCategory[] = ['work', 'outing', 'private']

export const CATEGORY_META: Record<ScheduleCategory, CategoryMeta> = {
  work: {
    label: '工作',
    shortLabel: '工',
    color: '#356e84',
    softColor: '#e7eff2',
  },
  outing: {
    label: '外出',
    shortLabel: '外',
    color: '#bc6745',
    softColor: '#f6e8e0',
  },
  private: {
    label: '私人时间',
    shortLabel: '私',
    color: '#75608a',
    softColor: '#eee9f2',
  },
}

export const ALL_STATUSES: ScheduleStatus[] = ['pending', 'completed', 'cancelled']

export const STATUS_META: Record<
  ScheduleStatus,
  { label: string; icon: string; className: string }
> = {
  pending: { label: '待进行', icon: '', className: 'status-pending' },
  completed: { label: '已完成', icon: '✓', className: 'status-completed' },
  cancelled: { label: '已取消', icon: '×', className: 'status-cancelled' },
}

export const VIEW_LABELS = {
  month: '月',
  week: '周',
  day: '日',
  agenda: '今日',
} as const
