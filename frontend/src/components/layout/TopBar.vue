<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, ArrowRight, Collection, Plus } from '@element-plus/icons-vue'

import SearchPopover from '@/components/search/SearchPopover.vue'
import { VIEW_LABELS } from '@/constants/schedule'
import type { AppView, Schedule } from '@/types/schedule'

const props = defineProps<{
  title: string
  view: AppView
  isMobile: boolean
  showFilterButton: boolean
  filterSummary: string
  stagingCount: number
}>()

const emit = defineEmits<{
  prev: []
  next: []
  today: []
  new: []
  changeView: [view: AppView]
  toggleFilters: []
  toggleStaging: []
  selectSchedule: [schedule: Schedule]
}>()

const searchRef = ref<InstanceType<typeof SearchPopover>>()

const viewOptions = computed(() =>
  (props.isMobile ? ['agenda', 'month', 'week', 'day'] : ['month', 'week', 'day']).map((value) => ({
    value: value as AppView,
    label: VIEW_LABELS[value as AppView],
  })),
)

function focusSearch() {
  searchRef.value?.focusSearch()
}

defineExpose({ focusSearch })
</script>

<template>
  <header
    class="top-bar relative z-30 flex min-h-[64px] flex-wrap items-center gap-x-4 gap-y-3 border-b border-line/80 bg-canvas/80 px-5 py-2.5 backdrop-blur-md max-xl:px-4 max-md:grid max-md:min-h-0 max-md:grid-cols-[minmax(0,1fr)_auto] max-md:gap-x-2 max-md:gap-y-1.5 max-md:px-3 max-md:py-2.5"
  >
    <div
      class="top-bar__identity col-start-1 row-start-1 mr-auto flex min-w-0 items-center gap-2.5 max-md:mr-0"
    >
      <span
        class="top-bar__seal inline-flex h-8 w-8 flex-[0_0_32px] items-center justify-center rounded-[10px] bg-focus font-display text-[15px] text-surface shadow-[0_1px_2px_rgb(169_79_50/25%)] max-md:hidden"
        aria-hidden="true"
      >
        日
      </span>
      <div class="top-bar__titles flex min-w-0 flex-col gap-px">
        <strong
          class="top-bar__product text-[10px] font-medium uppercase tracking-[0.18em] text-ink-muted max-md:text-[10px]"
        >
          个人日程
        </strong>
        <span
          class="top-bar__title overflow-hidden text-ellipsis whitespace-nowrap font-display text-[22px] font-semibold leading-[1.2] tracking-[-0.01em] text-ink max-xl:text-[20px] max-md:text-[17px]"
        >
          {{ title }}
        </span>
      </div>
    </div>

    <div
      class="top-bar__nav col-span-2 row-start-2 flex items-center gap-0.5 max-md:justify-self-start max-md:pt-0.5"
      aria-label="日期导航"
    >
      <button
        type="button"
        class="nav-button inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-transparent bg-transparent p-0 text-[15px] text-ink-secondary transition-colors hover:border-line hover:bg-surface hover:text-ink hover:shadow-soft max-md:min-h-11 max-md:min-w-11"
        aria-label="上一个周期"
        @click="emit('prev')"
      >
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <button
        type="button"
        class="today-button inline-flex min-h-9 cursor-pointer items-center rounded-full border border-line bg-surface px-3.5 text-[12px] font-medium text-ink-secondary shadow-[0_1px_2px_rgb(20_20_19/4%)] transition-colors hover:border-line-strong hover:text-ink max-md:min-h-11"
        @click="emit('today')"
      >
        今天
      </button>
      <button
        type="button"
        class="nav-button inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-transparent bg-transparent p-0 text-[15px] text-ink-secondary transition-colors hover:border-line hover:bg-surface hover:text-ink hover:shadow-soft max-md:min-h-11 max-md:min-w-11"
        aria-label="下一个周期"
        @click="emit('next')"
      >
        <el-icon><ArrowRight /></el-icon>
      </button>
    </div>

    <div
      class="top-bar__views col-span-2 row-start-3 flex items-center gap-0.5 rounded-full bg-[#ece7db] p-1 max-md:w-full max-md:justify-between"
      role="group"
      aria-label="视图切换"
    >
      <button
        v-for="option in viewOptions"
        :key="option.value"
        type="button"
        class="view-button min-h-7 min-w-[42px] cursor-pointer rounded-full border-0 px-3 text-[12px] transition-all max-md:min-h-11 max-md:flex-1"
        :class="
          option.value === props.view
            ? 'is-active bg-surface font-medium text-ink shadow-[0_1px_2px_rgb(20_20_19/8%),0_1px_1px_rgb(20_20_19/4%)]'
            : 'bg-transparent text-ink-muted hover:text-ink'
        "
        :aria-pressed="option.value === props.view"
        @click="emit('changeView', option.value)"
      >
        {{ option.label }}
      </button>
    </div>

    <div
      class="top-bar__actions col-start-2 row-start-1 flex items-center gap-1.5 max-md:justify-self-end"
    >
      <button
        v-if="!props.isMobile"
        type="button"
        class="staging-button relative inline-flex min-h-9 cursor-pointer items-center gap-1.5 rounded-full border border-transparent bg-transparent px-2.5 text-[12px] text-ink-secondary transition-colors hover:border-line hover:bg-surface hover:text-ink hover:shadow-soft"
        aria-label="打开暂存区"
        title="待确认日程暂存区"
        @click="emit('toggleStaging')"
      >
        <el-icon><Collection /></el-icon>
        <span>暂存</span>
        <span
          v-if="props.stagingCount"
          class="staging-button__badge inline-flex h-[17px] min-w-[17px] items-center justify-center rounded-full bg-focus px-1 text-[10px] font-medium tabular-nums text-surface"
        >
          {{ props.stagingCount > 99 ? '99+' : props.stagingCount }}
        </span>
      </button>

      <SearchPopover ref="searchRef" @select="emit('selectSchedule', $event)" />

      <button
        v-if="props.showFilterButton"
        type="button"
        class="filter-button relative min-h-9 cursor-pointer rounded-full border bg-transparent px-3 text-[12px] transition-colors hover:border-line hover:bg-surface hover:text-ink hover:shadow-soft max-md:min-h-11"
        :class="
          props.filterSummary
            ? 'has-filter border-line-strong text-focus'
            : 'border-transparent text-ink-secondary'
        "
        aria-label="打开筛选"
        @click="emit('toggleFilters')"
      >
        筛选
        <span
          v-if="props.filterSummary"
          class="filter-button__dot absolute right-1.5 top-[7px] h-[5px] w-[5px] rounded-full bg-focus"
        ></span>
      </button>

      <el-button
        class="top-bar__new max-md:hidden!"
        type="primary"
        :icon="Plus"
        @click="emit('new')"
      >
        新建日程
      </el-button>
    </div>
  </header>
</template>
