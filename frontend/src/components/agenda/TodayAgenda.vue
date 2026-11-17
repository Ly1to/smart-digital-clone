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
  <section class="agenda flex h-full min-h-0 flex-col" aria-label="当天日程">
    <header
      class="agenda__header flex items-start justify-between gap-3 border-b border-line px-5 pb-4 pt-5"
    >
      <div>
        <p
          class="agenda__eyebrow mb-1.5 text-[10px] font-medium uppercase tracking-[0.2em] text-ink-muted"
        >
          {{ isToday ? '今日安排' : '当天安排' }}
        </p>
        <h2
          class="m-0 font-display text-[21px] font-semibold leading-tight tracking-[-0.01em] text-ink"
        >
          {{ formatDayTitle(props.date) }}
        </h2>
      </div>
      <div class="agenda__meta flex shrink-0 flex-col items-end gap-2">
        <button
          v-if="props.showStagingButton"
          type="button"
          class="agenda__staging inline-flex min-h-[30px] cursor-pointer items-center gap-[5px] rounded-full border border-outing/25 bg-outing-soft px-2.5 text-[11px] text-outing transition-colors hover:border-outing/45"
          @click="emit('openStaging')"
        >
          暂存
          <span
            v-if="props.pendingCount"
            class="inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-outing text-[9px] text-surface"
          >
            {{ props.pendingCount }}
          </span>
        </button>
        <span class="agenda__count shrink-0 text-xs tabular-nums text-ink-muted">
          {{ props.loading ? '加载中' : `${items.length} 项` }}
        </span>
      </div>
    </header>
    <div v-if="props.loading" class="agenda__loading flex flex-col gap-2.5 p-4">
      <span
        v-for="index in 3"
        :key="index"
        class="agenda__skeleton h-[52px] animate-pulse rounded-lg bg-canvas"
      ></span>
    </div>

    <div v-else-if="isEmpty" class="agenda__empty flex flex-1 items-center justify-center">
      <EmptyState
        :title="isToday ? '今天还没有安排' : '这一天还没有安排'"
        description="留白也是日程的一部分，需要时再添加。"
        action-label="新建日程"
        @action="emit('create')"
      />
    </div>

    <ol v-else class="agenda__list m-0 flex-1 list-none overflow-y-auto px-2.5 pb-4 pt-2">
      <li v-for="item in items" :key="item.id">
        <button
          type="button"
          class="agenda-item flex w-full cursor-pointer items-start gap-2.5 rounded-xl border-0 bg-transparent px-2.5 py-3 text-left transition-colors hover:bg-canvas"
          :class="[STATUS_META[item.status].className, STATUS_META[item.status].itemClass]"
          @click="emit('select', item)"
        >
          <span
            class="agenda-item__time flex-[0_0_42px] pt-0.5 text-[11px] tabular-nums text-ink-muted"
          >
            {{ formatAgendaTime(item) }}
          </span>
          <span
            class="agenda-item__marker inline-flex h-6 flex-[0_0_24px] items-center justify-center rounded-lg text-[10px] font-semibold"
            :class="CATEGORY_META[item.category].badgeClass"
            aria-hidden="true"
          >
            {{ CATEGORY_META[item.category].shortLabel }}
          </span>
          <span class="agenda-item__body flex min-w-0 flex-col gap-[3px]">
            <span
              class="agenda-item__title overflow-hidden text-ellipsis whitespace-nowrap text-[13px] font-medium leading-[1.4]"
              :class="STATUS_META[item.status].titleClass"
            >
              <span
                v-if="STATUS_META[item.status].icon"
                class="agenda-item__status mr-[3px] text-success"
                aria-hidden="true"
              >
                {{ STATUS_META[item.status].icon }}
              </span>
              {{ item.title }}
            </span>
            <span
              class="agenda-item__meta overflow-hidden text-ellipsis whitespace-nowrap text-[11px] text-ink-muted"
            >
              {{ CATEGORY_META[item.category].label }}
              <template v-if="item.location"> · {{ item.location }}</template>
            </span>
          </span>
        </button>
      </li>
    </ol>
  </section>
</template>
