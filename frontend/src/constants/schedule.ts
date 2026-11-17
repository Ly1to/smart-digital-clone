import type { ScheduleCategory, ScheduleStatus } from '@/types/schedule'

export interface CategoryMeta {
  label: string
  shortLabel: string
  color: string
  softColor: string
  dotClass: string
  textClass: string
  softClass: string
  borderClass: string
  badgeClass: string
  activeCardClass: string
}

export const ALL_CATEGORIES: ScheduleCategory[] = ['work', 'outing', 'private']

export const CATEGORY_META: Record<ScheduleCategory, CategoryMeta> = {
  work: {
    label: '工作',
    shortLabel: '工',
    color: '#3f6c7d',
    softColor: '#e9eff1',
    dotClass: 'bg-work',
    textClass: 'text-work',
    softClass: 'bg-work-soft',
    borderClass: 'border-work',
    badgeClass: 'bg-work-soft text-work',
    activeCardClass: 'border-work bg-work-soft text-work',
  },
  outing: {
    label: '外出',
    shortLabel: '外',
    color: '#c96442',
    softColor: '#f9ede6',
    dotClass: 'bg-outing',
    textClass: 'text-outing',
    softClass: 'bg-outing-soft',
    borderClass: 'border-outing',
    badgeClass: 'bg-outing-soft text-outing',
    activeCardClass: 'border-outing bg-outing-soft text-outing',
  },
  private: {
    label: '私人时间',
    shortLabel: '私',
    color: '#7b6690',
    softColor: '#f0ebf5',
    dotClass: 'bg-private',
    textClass: 'text-private',
    softClass: 'bg-private-soft',
    borderClass: 'border-private',
    badgeClass: 'bg-private-soft text-private',
    activeCardClass: 'border-private bg-private-soft text-private',
  },
}

export const ALL_STATUSES: ScheduleStatus[] = ['pending', 'completed', 'cancelled']

export interface StatusMeta {
  label: string
  icon: string
  className: string
  itemClass: string
  titleClass: string
  badgeClass: string
  pillActiveClass: string
  eventItemClass: string
  eventTitleClass: string
}

export const STATUS_META: Record<ScheduleStatus, StatusMeta> = {
  pending: {
    label: '待进行',
    icon: '',
    className: 'status-pending',
    itemClass: '',
    titleClass: 'text-ink',
    badgeClass: 'bg-canvas text-ink-muted',
    pillActiveClass: 'border-line-strong text-ink-secondary',
    eventItemClass: '',
    eventTitleClass: 'text-ink',
  },
  completed: {
    label: '已完成',
    icon: '✓',
    className: 'status-completed',
    itemClass: '',
    titleClass: 'text-ink-secondary',
    badgeClass: 'bg-canvas text-success',
    pillActiveClass: 'border-success text-success',
    eventItemClass: '',
    eventTitleClass: 'text-ink-secondary',
  },
  cancelled: {
    label: '已取消',
    icon: '×',
    className: 'status-cancelled',
    itemClass: 'opacity-60',
    titleClass: 'text-ink-muted line-through',
    badgeClass: 'bg-canvas text-danger',
    pillActiveClass: 'border-danger text-danger',
    eventItemClass: 'opacity-60',
    eventTitleClass: 'text-ink-muted line-through',
  },
}

export const VIEW_LABELS = {
  month: '月',
  week: '周',
  day: '日',
  agenda: '今日',
} as const
