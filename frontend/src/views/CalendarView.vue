<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Close, Plus } from '@element-plus/icons-vue'
import type { DateClickArg } from '@fullcalendar/interaction'

import AppShell from '@/components/layout/AppShell.vue'
import TopBar from '@/components/layout/TopBar.vue'
import CalendarCanvas from '@/components/calendar/CalendarCanvas.vue'
import MiniCalendar from '@/components/calendar/MiniCalendar.vue'
import CategoryFilter from '@/components/filters/CategoryFilter.vue'
import MoreFilters from '@/components/filters/MoreFilters.vue'
import TodayAgenda from '@/components/agenda/TodayAgenda.vue'
import ScheduleDetailPanel from '@/components/schedule/ScheduleDetailPanel.vue'
import ScheduleForm from '@/components/schedule/ScheduleForm.vue'
import StagingDrawer from '@/components/staging/StagingDrawer.vue'
import AccountPanel from '@/components/settings/AccountPanel.vue'
import ThemeSwitcher from '@/components/settings/ThemeSwitcher.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { useScheduleStore } from '@/stores/schedule'
import { useMediaQuery } from '@/composables/useMediaQuery'
import type {
  AppView,
  CalendarView,
  Schedule,
  ScheduleInput,
  StagedSchedule,
} from '@/types/schedule'
import {
  allDayDate,
  formatDayTitle,
  formatMonthTitle,
  formatScheduleDate,
  formatScheduleTime,
} from '@/utils/date'
import { getErrorMessage } from '@/utils/error'

const store = useScheduleStore()
const isMobile = useMediaQuery('(max-width: 767px)')
const isDesktop = useMediaQuery('(min-width: 1280px)')

const today = dayjs().format('YYYY-MM-DD')
const agendaDate = ref(today)
const currentDate = ref(today)
const calendarView = ref<CalendarView>('week')
const mobileView = ref<AppView>(isMobile.value ? 'agenda' : 'week')
const calendarTitle = ref(formatMonthTitle(today))

const topBarRef = ref<InstanceType<typeof TopBar>>()
const calendarRef = ref<InstanceType<typeof CalendarCanvas>>()

const selected = ref<Schedule | null>(null)
const formMode = ref<'create' | 'edit' | null>(null)
const formInitial = ref<Schedule | null>(null)
const formDraftStart = ref<string | null>(null)
const formDraftEnd = ref<string | null>(null)
const formSessionKey = ref(0)
const formDirty = ref(false)
const submitting = ref(false)
const submitError = ref('')
const deleting = ref(false)

const filterDrawerVisible = ref(false)
const stagingDrawerVisible = ref(false)
const stagedFormVisible = ref(false)
const editingStaged = ref<StagedSchedule | null>(null)
const stagedSubmitting = ref(false)
const stagedError = ref('')
const stagedFormDirty = ref(false)

const activeView = computed<AppView>(() => (isMobile.value ? mobileView.value : calendarView.value))
const showCalendar = computed(() => !isMobile.value || mobileView.value !== 'agenda')
const pageTitle = computed(() =>
  isMobile.value && mobileView.value === 'agenda'
    ? formatDayTitle(agendaDate.value)
    : calendarTitle.value,
)
const activeError = computed(() => (showCalendar.value ? store.error : store.dayError))
const calendarEmpty = computed(
  () =>
    showCalendar.value &&
    store.initialized &&
    !store.loading &&
    !store.error &&
    store.schedules.length === 0,
)
const panelOpen = computed({
  get: () => !isDesktop.value && (formMode.value !== null || selected.value !== null),
  set: (value: boolean) => {
    if (!value) {
      void requestCloseSheet()
    }
  },
})

watch(isDesktop, (desktop) => {
  if (desktop && agendaDate.value !== today) {
    agendaDate.value = today
    void store.fetchDaySchedules(today)
  }
})

onMounted(() => {
  void store.fetchDaySchedules(agendaDate.value)
  void store.fetchStaging()
  void store.fetchGithubStatus()
  document.addEventListener('keydown', handleShortcut)
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleShortcut)
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

function handleBeforeUnload(event: BeforeUnloadEvent) {
  if (formMode.value && formDirty.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}

function handleShortcut(event: KeyboardEvent) {
  if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) {
    return
  }
  const target = event.target as HTMLElement | null
  if (
    target?.closest('input, textarea, select, [contenteditable="true"]') ||
    document.querySelector('.el-overlay')
  ) {
    return
  }

  if (event.key === 'Escape' && formMode.value) {
    void closeForm()
    return
  }
  if (formMode.value) {
    return
  }

  switch (event.key) {
    case 'n':
    case 'N':
      event.preventDefault()
      openCreate()
      break
    case 't':
    case 'T':
      event.preventDefault()
      goToday()
      break
    case '/':
      event.preventDefault()
      topBarRef.value?.focusSearch()
      break
  }
}

function handleDatesSet(range: {
  start: string
  end: string
  title: string
  view: CalendarView
  currentDate: string
}) {
  calendarTitle.value = range.title
  if (!isMobile.value) {
    calendarView.value = range.view
  }
  const todayValue = dayjs()
  const inRange =
    dayjs(range.start).valueOf() <= todayValue.valueOf() &&
    dayjs(range.end).valueOf() > todayValue.valueOf()
  currentDate.value = inRange ? today : range.currentDate
  void store.setVisibleRange({ start: range.start, end: range.end })
}

function handleDateClick(info: DateClickArg) {
  const start = info.allDay
    ? dayjs(info.date).hour(9).minute(0).second(0)
    : dayjs(info.date).second(0)
  openCreate(
    start.format('YYYY-MM-DDTHH:mm:ss'),
    start.add(1, 'hour').format('YYYY-MM-DDTHH:mm:ss'),
  )
}

function openCreate(initialStart?: string, initialEnd?: string) {
  const baseDate =
    isMobile.value && mobileView.value === 'agenda' ? agendaDate.value : currentDate.value
  const base = dayjs(baseDate)
  const nextHour = dayjs().add(1, 'hour').minute(0).second(0)
  // 深夜创建时不要把默认时间跳到下一天，否则“今日安排”里看不到刚创建的日程。
  const sameDayDefault = nextHour.isSame(base, 'day') ? nextHour : base.hour(23).minute(0).second(0)
  const start =
    initialStart ??
    (base.isSame(dayjs(), 'day') ? sameDayDefault : base.hour(9).minute(0).second(0)).format(
      'YYYY-MM-DDTHH:mm:ss',
    )
  const end = initialEnd ?? dayjs(start).add(1, 'hour').format('YYYY-MM-DDTHH:mm:ss')

  selected.value = null
  formInitial.value = null
  formDraftStart.value = start
  formDraftEnd.value = end
  formMode.value = 'create'
  submitError.value = ''
  formDirty.value = false
  formSessionKey.value += 1
}

function openDetail(schedule: Schedule) {
  selected.value = schedule
  formMode.value = null
}

function openEdit() {
  if (!selected.value) {
    return
  }
  formInitial.value = selected.value
  formDraftStart.value = null
  formDraftEnd.value = null
  formMode.value = 'edit'
  submitError.value = ''
  formDirty.value = false
  formSessionKey.value += 1
}

async function requestCloseSheet() {
  if (formMode.value) {
    await closeForm()
    return
  }
  selected.value = null
}

async function closeForm() {
  if (formDirty.value) {
    try {
      await ElMessageBox.confirm('还有未保存的修改，确定关闭吗？', '放弃修改', {
        confirmButtonText: '放弃修改',
        cancelButtonText: '继续编辑',
        type: 'warning',
      })
    } catch {
      return
    }
  }

  if (formMode.value === 'create') {
    selected.value = null
  }
  formMode.value = null
  formInitial.value = null
  formDirty.value = false
  submitError.value = ''
}

async function handleSave(payload: ScheduleInput) {
  submitting.value = true
  submitError.value = ''
  try {
    const saved =
      formMode.value === 'edit' && formInitial.value
        ? await store.updateSchedule(formInitial.value.id, payload, agendaDate.value)
        : await store.createSchedule(payload, agendaDate.value)
    selected.value = saved
    formMode.value = null
    formInitial.value = null
    formDirty.value = false
    ElMessage.success('日程已保存')
  } catch (error) {
    submitError.value = getErrorMessage(error)
  } finally {
    submitting.value = false
  }
}

async function handleDelete() {
  if (!selected.value) {
    return
  }
  const schedule = selected.value
  try {
    await ElMessageBox.confirm(
      `「${schedule.title}」 · ${formatScheduleDate(schedule)} ${formatScheduleTime(schedule)}`,
      '删除这个日程？',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }

  deleting.value = true
  try {
    await store.removeSchedule(schedule.id)
    selected.value = null
    ElMessage.success('日程已删除')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    deleting.value = false
  }
}

async function handleSearchSelect(schedule: Schedule) {
  selected.value = schedule
  formMode.value = null
  const date = schedule.all_day
    ? allDayDate(schedule.start_at)
    : dayjs(schedule.start_at).format('YYYY-MM-DD')
  currentDate.value = date

  if (isMobile.value) {
    agendaDate.value = date
    void store.fetchDaySchedules(date)
    if (mobileView.value === 'agenda') {
      return
    }
  }
  await nextTick()
  calendarRef.value?.goToDate(date)
}

async function handleMiniSelect(date: string) {
  currentDate.value = date
  await nextTick()
  calendarRef.value?.goToDate(date)
}

async function changeView(view: AppView) {
  if (view === 'agenda') {
    mobileView.value = 'agenda'
    return
  }
  calendarView.value = view
  if (isMobile.value) {
    mobileView.value = view
  }
  await nextTick()
  calendarRef.value?.changeView(view)
  calendarRef.value?.updateSize()
}

function goPrev() {
  if (isMobile.value && mobileView.value === 'agenda') {
    void moveAgenda(-1)
    return
  }
  calendarRef.value?.prev()
}

function goNext() {
  if (isMobile.value && mobileView.value === 'agenda') {
    void moveAgenda(1)
    return
  }
  calendarRef.value?.next()
}

function goToday() {
  currentDate.value = today
  if (isMobile.value && mobileView.value === 'agenda') {
    agendaDate.value = today
    void store.fetchDaySchedules(today)
    return
  }
  calendarRef.value?.today()
}

async function moveAgenda(offset: number) {
  agendaDate.value = dayjs(agendaDate.value).add(offset, 'day').format('YYYY-MM-DD')
  currentDate.value = agendaDate.value
  await store.fetchDaySchedules(agendaDate.value)
}

function retryLoad() {
  if (showCalendar.value) {
    void store.fetchSchedules()
    return
  }
  void store.fetchDaySchedules(agendaDate.value)
}

function clearFilters() {
  void store.resetFilters(agendaDate.value)
}

function stagedAsSchedule(staged: StagedSchedule): Schedule {
  const start = staged.start_at ?? dayjs().hour(9).minute(0).second(0).toISOString()
  const end = staged.end_at ?? dayjs(start).add(30, 'minute').toISOString()
  return {
    id: staged.id,
    title: staged.title,
    category: staged.category,
    description: staged.description,
    start_at: start,
    end_at: end,
    all_day: staged.all_day,
    location: staged.location,
    status: 'pending',
    source: staged.source,
    source_ref: staged.source_ref,
    source_url: staged.source_url,
    created_at: staged.created_at,
    updated_at: staged.updated_at,
  }
}

function openStagedEdit(staged: StagedSchedule) {
  editingStaged.value = staged
  stagedError.value = ''
  stagedFormDirty.value = false
  stagedFormVisible.value = true
}

async function closeStagedEdit() {
  if (stagedFormDirty.value) {
    try {
      await ElMessageBox.confirm('还有未保存的修改，确定关闭吗？', '放弃修改', {
        confirmButtonText: '放弃修改',
        cancelButtonText: '继续编辑',
        type: 'warning',
      })
    } catch {
      return
    }
  }
  stagedFormVisible.value = false
  stagedFormDirty.value = false
  editingStaged.value = null
  stagedError.value = ''
}

async function handleStagedBeforeClose(done: () => void) {
  if (stagedFormDirty.value) {
    try {
      await ElMessageBox.confirm('还有未保存的修改，确定关闭吗？', '放弃修改', {
        confirmButtonText: '放弃修改',
        cancelButtonText: '继续编辑',
        type: 'warning',
      })
    } catch {
      return
    }
  }
  editingStaged.value = null
  stagedError.value = ''
  stagedFormDirty.value = false
  done()
}

async function handleStagedSave(payload: ScheduleInput) {
  if (!editingStaged.value) {
    return
  }
  stagedSubmitting.value = true
  stagedError.value = ''
  try {
    await store.updateStaged(editingStaged.value.id, {
      title: payload.title,
      category: payload.category,
      description: payload.description,
      start_at: payload.start_at,
      end_at: payload.end_at,
      all_day: payload.all_day,
      location: payload.location,
    })
    ElMessage.success('暂存日程已更新')
    stagedFormDirty.value = false
    stagedFormVisible.value = false
    editingStaged.value = null
  } catch (error) {
    stagedError.value = getErrorMessage(error)
  } finally {
    stagedSubmitting.value = false
  }
}
</script>

<template>
  <AppShell>
    <template #topbar>
      <TopBar
        ref="topBarRef"
        :title="pageTitle"
        :view="activeView"
        :is-mobile="isMobile"
        :show-filter-button="!isDesktop"
        :filter-summary="store.activeFilterSummary"
        :staging-count="store.pendingStagingCount"
        @prev="goPrev"
        @next="goNext"
        @today="goToday"
        @new="openCreate()"
        @change-view="changeView"
        @toggle-filters="filterDrawerVisible = true"
        @toggle-staging="stagingDrawerVisible = true"
        @select-schedule="handleSearchSelect"
      />
    </template>

    <template #sidebar>
      <div v-if="isDesktop" class="sidebar flex flex-col gap-3.5 pr-0.5">
        <MiniCalendar :current-date="currentDate" @select="handleMiniSelect" />
        <CategoryFilter :day-date="agendaDate" />
        <MoreFilters :day-date="agendaDate" />
        <ThemeSwitcher />
        <AccountPanel />
        <div
          v-if="store.hasActiveFilters"
          class="filter-summary flex items-start justify-between gap-2 rounded-xl border border-line bg-canvas px-3 py-2.5 text-[11px] leading-relaxed text-ink-muted"
        >
          <span class="min-w-0">{{ store.activeFilterSummary }}</span>
          <button
            type="button"
            class="shrink-0 cursor-pointer border-0 bg-transparent p-0 text-[11px] text-danger hover:underline"
            @click="clearFilters"
          >
            清除
          </button>
        </div>
      </div>
    </template>

    <div class="main-content flex min-h-0 flex-1 flex-col">
      <el-alert
        v-if="activeError"
        :title="activeError"
        type="error"
        show-icon
        :closable="false"
        class="mb-2.5 shrink-0"
      >
        <template #default>
          <el-button link type="primary" @click="retryLoad">重新加载</el-button>
        </template>
      </el-alert>

      <section
        v-show="showCalendar"
        class="calendar-shell relative min-h-0 flex-1 overflow-hidden rounded-2xl border border-line bg-surface shadow-soft max-md:rounded-[14px]"
        aria-label="日历画布"
      >
        <div
          v-if="store.loading && !store.initialized"
          class="calendar-skeleton absolute inset-0 z-[5] overflow-hidden bg-surface p-3.5"
          aria-label="日历加载中"
        >
          <LoadingState />
        </div>
        <div
          v-if="store.loading && store.initialized"
          class="loading-line absolute left-0 top-0 z-[6] h-0.5 w-[36%] animate-[loading-slide_1.2s_ease-in-out_infinite] bg-focus motion-reduce:w-full motion-reduce:animate-none motion-reduce:opacity-55"
        ></div>

        <CalendarCanvas
          ref="calendarRef"
          :schedules="store.schedules"
          :initial-view="calendarView"
          @dates-set="handleDatesSet"
          @date-click="handleDateClick"
          @event-click="openDetail"
        />

        <div
          v-if="calendarEmpty"
          class="calendar-empty absolute left-1/2 top-[74px] z-[4] flex -translate-x-1/2 flex-col items-center gap-1 rounded-full border border-line bg-surface/95 px-4 py-2 text-center text-xs text-ink-muted shadow-soft max-md:top-[62px] max-md:w-max max-md:max-w-[88%]"
        >
          <p class="m-0">
            {{ store.hasActiveFilters ? '没有符合筛选条件的日程' : '这个时间段还没有安排' }}
          </p>
          <el-button v-if="store.hasActiveFilters" text type="primary" @click="clearFilters">
            清除筛选
          </el-button>
        </div>
      </section>

      <section
        v-if="!showCalendar"
        class="agenda-shell min-h-0 flex-1 overflow-hidden rounded-2xl border border-line bg-surface shadow-soft max-md:rounded-[14px]"
        aria-label="当天日程"
      >
        <TodayAgenda
          :date="agendaDate"
          :schedules="store.daySchedules"
          :loading="store.dayLoading"
          :pending-count="store.pendingStagingCount"
          show-staging-button
          @select="openDetail"
          @create="openCreate()"
          @open-staging="stagingDrawerVisible = true"
        />
      </section>
    </div>

    <template #panel>
      <div v-if="isDesktop" class="panel-content flex h-full min-h-0 flex-col">
        <div v-if="formMode" class="panel-form flex h-full min-h-0 flex-col">
          <header
            class="panel-form__header flex shrink-0 items-center justify-between border-b border-line px-5 pb-3 pt-4"
          >
            <h2 class="m-0 font-display text-[19px] font-semibold tracking-[-0.01em] text-ink">
              {{ formMode === 'edit' ? '编辑日程' : '新建日程' }}
            </h2>
            <button
              type="button"
              aria-label="关闭表单"
              class="panel-close inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border-0 bg-transparent p-0 text-ink-muted hover:bg-canvas hover:text-ink"
              @click="closeForm"
            >
              <el-icon><Close /></el-icon>
            </button>
          </header>
          <ScheduleForm
            :key="formSessionKey"
            class="flex-1 overflow-y-auto px-5 pb-5 pt-4"
            :initial="formInitial"
            :initial-start="formDraftStart"
            :initial-end="formDraftEnd"
            :submitting="submitting"
            :submit-error="submitError"
            @submit="handleSave"
            @cancel="closeForm"
            @dirty-change="formDirty = $event"
          />
        </div>

        <ScheduleDetailPanel
          v-else-if="selected"
          :schedule="selected"
          :deleting="deleting"
          @edit="openEdit"
          @delete="handleDelete"
          @close="selected = null"
        />

        <TodayAgenda
          v-else
          :date="today"
          :schedules="store.daySchedules"
          :loading="store.dayLoading"
          @select="openDetail"
          @create="openCreate()"
        />
      </div>
    </template>
  </AppShell>

  <el-drawer
    v-model="filterDrawerVisible"
    :direction="isMobile ? 'btt' : 'rtl'"
    :size="isMobile ? '74%' : '360px'"
    title="筛选"
  >
    <div class="filter-drawer flex flex-col gap-3.5">
      <CategoryFilter :day-date="agendaDate" />
      <MoreFilters :day-date="agendaDate" />
      <ThemeSwitcher />
      <AccountPanel />
      <div
        v-if="store.hasActiveFilters"
        class="filter-summary flex items-start justify-between gap-2 rounded-xl border border-line bg-canvas px-3 py-2.5 text-[11px] leading-relaxed text-ink-muted"
      >
        <span class="min-w-0">{{ store.activeFilterSummary }}</span>
        <button
          type="button"
          class="shrink-0 cursor-pointer border-0 bg-transparent p-0 text-[11px] text-danger hover:underline"
          @click="clearFilters"
        >
          清除
        </button>
      </div>
    </div>
  </el-drawer>

  <StagingDrawer v-model="stagingDrawerVisible" @edit="openStagedEdit" />

  <el-dialog
    v-model="stagedFormVisible"
    title="调整暂存日程"
    width="560px"
    destroy-on-close
    :before-close="handleStagedBeforeClose"
  >
    <ScheduleForm
      v-if="editingStaged"
      :key="editingStaged.id"
      :initial="stagedAsSchedule(editingStaged)"
      :submitting="stagedSubmitting"
      :submit-error="stagedError"
      submit-label="保存调整"
      @submit="handleStagedSave"
      @cancel="closeStagedEdit"
      @dirty-change="stagedFormDirty = $event"
    />
  </el-dialog>

  <el-drawer
    v-if="!isDesktop"
    v-model="panelOpen"
    :direction="isMobile ? 'btt' : 'rtl'"
    :size="isMobile ? '88%' : '420px'"
    :with-header="false"
    class="mobile-panel"
  >
    <div v-if="formMode" class="panel-form flex h-full min-h-0 flex-col">
      <header
        class="panel-form__header flex shrink-0 items-center justify-between border-b border-line px-5 pb-3 pt-4"
      >
        <h2 class="m-0 font-display text-[19px] font-semibold tracking-[-0.01em] text-ink">
          {{ formMode === 'edit' ? '编辑日程' : '新建日程' }}
        </h2>
        <button
          type="button"
          aria-label="关闭表单"
          class="panel-close inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border-0 bg-transparent p-0 text-ink-muted hover:bg-canvas hover:text-ink"
          @click="closeForm"
        >
          <el-icon><Close /></el-icon>
        </button>
      </header>
      <ScheduleForm
        :key="formSessionKey"
        class="flex-1 overflow-y-auto px-5 pb-5 pt-4"
        :initial="formInitial"
        :initial-start="formDraftStart"
        :initial-end="formDraftEnd"
        :submitting="submitting"
        :submit-error="submitError"
        @submit="handleSave"
        @cancel="closeForm"
        @dirty-change="formDirty = $event"
      />
    </div>

    <ScheduleDetailPanel
      v-else-if="selected"
      :schedule="selected"
      :deleting="deleting"
      @edit="openEdit"
      @delete="handleDelete"
      @close="selected = null"
    />
  </el-drawer>

  <button
    v-if="isMobile"
    type="button"
    class="fab fixed bottom-[calc(18px+env(safe-area-inset-bottom))] right-[18px] z-30 inline-flex min-h-12 min-w-24 cursor-pointer items-center justify-center gap-1.5 rounded-full border-0 bg-ink px-5 text-[13px] font-medium text-surface shadow-[0_10px_28px_rgb(20_20_19/22%)] transition-transform hover:-translate-y-0.5"
    aria-label="新建日程"
    @click="openCreate()"
  >
    <el-icon><Plus /></el-icon>
    <span>新建</span>
  </button>
</template>
