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
  <section class="mini-calendar" aria-label="小型月历">
    <div class="mini-calendar__header">
      <button type="button" aria-label="上个月" @click="changeMonth(-1)">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <button type="button" class="mini-calendar__title" title="回到本月" @click="resetMonth">
        {{ formatMonthTitle(cursor) }}
      </button>
      <button type="button" aria-label="下个月" @click="changeMonth(1)">
        <el-icon><ArrowRight /></el-icon>
      </button>
    </div>

    <div class="mini-calendar__weekdays" aria-hidden="true">
      <span v-for="label in weekdayLabels" :key="label">{{ label }}</span>
    </div>

    <div class="mini-calendar__grid" role="grid" aria-label="选择日期">
      <button
        v-for="day in days"
        :key="day.key"
        type="button"
        role="gridcell"
        class="mini-calendar__day"
        :class="{
          'is-outside': !day.inMonth,
          'is-today': day.isToday,
          'is-selected': day.isSelected,
        }"
        :aria-label="day.key"
        :aria-selected="day.isSelected"
        @click="selectDay(day)"
      >
        <span class="mini-calendar__number">{{ day.day }}</span>
        <span v-if="day.categories.length" class="mini-calendar__dots" aria-hidden="true">
          <span
            v-for="category in day.categories.slice(0, 3)"
            :key="category"
            :style="{ backgroundColor: CATEGORY_META[category].color }"
          ></span>
        </span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.mini-calendar {
  padding: 14px 14px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: 12px;
}

.mini-calendar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 10px;
}

.mini-calendar__header button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0;
  color: var(--color-ink-muted);
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
}

.mini-calendar__header button:hover {
  color: var(--color-ink);
  background: var(--color-canvas);
}

.mini-calendar__header button:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 1px;
}

.mini-calendar__title {
  flex: 1;
  color: var(--color-ink);
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
}

.mini-calendar__weekdays,
.mini-calendar__grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.mini-calendar__weekdays {
  margin-bottom: 4px;
  color: var(--color-ink-muted);
  font-size: 10px;
  text-align: center;
}

.mini-calendar__day {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 0;
  height: 32px;
  padding: 0;
  color: var(--color-ink-secondary);
  background: transparent;
  border: 0;
  border-radius: 7px;
  cursor: pointer;
}

.mini-calendar__day:hover {
  background: var(--color-canvas);
}

.mini-calendar__day:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: -2px;
}

.mini-calendar__day.is-outside {
  color: var(--color-ink-muted);
  opacity: 0.55;
}

.mini-calendar__day.is-today .mini-calendar__number {
  color: var(--color-focus);
  font-weight: 700;
}

.mini-calendar__day.is-selected {
  background: var(--color-canvas);
  box-shadow: inset 0 0 0 1px var(--color-line-strong);
}

.mini-calendar__number {
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.mini-calendar__dots {
  position: absolute;
  bottom: 2px;
  display: flex;
  gap: 2px;
}

.mini-calendar__dots span {
  width: 3px;
  height: 3px;
  border-radius: 50%;
}
</style>
