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
    class="top-bar flex min-h-[70px] flex-wrap items-center gap-x-[18px] gap-y-3.5 border-b border-line px-6 py-3 max-xl:px-4 max-xl:py-2.5 max-md:grid max-md:min-h-0 max-md:grid-cols-[minmax(0,1fr)_auto] max-md:gap-x-2 max-md:gap-y-1.5 max-md:px-3 max-md:py-2.5"
  >
    <div
      class="top-bar__identity col-start-1 row-start-1 mr-auto flex min-w-0 items-center gap-2.5 max-md:mr-0"
    >
      <span
        class="top-bar__seal inline-flex h-[34px] w-[34px] flex-[0_0_34px] items-center justify-center rounded-[10px] bg-focus font-display text-[17px] text-surface max-md:hidden"
        aria-hidden="true"
      >
        日
      </span>
      <div class="top-bar__titles flex min-w-0 flex-col gap-0.5">
        <strong
          class="top-bar__product text-[13px] font-semibold tracking-[0.04em] text-ink max-md:text-[11px] max-md:text-ink-muted"
        >
          个人日程
        </strong>
        <span
          class="top-bar__title overflow-hidden text-ellipsis whitespace-nowrap font-display text-[21px] font-semibold leading-tight text-ink max-xl:text-[19px] max-md:text-lg"
        >
          {{ title }}
        </span>
      </div>
    </div>

    <div
      class="top-bar__nav col-span-2 row-start-2 flex items-center gap-1 max-md:justify-self-start max-md:pt-0.5"
      aria-label="日期导航"
    >
      <button
        type="button"
        class="nav-button inline-flex h-[38px] w-[38px] cursor-pointer items-center justify-center rounded-lg border border-transparent bg-transparent p-0 text-[15px] text-ink-secondary transition-colors hover:border-line hover:bg-surface hover:text-ink max-md:min-h-11"
        aria-label="上一个周期"
        @click="emit('prev')"
      >
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <button
        type="button"
        class="today-button min-h-[38px] cursor-pointer rounded-lg border border-transparent bg-transparent px-[11px] text-[13px] text-ink-secondary transition-colors hover:border-line hover:bg-surface hover:text-ink max-md:min-h-11"
        @click="emit('today')"
      >
        今天
      </button>
      <button
        type="button"
        class="nav-button inline-flex h-[38px] w-[38px] cursor-pointer items-center justify-center rounded-lg border border-transparent bg-transparent p-0 text-[15px] text-ink-secondary transition-colors hover:border-line hover:bg-surface hover:text-ink max-md:min-h-11"
        aria-label="下一个周期"
        @click="emit('next')"
      >
        <el-icon><ArrowRight /></el-icon>
      </button>
    </div>

    <div
      class="top-bar__views col-span-2 row-start-3 flex items-center gap-0.5 rounded-[10px] bg-[rgb(223_215_200/42%)] p-[3px] max-md:w-full max-md:justify-between"
      role="group"
      aria-label="视图切换"
    >
      <button
        v-for="option in viewOptions"
        :key="option.value"
        type="button"
        class="view-button min-h-8 min-w-[38px] cursor-pointer rounded-lg border-0 px-3 text-[13px] transition-colors hover:bg-surface hover:text-ink max-md:min-h-11 max-md:flex-1"
        :class="
          option.value === props.view
            ? 'is-active bg-ink text-surface'
            : 'bg-transparent text-ink-secondary'
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
        class="staging-button relative inline-flex min-h-[38px] cursor-pointer items-center gap-[5px] rounded-lg border border-transparent bg-transparent px-2.5 text-[13px] text-ink-secondary transition-colors hover:border-line hover:bg-surface hover:text-ink"
        aria-label="打开暂存区"
        title="待确认日程暂存区"
        @click="emit('toggleStaging')"
      >
        <el-icon><Collection /></el-icon>
        <span>暂存</span>
        <span
          v-if="props.stagingCount"
          class="staging-button__badge inline-flex h-[17px] min-w-[17px] items-center justify-center rounded-full bg-focus px-1 text-[10px] tabular-nums text-surface"
        >
          {{ props.stagingCount > 99 ? '99+' : props.stagingCount }}
        </span>
      </button>

      <SearchPopover ref="searchRef" @select="emit('selectSchedule', $event)" />

      <button
        v-if="props.showFilterButton"
        type="button"
        class="filter-button relative min-h-[38px] cursor-pointer rounded-lg border bg-transparent px-[11px] text-[13px] transition-colors hover:border-line hover:bg-surface hover:text-ink max-md:min-h-11"
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
