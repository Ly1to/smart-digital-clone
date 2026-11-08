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
  <header class="top-bar">
    <div class="top-bar__identity">
      <span class="top-bar__seal" aria-hidden="true">日</span>
      <div class="top-bar__titles">
        <strong class="top-bar__product">个人日程</strong>
        <span class="top-bar__title">{{ title }}</span>
      </div>
    </div>

    <div class="top-bar__nav" aria-label="日期导航">
      <button type="button" class="nav-button" aria-label="上一个周期" @click="emit('prev')">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <button type="button" class="today-button" @click="emit('today')">今天</button>
      <button type="button" class="nav-button" aria-label="下一个周期" @click="emit('next')">
        <el-icon><ArrowRight /></el-icon>
      </button>
    </div>

    <div class="top-bar__views" role="group" aria-label="视图切换">
      <button
        v-for="option in viewOptions"
        :key="option.value"
        type="button"
        class="view-button"
        :class="{ 'is-active': option.value === props.view }"
        :aria-pressed="option.value === props.view"
        @click="emit('changeView', option.value)"
      >
        {{ option.label }}
      </button>
    </div>

    <div class="top-bar__actions">
      <button
        v-if="!props.isMobile"
        type="button"
        class="staging-button"
        aria-label="打开暂存区"
        title="待确认日程暂存区"
        @click="emit('toggleStaging')"
      >
        <el-icon><Collection /></el-icon>
        <span>暂存</span>
        <span v-if="props.stagingCount" class="staging-button__badge">
          {{ props.stagingCount > 99 ? '99+' : props.stagingCount }}
        </span>
      </button>

      <SearchPopover ref="searchRef" @select="emit('selectSchedule', $event)" />

      <button
        v-if="props.showFilterButton"
        type="button"
        class="filter-button"
        :class="{ 'has-filter': props.filterSummary }"
        aria-label="打开筛选"
        @click="emit('toggleFilters')"
      >
        筛选
        <span v-if="props.filterSummary" class="filter-button__dot"></span>
      </button>

      <el-button class="top-bar__new" type="primary" :icon="Plus" @click="emit('new')">
        新建日程
      </el-button>
    </div>
  </header>
</template>

<style scoped>
.top-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px 18px;
  min-height: 70px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--color-line);
}

.top-bar__identity {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  margin-right: auto;
}

.top-bar__seal {
  display: inline-flex;
  flex: 0 0 34px;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  color: var(--color-surface);
  font-family: var(--font-display);
  font-size: 17px;
  background: var(--color-focus);
  border-radius: 10px;
}

.top-bar__titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.top-bar__product {
  color: var(--color-ink);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.top-bar__title {
  overflow: hidden;
  color: var(--color-ink);
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 600;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.top-bar__nav,
.top-bar__views,
.top-bar__actions {
  display: flex;
  align-items: center;
}

.top-bar__nav {
  gap: 4px;
}

.nav-button,
.today-button,
.view-button,
.filter-button,
.staging-button {
  min-height: 38px;
  padding: 0 11px;
  color: var(--color-ink-secondary);
  font-size: 13px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition:
    color 0.15s ease,
    background-color 0.15s ease,
    border-color 0.15s ease;
}

.staging-button {
  position: relative;
  display: inline-flex;
  gap: 5px;
  align-items: center;
  padding: 0 10px;
}

.staging-button__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  color: var(--color-surface);
  font-size: 10px;
  font-variant-numeric: tabular-nums;
  background: var(--color-focus);
  border-radius: 999px;
}

.nav-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  padding: 0;
  font-size: 15px;
}

.nav-button:hover,
.today-button:hover,
.view-button:hover,
.filter-button:hover,
.staging-button:hover {
  color: var(--color-ink);
  background: var(--color-surface);
  border-color: var(--color-line);
}

.nav-button:focus-visible,
.today-button:focus-visible,
.view-button:focus-visible,
.filter-button:focus-visible,
.staging-button:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.top-bar__views {
  gap: 2px;
  padding: 3px;
  background: rgb(223 215 200 / 42%);
  border-radius: 10px;
}

.view-button {
  min-width: 38px;
  min-height: 32px;
  padding: 0 12px;
  border: 0;
}

.view-button.is-active {
  color: var(--color-surface);
  background: var(--color-ink);
}

.top-bar__actions {
  gap: 6px;
}

.filter-button {
  position: relative;
}

.filter-button.has-filter {
  color: var(--color-focus);
  border-color: var(--color-line-strong);
}

.filter-button__dot {
  position: absolute;
  top: 7px;
  right: 6px;
  width: 5px;
  height: 5px;
  background: var(--color-focus);
  border-radius: 50%;
}

@media (max-width: 1279px) {
  .top-bar {
    padding: 10px 16px;
  }

  .top-bar__title {
    font-size: 19px;
  }
}

@media (max-width: 767px) {
  .top-bar {
    display: grid;
    grid-template-areas:
      'identity actions'
      'nav nav'
      'views views';
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 6px 8px;
    padding: 10px 12px;
    min-height: auto;
  }

  .top-bar__identity {
    grid-area: identity;
    margin-right: 0;
  }

  .top-bar__seal {
    display: none;
  }

  .top-bar__product {
    font-size: 11px;
    color: var(--color-ink-muted);
  }

  .top-bar__title {
    font-size: 18px;
  }

  .top-bar__nav {
    grid-area: nav;
    justify-self: start;
    padding-top: 2px;
  }

  .nav-button,
  .today-button {
    min-height: 44px;
  }

  .top-bar__views {
    grid-area: views;
    width: 100%;
    justify-content: space-between;
  }

  .view-button {
    flex: 1;
    min-height: 44px;
  }

  .top-bar__actions {
    grid-area: actions;
    position: static;
    justify-self: end;
  }

  .top-bar__new {
    display: none;
  }

  .filter-button {
    min-height: 44px;
  }
}
</style>
