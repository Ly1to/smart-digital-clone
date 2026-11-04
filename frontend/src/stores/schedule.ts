import { defineStore } from 'pinia'

import * as scheduleApi from '@/api/schedules'
import { ALL_CATEGORIES, ALL_STATUSES, CATEGORY_META, STATUS_META } from '@/constants/schedule'
import type {
  CalendarRange,
  Schedule,
  ScheduleCategory,
  ScheduleFilters,
  ScheduleInput,
} from '@/types/schedule'
import { buildQueryWindow, compareSchedules, localDayRange } from '@/utils/date'
import { getErrorMessage } from '@/utils/error'

interface ScheduleState {
  schedules: Schedule[]
  countSchedules: Schedule[]
  daySchedules: Schedule[]
  loading: boolean
  dayLoading: boolean
  initialized: boolean
  error: string
  dayError: string
  visibleRange: CalendarRange | null
  filters: ScheduleFilters
  fetchToken: number
  dayFetchToken: number
  revision: number
}

export function createDefaultFilters(): ScheduleFilters {
  return {
    categories: [...ALL_CATEGORIES],
    statuses: [...ALL_STATUSES],
    dateRange: null,
  }
}

function filterParams(filters: ScheduleFilters) {
  return {
    categories: filters.categories.length ? filters.categories.join(',') : undefined,
    statuses: filters.statuses.length ? filters.statuses.join(',') : undefined,
  }
}

export const useScheduleStore = defineStore('schedule', {
  state: (): ScheduleState => ({
    schedules: [],
    countSchedules: [],
    daySchedules: [],
    loading: false,
    dayLoading: false,
    initialized: false,
    error: '',
    dayError: '',
    visibleRange: null,
    filters: createDefaultFilters(),
    fetchToken: 0,
    dayFetchToken: 0,
    revision: 0,
  }),

  getters: {
    hasActiveFilters(state): boolean {
      return (
        state.filters.categories.length !== ALL_CATEGORIES.length ||
        state.filters.statuses.length !== ALL_STATUSES.length ||
        state.filters.dateRange !== null
      )
    },

    categoryCounts(state): Record<ScheduleCategory, number> {
      const counts: Record<ScheduleCategory, number> = { work: 0, outing: 0, private: 0 }
      for (const schedule of state.countSchedules) {
        counts[schedule.category] += 1
      }
      return counts
    },

    activeFilterSummary(state): string {
      const parts: string[] = []
      if (state.filters.categories.length !== ALL_CATEGORIES.length) {
        parts.push(
          state.filters.categories.length
            ? state.filters.categories.map((item) => CATEGORY_META[item].label).join('、')
            : '无分类',
        )
      }
      if (state.filters.statuses.length !== ALL_STATUSES.length) {
        parts.push(
          state.filters.statuses.length
            ? state.filters.statuses.map((item) => STATUS_META[item].label).join('、')
            : '无状态',
        )
      }
      if (state.filters.dateRange) {
        parts.push(`${state.filters.dateRange[0]} 至 ${state.filters.dateRange[1]}`)
      }
      return parts.join(' · ')
    },
  },

  actions: {
    async fetchSchedules() {
      const token = ++this.fetchToken
      const window = buildQueryWindow(this.filters, this.visibleRange)
      this.loading = true
      this.error = ''

      try {
        const schedules = await scheduleApi.fetchSchedules({
          ...window,
          ...filterParams(this.filters),
        })
        if (token === this.fetchToken) {
          this.schedules = schedules
        }
      } catch (error) {
        if (token === this.fetchToken) {
          this.error = getErrorMessage(error)
          this.schedules = []
        }
      } finally {
        if (token === this.fetchToken) {
          this.loading = false
          this.initialized = true
        }
      }
    },

    async fetchCategoryCounts() {
      const window = buildQueryWindow(this.filters, this.visibleRange)
      try {
        this.countSchedules = await scheduleApi.fetchSchedules(window)
      } catch {
        // 分类计数是辅助信息，失败时保留上一次结果。
      }
    },

    async fetchDaySchedules(date: string) {
      const token = ++this.dayFetchToken
      const window = localDayRange(date)
      this.dayLoading = true
      this.dayError = ''

      try {
        const schedules = await scheduleApi.fetchSchedules({
          ...window,
          ...filterParams(this.filters),
        })
        if (token === this.dayFetchToken) {
          this.daySchedules = schedules.sort(compareSchedules)
        }
      } catch (error) {
        if (token === this.dayFetchToken) {
          this.daySchedules = []
          this.dayError = getErrorMessage(error)
        }
      } finally {
        if (token === this.dayFetchToken) {
          this.dayLoading = false
        }
      }
    },

    async refreshAll(date: string) {
      await Promise.all([
        this.fetchSchedules(),
        this.fetchDaySchedules(date),
        this.fetchCategoryCounts(),
      ])
    },

    async setVisibleRange(range: CalendarRange) {
      this.visibleRange = range
      await Promise.all([this.fetchSchedules(), this.fetchCategoryCounts()])
    },

    async applyFilters(filters: ScheduleFilters, dayDate: string) {
      this.filters = {
        categories: [...filters.categories],
        statuses: [...filters.statuses],
        dateRange: filters.dateRange ? [...filters.dateRange] : null,
      }
      await this.refreshAll(dayDate)
    },

    async resetFilters(dayDate: string) {
      this.filters = createDefaultFilters()
      await this.refreshAll(dayDate)
    },

    async createSchedule(payload: ScheduleInput, dayDate: string) {
      const schedule = await scheduleApi.createSchedule(payload)
      this.revision += 1
      await this.refreshAll(dayDate)
      return schedule
    },

    async updateSchedule(id: number, payload: ScheduleInput, dayDate: string) {
      const schedule = await scheduleApi.updateSchedule(id, payload)
      this.revision += 1
      await this.refreshAll(dayDate)
      return schedule
    },

    async removeSchedule(id: number) {
      await scheduleApi.deleteSchedule(id)
      this.schedules = this.schedules.filter((schedule) => schedule.id !== id)
      this.countSchedules = this.countSchedules.filter((schedule) => schedule.id !== id)
      this.daySchedules = this.daySchedules.filter((schedule) => schedule.id !== id)
      this.revision += 1
    },
  },
})
