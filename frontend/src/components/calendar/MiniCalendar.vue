<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

import { fetchSchedules } from '@/api/schedules'
import { CATEGORY_META } from '@/constants/schedule'
import { useScheduleStore } from '@/stores/schedule'
import type { ScheduleCategory } from '@/types/schedule'
import { formatMonthTitle, scheduleDateKey } from '@/utils/date'

const props = defineProps<{
  currentDate: string
}>()

const emit = defineEmits<{
  select: [date: string]
}>()

const store = useScheduleStore()
const cursor = ref(dayjs(props.currentDate).startOf('month'))
const categoryMap = ref<Record<string, ScheduleCategory[]>>({})
let requestToken = 0

const weekdayLabels = ['一', '二', '三', '四', '五', '六', '日']

watch(
  () => props.currentDate,
  (value) => {
    cursor.value = dayjs(value).startOf('month')
  },
)

watch(
  [cursor, () => store.revision],
  () => {
    void loadCounts()
  },
  { immediate: true },
)

async function loadCounts() {
  const token = ++requestToken
  const start = cursor.value.startOf('month')
  const end = start.add(1, 'month')
  try {
    const schedules = await fetchSchedules({
      start: start.toISOString(),
      end: end.toISOString(),
    })
    if (token !== requestToken) {
      return
    }
    const map: Record<string, ScheduleCategory[]> = {}
    for (const schedule of schedules) {
      const key = scheduleDateKey(schedule)
      const categories = map[key] ?? []
      if (!categories.includes(schedule.category)) {
        categories.push(schedule.category)
      }
      map[key] = categories
    }
    categoryMap.value = map
  } catch {
    if (token === requestToken) {
      categoryMap.value = {}
    }
  }
}

const todayKey = dayjs().format('YYYY-MM-DD')
const selectedKey = computed(() => dayjs(props.currentDate).format('YYYY-MM-DD'))

interface MiniDay {
  key: string
  day: number
  inMonth: boolean
  isToday: boolean
  isSelected: boolean
  categories: ScheduleCategory[]
}

const days = computed<MiniDay[]>(() => {
  const monthStart = cursor.value.startOf('month')
  const offset = (monthStart.day() + 6) % 7
  const gridStart = monthStart.subtract(offset, 'day')

  return Array.from({ length: 42 }, (_, index) => {
    const value = gridStart.add(index, 'day')
    const key = value.format('YYYY-MM-DD')
    return {
      key,
      day: value.date(),
      inMonth: value.month() === monthStart.month(),
      isToday: key === todayKey,
      isSelected: key === selectedKey.value,
      categories: categoryMap.value[key] ?? [],
    }
  })
})

function changeMonth(offset: number) {
  cursor.value = cursor.value.add(offset, 'month')
}

function resetMonth() {
  cursor.value = dayjs().startOf('month')
}

function selectDay(day: MiniDay) {
  emit('select', day.key)
  if (!day.inMonth) {
    cursor.value = dayjs(day.key).startOf('month')
  }
}
</script>

<template>
  <section
    class="mini-calendar rounded-xl border border-line bg-surface px-3.5 pb-3 pt-3.5"
    aria-label="小型月历"
  >
    <div class="mini-calendar__header mb-2.5 flex items-center justify-between gap-1.5">
      <button
        type="button"
        class="inline-flex h-7 min-w-7 cursor-pointer items-center justify-center rounded-md border-0 bg-transparent p-0 text-ink-muted hover:bg-canvas hover:text-ink"
        aria-label="上个月"
        @click="changeMonth(-1)"
      >
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <button
        type="button"
        class="mini-calendar__title flex-1 border-0 bg-transparent p-0 font-display text-sm font-semibold text-ink"
        title="回到本月"
        @click="resetMonth"
      >
        {{ formatMonthTitle(cursor) }}
      </button>
      <button
        type="button"
        class="inline-flex h-7 min-w-7 cursor-pointer items-center justify-center rounded-md border-0 bg-transparent p-0 text-ink-muted hover:bg-canvas hover:text-ink"
        aria-label="下个月"
        @click="changeMonth(1)"
      >
        <el-icon><ArrowRight /></el-icon>
      </button>
    </div>

    <div
      class="mini-calendar__weekdays mb-1 grid grid-cols-7 text-center text-[10px] text-ink-muted"
      aria-hidden="true"
    >
      <span v-for="label in weekdayLabels" :key="label">{{ label }}</span>
    </div>

    <div class="mini-calendar__grid grid grid-cols-7" role="grid" aria-label="选择日期">
      <button
        v-for="day in days"
        :key="day.key"
        type="button"
        role="gridcell"
        class="mini-calendar__day relative flex h-8 min-w-0 cursor-pointer flex-col items-center justify-center rounded-[7px] border-0 p-0 hover:bg-canvas max-md:h-11"
        :class="[
          day.isSelected
            ? 'is-selected bg-canvas shadow-[inset_0_0_0_1px_var(--color-line-strong)]'
            : 'bg-transparent',
          !day.inMonth ? 'is-outside text-ink-muted opacity-55' : 'text-ink-secondary',
          { 'is-today': day.isToday },
        ]"
        :aria-label="day.key"
        :aria-selected="day.isSelected"
        @click="selectDay(day)"
      >
        <span
          class="mini-calendar__number text-[11px] leading-none tabular-nums"
          :class="day.isToday ? 'font-bold text-focus' : ''"
        >
          {{ day.day }}
        </span>
        <span
          v-if="day.categories.length"
          class="mini-calendar__dots absolute bottom-0.5 flex gap-0.5"
          aria-hidden="true"
        >
          <span
            v-for="category in day.categories.slice(0, 3)"
            :key="category"
            class="h-[3px] w-[3px] rounded-full"
            :class="CATEGORY_META[category].dotClass"
          ></span>
        </span>
      </button>
    </div>
  </section>
</template>
