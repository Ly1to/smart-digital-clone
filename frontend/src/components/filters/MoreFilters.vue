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
  <details class="more-filters">
    <summary>更多筛选</summary>

    <div class="more-filters__body">
      <fieldset class="status-group">
        <legend>状态</legend>
        <button
          v-for="status in ALL_STATUSES"
          :key="status"
          type="button"
          class="status-pill"
          :class="[STATUS_META[status].className, { 'is-active': statuses.includes(status) }]"
          :aria-pressed="statuses.includes(status)"
          @click="toggleStatus(status)"
        >
          <span v-if="STATUS_META[status].icon" aria-hidden="true">
            {{ STATUS_META[status].icon }}
          </span>
          {{ STATUS_META[status].label }}
        </button>
      </fieldset>

      <label class="date-filter">
        <span>时间范围</span>
        <el-date-picker
          :model-value="store.filters.dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          range-separator="至"
          unlink-panels
          @update:model-value="updateDateRange"
        />
      </label>

      <button v-if="store.hasActiveFilters" type="button" class="clear-button" @click="clearAll">
        清除全部筛选
      </button>

      <p class="more-filters__hint">
        {{ store.activeFilterSummary || '未启用额外筛选' }}
      </p>
    </div>
  </details>
</template>

<style scoped>
.more-filters {
  border-top: 1px solid var(--color-line);
}

.more-filters summary {
  padding: 12px 4px 8px;
  color: var(--color-ink-secondary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  cursor: pointer;
  list-style: none;
}

.more-filters summary::-webkit-details-marker {
  display: none;
}

.more-filters summary::after {
  content: '+';
  float: right;
  color: var(--color-ink-muted);
  font-weight: 400;
}

.more-filters[open] summary::after {
  content: '−';
}

.more-filters summary:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.more-filters__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 2px 0 6px;
}

.status-group {
  padding: 0;
  margin: 0;
  border: 0;
}

.status-group legend,
.date-filter > span {
  display: block;
  margin-bottom: 6px;
  color: var(--color-ink-muted);
  font-size: 11px;
}

.status-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.status-group legend {
  width: 100%;
}

.status-pill {
  min-height: 30px;
  padding: 0 10px;
  color: var(--color-ink-muted);
  font-size: 12px;
  background: transparent;
  border: 1px solid var(--color-line);
  border-radius: 999px;
  cursor: pointer;
  opacity: 0.6;
}

.status-pill.is-active {
  color: var(--color-ink-secondary);
  background: var(--color-surface);
  opacity: 1;
}

.status-pill:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.status-pill.status-completed.is-active {
  color: var(--color-success);
  border-color: var(--color-success);
}

.status-pill.status-cancelled.is-active {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.date-filter :deep(.el-date-editor) {
  width: 100%;
}

.clear-button {
  align-self: flex-start;
  padding: 2px 0;
  color: var(--color-danger);
  font-size: 12px;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.clear-button:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.more-filters__hint {
  margin: 0;
  color: var(--color-ink-muted);
  font-size: 11px;
  line-height: 1.6;
}

@media (max-width: 767px) {
  .status-pill {
    min-height: 44px;
    padding: 0 14px;
  }
}
</style>
