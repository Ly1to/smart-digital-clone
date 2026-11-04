<script setup lang="ts">
import { computed, ref } from 'vue'
import dayjs from 'dayjs'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import zhCnLocale from '@fullcalendar/core/locales/zh-cn'
import type {
  Calendar,
  CalendarOptions,
  DatesSetArg,
  EventClickArg,
  EventInput,
} from '@fullcalendar/core'
import type { DateClickArg } from '@fullcalendar/interaction'

import type { CalendarView, Schedule } from '@/types/schedule'
import { formatScheduleTime } from '@/utils/date'
import { renderEventContent, toCalendarEvent } from '@/utils/calendarEvent'

const props = withDefaults(
  defineProps<{
    schedules: Schedule[]
    initialView?: CalendarView
  }>(),
  {
    initialView: 'week',
  },
)

const emit = defineEmits<{
  dateClick: [arg: DateClickArg]
  eventClick: [schedule: Schedule]
  datesSet: [
    range: {
      start: string
      end: string
      title: string
      view: CalendarView
      currentDate: string
    },
  ]
}>()

const wrapperRef = ref<{ getApi: () => Calendar }>()
const viewNames: Record<CalendarView, string> = {
  month: 'dayGridMonth',
  week: 'timeGridWeek',
  day: 'timeGridDay',
}

const events = computed<EventInput[]>(() => props.schedules.map(toCalendarEvent))

const options = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: viewNames[props.initialView],
  locale: zhCnLocale,
  headerToolbar: false,
  firstDay: 1,
  height: '100%',
  expandRows: true,
  nowIndicator: true,
  dayMaxEvents: 3,
  slotEventOverlap: false,
  allDayText: '全天',
  scrollTime: '08:00:00',
  slotMinTime: '00:00:00',
  slotMaxTime: '24:00:00',
  eventDisplay: 'block',
  eventShortHeight: 28,
  eventTimeFormat: {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  },
  events: events.value,
  eventContent: renderEventContent,
  eventDidMount: (info) => {
    const schedule = props.schedules.find((item) => String(item.id) === info.event.id)
    if (!schedule) {
      return
    }
    const parts = [
      `${schedule.title}（${schedule.category}）`,
      formatScheduleTime(schedule),
      schedule.location ?? '',
    ].filter(Boolean)
    info.el.setAttribute('title', parts.join('\n'))
  },
  eventClick: (info: EventClickArg) => {
    const schedule = props.schedules.find((item) => String(item.id) === info.event.id)
    if (schedule) {
      info.jsEvent.preventDefault()
      emit('eventClick', schedule)
    }
  },
  dateClick: (info: DateClickArg) => {
    emit('dateClick', info)
  },
  datesSet: (info: DatesSetArg) => {
    const viewType = info.view.type
    const view: CalendarView = viewType.startsWith('dayGrid')
      ? 'month'
      : viewType === 'timeGridDay'
        ? 'day'
        : 'week'
    emit('datesSet', {
      start: info.startStr,
      end: info.endStr,
      title: info.view.title,
      view,
      currentDate: dayjs(info.view.currentStart).format('YYYY-MM-DD'),
    })
  },
}))

function getApi(): Calendar | undefined {
  return wrapperRef.value?.getApi()
}

function goToDate(date: string) {
  getApi()?.gotoDate(date)
}

function next() {
  getApi()?.next()
}

function prev() {
  getApi()?.prev()
}

function today() {
  getApi()?.today()
}

function changeView(view: CalendarView) {
  getApi()?.changeView(viewNames[view])
}

function updateSize() {
  getApi()?.updateSize()
}

defineExpose({ goToDate, next, prev, today, changeView, updateSize })
</script>

<template>
  <FullCalendar ref="wrapperRef" :options="options" />
</template>
