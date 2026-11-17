<script setup lang="ts">
import { computed } from 'vue'

import { ALL_STATUSES, STATUS_META } from '@/constants/schedule'
import { useScheduleStore } from '@/stores/schedule'
import type { ScheduleStatus } from '@/types/schedule'

const props = defineProps<{
  dayDate: string
}>()

const store = useScheduleStore()
const statuses = computed(() => store.filters.statuses)

function toggleStatus(status: ScheduleStatus) {
  const selected = store.filters.statuses
  const next = selected.includes(status)
    ? selected.filter((item) => item !== status)
    : [...selected, status]
  void store.applyFilters({ ...store.filters, statuses: next }, props.dayDate)
}

function updateDateRange(value: [string, string] | null) {
  void store.applyFilters({ ...store.filters, dateRange: value }, props.dayDate)
}

function clearAll() {
  void store.resetFilters(props.dayDate)
}
</script>

<template>
  <details class="more-filters border-t border-line">
    <summary
      class="relative cursor-pointer list-none px-1 pb-2 pt-3 text-xs font-semibold tracking-[0.08em] text-ink-secondary after:absolute after:right-0 after:font-normal after:text-ink-muted after:content-['+'] open:after:content-['−'] [&::-webkit-details-marker]:hidden"
    >
      更多筛选
    </summary>

    <div class="more-filters__body flex flex-col gap-3 pb-1.5 pt-0.5">
      <fieldset class="status-group m-0 flex flex-wrap gap-1.5 border-0 p-0">
        <legend class="mb-1.5 w-full text-[11px] text-ink-muted">状态</legend>
        <button
          v-for="status in ALL_STATUSES"
          :key="status"
          type="button"
          class="status-pill min-h-[30px] cursor-pointer rounded-full border px-2.5 text-xs max-md:min-h-11 max-md:px-3.5"
          :class="
            statuses.includes(status)
              ? `bg-surface opacity-100 ${STATUS_META[status].pillActiveClass}`
              : 'border-line bg-transparent text-ink-muted opacity-60'
          "
          :aria-pressed="statuses.includes(status)"
          @click="toggleStatus(status)"
        >
          <span v-if="STATUS_META[status].icon" aria-hidden="true">
            {{ STATUS_META[status].icon }}
          </span>
          {{ STATUS_META[status].label }}
        </button>
      </fieldset>

      <label class="date-filter flex flex-col gap-1.5 text-[11px] text-ink-muted">
        <span>时间范围</span>
        <el-date-picker
          :model-value="store.filters.dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          range-separator="至"
          unlink-panels
          class="w-full!"
          @update:model-value="updateDateRange"
        />
      </label>

      <button
        v-if="store.hasActiveFilters"
        type="button"
        class="clear-button cursor-pointer self-start border-0 bg-transparent p-0 text-xs text-danger hover:underline"
        @click="clearAll"
      >
        清除全部筛选
      </button>

      <p class="more-filters__hint m-0 text-[11px] leading-relaxed text-ink-muted">
        {{ store.activeFilterSummary || '未启用额外筛选' }}
      </p>
    </div>
  </details>
</template>
