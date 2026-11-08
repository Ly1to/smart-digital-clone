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
  const start =
    initialStart ??
    (base.isSame(dayjs(), 'day')
      ? dayjs().add(1, 'hour').minute(0).second(0)
      : base.hour(9).minute(0).second(0)
    ).format('YYYY-MM-DDTHH:mm:ss')
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
      <div v-if="isDesktop" class="sidebar">
        <MiniCalendar :current-date="currentDate" @select="handleMiniSelect" />
        <CategoryFilter :day-date="agendaDate" />
        <MoreFilters :day-date="agendaDate" />
        <ThemeSwitcher />
        <AccountPanel />
        <div v-if="store.hasActiveFilters" class="filter-summary">
          <span>{{ store.activeFilterSummary }}</span>
          <button type="button" @click="clearFilters">清除</button>
        </div>
      </div>
    </template>

    <div class="main-content">
      <el-alert
        v-if="activeError"
        :title="activeError"
        type="error"
        show-icon
        :closable="false"
        class="main-alert"
      >
        <template #default>
          <el-button link type="primary" @click="retryLoad">重新加载</el-button>
        </template>
      </el-alert>

      <section v-show="showCalendar" class="calendar-shell" aria-label="日历画布">
        <div
          v-if="store.loading && !store.initialized"
          class="calendar-skeleton"
          aria-label="日历加载中"
        >
          <LoadingState />
        </div>
        <div v-if="store.loading && store.initialized" class="loading-line"></div>

        <CalendarCanvas
          ref="calendarRef"
          :schedules="store.schedules"
          :initial-view="calendarView"
          @dates-set="handleDatesSet"
          @date-click="handleDateClick"
          @event-click="openDetail"
        />

        <div v-if="calendarEmpty" class="calendar-empty">
          <p>
            {{ store.hasActiveFilters ? '没有符合筛选条件的日程' : '这个时间段还没有安排' }}
          </p>
          <el-button v-if="store.hasActiveFilters" text type="primary" @click="clearFilters">
            清除筛选
          </el-button>
        </div>
      </section>

      <section v-if="!showCalendar" class="agenda-shell" aria-label="当天日程">
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
      <div v-if="isDesktop" class="panel-content">
        <div v-if="formMode" class="panel-form">
          <header class="panel-form__header">
            <h2>{{ formMode === 'edit' ? '编辑日程' : '新建日程' }}</h2>
            <button type="button" aria-label="关闭表单" class="panel-close" @click="closeForm">
              <el-icon><Close /></el-icon>
            </button>
          </header>
          <ScheduleForm
            :key="formSessionKey"
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
    <div class="filter-drawer">
      <CategoryFilter :day-date="agendaDate" />
      <MoreFilters :day-date="agendaDate" />
      <ThemeSwitcher />
      <AccountPanel />
      <div v-if="store.hasActiveFilters" class="filter-summary">
        <span>{{ store.activeFilterSummary }}</span>
        <button type="button" @click="clearFilters">清除</button>
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
    <div v-if="formMode" class="panel-form">
      <header class="panel-form__header">
        <h2>{{ formMode === 'edit' ? '编辑日程' : '新建日程' }}</h2>
        <button type="button" aria-label="关闭表单" class="panel-close" @click="closeForm">
          <el-icon><Close /></el-icon>
        </button>
      </header>
      <ScheduleForm
        :key="formSessionKey"
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

  <button v-if="isMobile" type="button" class="fab" aria-label="新建日程" @click="openCreate()">
    <el-icon><Plus /></el-icon>
    <span>新建</span>
  </button>
</template>

<style scoped>
.main-content {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}

.main-alert {
  flex: 0 0 auto;
  margin-bottom: 10px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 2px;
}

.calendar-shell {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: 12px;
}

.calendar-skeleton {
  position: absolute;
  inset: 0;
  z-index: 5;
  padding: 14px;
  overflow: hidden;
  background: var(--color-surface);
}

.loading-line {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 6;
  width: 36%;
  height: 2px;
  background: var(--color-focus);
  animation: loading-slide 1.2s ease-in-out infinite;
}

.calendar-empty {
  position: absolute;
  top: 74px;
  left: 50%;
  z-index: 4;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  color: var(--color-ink-muted);
  font-size: 12px;
  text-align: center;
  background: rgb(255 253 248 / 92%);
  border: 1px solid var(--color-line);
  border-radius: 10px;
  transform: translateX(-50%);
}

.calendar-empty p {
  margin: 0;
}

.agenda-shell {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: 12px;
}

.panel-content,
.mobile-panel :deep(.el-drawer__body) {
  height: 100%;
}

.panel-content {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

:global(.el-drawer.staging-drawer .el-drawer__body) {
  padding: 0;
}

.panel-form {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.panel-form__header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px 10px;
  border-bottom: 1px solid var(--color-line);
}

.panel-form__header h2 {
  margin: 0;
  color: var(--color-ink);
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
}

.panel-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  color: var(--color-ink-muted);
  background: transparent;
  border: 0;
  border-radius: 7px;
  cursor: pointer;
}

.panel-close:hover {
  color: var(--color-ink);
  background: var(--color-canvas);
}

.panel-close:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 1px;
}

.panel-form > :deep(.schedule-form) {
  flex: 1;
  padding: 14px 18px 18px;
  overflow-y: auto;
}

.filter-drawer {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.filter-summary {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 10px;
  color: var(--color-ink-muted);
  font-size: 11px;
  line-height: 1.6;
  background: var(--color-canvas);
  border-radius: 8px;
}

.filter-summary span {
  min-width: 0;
}

.filter-summary button {
  flex: 0 0 auto;
  padding: 0;
  color: var(--color-danger);
  font-size: 11px;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.filter-summary button:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.fab {
  position: fixed;
  right: 18px;
  bottom: calc(18px + env(safe-area-inset-bottom));
  z-index: 30;
  display: inline-flex;
  gap: 6px;
  align-items: center;
  justify-content: center;
  min-width: 96px;
  min-height: 48px;
  padding: 0 18px;
  color: var(--color-surface);
  font-size: 14px;
  font-weight: 500;
  background: var(--color-ink);
  border: 0;
  border-radius: 999px;
  box-shadow: 0 8px 20px rgb(55 46 35 / 18%);
  cursor: pointer;
}

.fab:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 3px;
}

@keyframes loading-slide {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(360%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .loading-line {
    width: 100%;
    animation: none;
    opacity: 0.55;
  }
}

@media (max-width: 767px) {
  .calendar-shell,
  .agenda-shell {
    border-radius: 10px;
  }

  .calendar-empty {
    top: 62px;
    width: max-content;
    max-width: 88%;
  }
}
</style>
