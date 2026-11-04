import type { EventContentArg, EventInput } from '@fullcalendar/core'

import { CATEGORY_META, STATUS_META } from '@/constants/schedule'
import type { Schedule } from '@/types/schedule'

/** API 日程到 FullCalendar 事件的统一适配层。 */
export function toCalendarEvent(schedule: Schedule): EventInput {
  return {
    id: String(schedule.id),
    title: schedule.title,
    start: schedule.start_at,
    end: schedule.end_at,
    allDay: schedule.all_day,
    classNames: [
      'schedule-event',
      `category-${schedule.category}`,
      `status-${schedule.status}`,
      ...(schedule.all_day ? ['is-all-day'] : []),
    ],
    extendedProps: {
      category: schedule.category,
      status: schedule.status,
      location: schedule.location,
      description: schedule.description,
    },
  }
}

function createSpan(className: string, text: string): HTMLSpanElement {
  const element = document.createElement('span')
  element.className = className
  element.textContent = text
  return element
}

/** FullCalendar 自定义事件内容：分类标记、时间、标题和状态。 */
export function renderEventContent(arg: EventContentArg): { domNodes: Node[] } {
  const category = arg.event.extendedProps.category as keyof typeof CATEGORY_META
  const status = arg.event.extendedProps.status as keyof typeof STATUS_META
  const categoryMeta = CATEGORY_META[category]
  const statusMeta = STATUS_META[status]
  const isTimeGrid = arg.view.type.startsWith('timeGrid')

  const root = document.createElement('div')
  root.className = `schedule-event__content${isTimeGrid ? ' is-timegrid' : ''}`

  const marker = createSpan(
    `schedule-event__marker${isTimeGrid ? ' is-full' : ''}`,
    isTimeGrid ? categoryMeta.label : categoryMeta.shortLabel,
  )
  root.appendChild(marker)

  const main = document.createElement('span')
  main.className = 'schedule-event__main'

  const head = document.createElement('span')
  head.className = 'schedule-event__head'
  if (!isTimeGrid && arg.timeText) {
    head.appendChild(createSpan('schedule-event__time', arg.timeText))
  }
  head.appendChild(createSpan('schedule-event__title', arg.event.title))
  if (statusMeta.icon) {
    head.appendChild(createSpan('schedule-event__status', statusMeta.icon))
  }
  main.appendChild(head)

  if (isTimeGrid && arg.timeText) {
    main.appendChild(createSpan('schedule-event__time', arg.timeText))
  }

  const location = arg.event.extendedProps.location as string | null
  if (isTimeGrid && location) {
    main.appendChild(createSpan('schedule-event__location', location))
  }

  root.appendChild(main)

  return { domNodes: [root] }
}
