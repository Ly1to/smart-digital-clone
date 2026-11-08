<script setup lang="ts">
import { computed } from 'vue'
import dayjs from 'dayjs'

import EmptyState from '@/components/common/EmptyState.vue'
import { CATEGORY_META, STATUS_META } from '@/constants/schedule'
import type { Schedule } from '@/types/schedule'
import { compareSchedules, formatAgendaTime, formatDayTitle } from '@/utils/date'

const props = withDefaults(
  defineProps<{
    date: string
    schedules: Schedule[]
    loading?: boolean
    pendingCount?: number
    showStagingButton?: boolean
  }>(),
  {
    loading: false,
    pendingCount: 0,
    showStagingButton: false,
  },
)

const emit = defineEmits<{
  select: [schedule: Schedule]
  create: []
  openStaging: []
}>()

const items = computed(() => [...props.schedules].sort(compareSchedules))
const isEmpty = computed(() => !props.loading && items.value.length === 0)
const isToday = computed(() => dayjs(props.date).isSame(dayjs(), 'day'))
</script>

<template>
  <section class="agenda" aria-label="当天日程">
    <header class="agenda__header">
      <div>
        <p class="agenda__eyebrow">{{ isToday ? '今日安排' : '当天安排' }}</p>
        <h2>{{ formatDayTitle(props.date) }}</h2>
      </div>
      <div class="agenda__meta">
        <button
          v-if="props.showStagingButton"
          type="button"
          class="agenda__staging"
          @click="emit('openStaging')"
        >
          暂存
          <span v-if="props.pendingCount">{{ props.pendingCount }}</span>
        </button>
        <span class="agenda__count">
          {{ props.loading ? '加载中' : `${items.length} 项` }}
        </span>
      </div>
    </header>
    <div v-if="props.loading" class="agenda__loading">
      <span v-for="index in 3" :key="index" class="agenda__skeleton"></span>
    </div>

    <div v-else-if="isEmpty" class="agenda__empty">
      <EmptyState
        :title="isToday ? '今天还没有安排' : '这一天还没有安排'"
        description="留白也是日程的一部分，需要时再添加。"
        action-label="新建日程"
        @action="emit('create')"
      />
    </div>

    <ol v-else class="agenda__list">
      <li v-for="item in items" :key="item.id">
        <button
          type="button"
          class="agenda-item"
          :class="[STATUS_META[item.status].className]"
          @click="emit('select', item)"
        >
          <span class="agenda-item__time">{{ formatAgendaTime(item) }}</span>
          <span
            class="agenda-item__marker"
            :style="{
              color: CATEGORY_META[item.category].color,
              backgroundColor: CATEGORY_META[item.category].softColor,
            }"
            aria-hidden="true"
          >
            {{ CATEGORY_META[item.category].shortLabel }}
          </span>
          <span class="agenda-item__body">
            <span class="agenda-item__title">
              <span
                v-if="STATUS_META[item.status].icon"
                class="agenda-item__status"
                aria-hidden="true"
              >
                {{ STATUS_META[item.status].icon }}
              </span>
              {{ item.title }}
            </span>
            <span class="agenda-item__meta">
              {{ CATEGORY_META[item.category].label }}
              <template v-if="item.location"> · {{ item.location }}</template>
            </span>
          </span>
        </button>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.agenda {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.agenda__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 18px 14px;
  border-bottom: 1px solid var(--color-line);
}

.agenda__eyebrow {
  margin: 0 0 4px;
  color: var(--color-ink-muted);
  font-size: 11px;
  letter-spacing: 0.1em;
}

.agenda__header h2 {
  margin: 0;
  color: var(--color-ink);
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 600;
}

.agenda__count {
  flex: 0 0 auto;
  color: var(--color-ink-muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.agenda__meta {
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.agenda__staging {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  color: var(--color-focus);
  font-size: 11px;
  background: var(--color-canvas);
  border: 1px solid var(--color-line);
  border-radius: 999px;
  cursor: pointer;
}

.agenda__staging span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  color: var(--color-surface);
  font-size: 9px;
  background: var(--color-focus);
  border-radius: 999px;
}

.agenda__staging:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.agenda__loading {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
}

.agenda__skeleton {
  height: 52px;
  background: var(--color-canvas);
  border-radius: 8px;
  animation: pulse 1.4s ease-in-out infinite;
}

.agenda__empty {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
}

.agenda__list {
  flex: 1;
  padding: 8px 10px 16px;
  margin: 0;
  overflow-y: auto;
  list-style: none;
}

.agenda-item {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  width: 100%;
  padding: 10px 8px;
  text-align: left;
  background: transparent;
  border: 0;
  border-bottom: 1px dashed var(--color-line);
  border-radius: 7px;
  cursor: pointer;
}

.agenda-item:hover {
  background: var(--color-canvas);
}

.agenda-item:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: -2px;
}

.agenda-item__time {
  flex: 0 0 40px;
  padding-top: 2px;
  color: var(--color-ink-muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.agenda-item__marker {
  display: inline-flex;
  flex: 0 0 22px;
  align-items: center;
  justify-content: center;
  height: 22px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 6px;
}

.agenda-item__body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.agenda-item__title {
  overflow: hidden;
  color: var(--color-ink);
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agenda-item__status {
  margin-right: 3px;
  color: var(--color-success);
}

.agenda-item.status-cancelled {
  opacity: 0.6;
}

.agenda-item.status-cancelled .agenda-item__title {
  text-decoration: line-through;
}

.agenda-item.status-completed .agenda-item__title {
  color: var(--color-ink-secondary);
}

.agenda-item__meta {
  overflow: hidden;
  color: var(--color-ink-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.65;
  }
  50% {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .agenda__skeleton {
    animation: none;
  }
}
</style>
