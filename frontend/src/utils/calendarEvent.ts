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
  root.className = [
    'schedule-event__content',
    'flex min-w-0 items-start gap-1.5 overflow-hidden rounded-md border-l-[3px] px-1.5 py-[3px]',
    categoryMeta.softClass,
    categoryMeta.borderClass,
    statusMeta.eventItemClass,
    isTimeGrid ? 'flex-col gap-0.5 py-1' : '',
  ]
    .filter(Boolean)
    .join(' ')

  const marker = createSpan(
    [
      'schedule-event__marker',
      'shrink-0 pt-px text-[10px] font-bold leading-[1.3]',
      categoryMeta.textClass,
      isTimeGrid ? 'pt-0 text-[11px] leading-[1.2]' : '',
    ]
      .filter(Boolean)
      .join(' '),
    isTimeGrid ? categoryMeta.label : categoryMeta.shortLabel,
  )
  root.appendChild(marker)

  const main = document.createElement('span')
  main.className = 'schedule-event__main flex min-w-0 flex-col gap-px'

  const head = document.createElement('span')
  head.className = 'schedule-event__head flex min-w-0 items-baseline gap-1'
  if (!isTimeGrid && arg.timeText) {
    head.appendChild(
      createSpan(
        'schedule-event__time shrink-0 text-[10px] tabular-nums text-ink-muted max-md:hidden',
        arg.timeText,
      ),
    )
  }
  head.appendChild(
    createSpan(
      [
        'schedule-event__title',
        'overflow-hidden text-[12px] font-medium leading-[1.35] text-ellipsis whitespace-nowrap max-md:text-[11px]',
        statusMeta.eventTitleClass,
      ].join(' '),
      arg.event.title,
    ),
  )
  if (statusMeta.icon) {
    head.appendChild(
      createSpan('schedule-event__status shrink-0 text-[10px] text-success', statusMeta.icon),
    )
  }
  main.appendChild(head)

  if (isTimeGrid && arg.timeText) {
    main.appendChild(
      createSpan(
        'schedule-event__time shrink-0 text-[10px] tabular-nums text-ink-muted max-md:hidden',
        arg.timeText,
      ),
    )
  }

  const location = arg.event.extendedProps.location as string | null
  if (isTimeGrid && location) {
    main.appendChild(
      createSpan(
        'schedule-event__location overflow-hidden text-[10px] text-ellipsis whitespace-nowrap text-ink-muted',
        location,
      ),
    )
  }

  root.appendChild(main)

  return { domNodes: [root] }
}
