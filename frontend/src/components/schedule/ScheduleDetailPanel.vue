<script setup lang="ts">
import { Close, EditPen } from '@element-plus/icons-vue'

import { CATEGORY_META, STATUS_META } from '@/constants/schedule'
import type { Schedule } from '@/types/schedule'
import { formatLocalDateTime, formatScheduleDate, formatScheduleTime } from '@/utils/date'

withDefaults(
  defineProps<{
    schedule: Schedule
    deleting?: boolean
  }>(),
  {
    deleting: false,
  },
)

const emit = defineEmits<{
  edit: []
  delete: []
  close: []
}>()

function sourceLabel(source: string): string {
  if (source === 'github') {
    return 'GitHub'
  }
  if (source === 'gitee') {
    return 'Gitee'
  }
  return source
}
</script>

<template>
  <article class="detail-panel flex h-full min-h-0 flex-col overflow-y-auto p-5">
    <header class="detail-panel__header flex items-start justify-between gap-2.5">
      <div class="detail-panel__heading flex flex-wrap items-center gap-2">
        <span
          class="detail-panel__category inline-flex items-center gap-1 rounded-full px-[9px] py-[3px] text-[11px]"
          :class="CATEGORY_META[schedule.category].badgeClass"
        >
          {{ CATEGORY_META[schedule.category].label }}
        </span>
        <span
          class="detail-panel__status inline-flex items-center gap-1 rounded-full px-[9px] py-[3px] text-[11px]"
          :class="STATUS_META[schedule.status].badgeClass"
        >
          <span v-if="STATUS_META[schedule.status].icon" aria-hidden="true">
            {{ STATUS_META[schedule.status].icon }}
          </span>
          {{ STATUS_META[schedule.status].label }}
        </span>
      </div>
      <button
        type="button"
        class="detail-panel__close inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border-0 bg-transparent p-0 text-ink-muted hover:bg-canvas hover:text-ink"
        aria-label="关闭日程详情"
        @click="emit('close')"
      >
        <el-icon><Close /></el-icon>
      </button>
    </header>

    <h2
      class="detail-panel__title mb-2 mt-4 break-words font-display text-[24px] font-semibold leading-[1.3] tracking-[-0.01em]"
      :class="STATUS_META[schedule.status].titleClass"
    >
      {{ schedule.title }}
    </h2>

    <dl class="detail-list m-0 mb-6 p-0 pt-1">
      <div class="flex gap-3.5 border-b border-dashed border-line py-[11px]">
        <dt class="flex-[0_0_48px] text-xs text-ink-muted">日期</dt>
        <dd class="m-0 flex-1 break-words text-[13px] leading-[1.65] text-ink-secondary">
          {{ formatScheduleDate(schedule) }}
        </dd>
      </div>
      <div class="flex gap-3.5 border-b border-dashed border-line py-[11px]">
        <dt class="flex-[0_0_48px] text-xs text-ink-muted">时间</dt>
        <dd class="m-0 flex-1 break-words text-[13px] leading-[1.65] text-ink-secondary">
          {{ formatScheduleTime(schedule) }}
        </dd>
      </div>
      <div
        v-if="schedule.location"
        class="flex gap-3.5 border-b border-dashed border-line py-[11px]"
      >
        <dt class="flex-[0_0_48px] text-xs text-ink-muted">地点</dt>
        <dd class="m-0 flex-1 break-words text-[13px] leading-[1.65] text-ink-secondary">
          {{ schedule.location }}
        </dd>
      </div>
      <div
        v-if="schedule.source && schedule.source !== 'manual'"
        class="flex gap-3.5 border-b border-dashed border-line py-[11px]"
      >
        <dt class="flex-[0_0_48px] text-xs text-ink-muted">来源</dt>
        <dd class="m-0 flex-1 break-words text-[13px] leading-[1.65] text-ink-secondary">
          <a
            v-if="schedule.source_url"
            :href="schedule.source_url"
            target="_blank"
            rel="noreferrer"
            class="detail-list__source text-focus no-underline hover:underline"
          >
            {{ sourceLabel(schedule.source) }}
          </a>
          <span v-else>{{ sourceLabel(schedule.source) }}</span>
        </dd>
      </div>
      <div
        v-if="schedule.description"
        class="flex gap-3.5 border-b border-dashed border-line py-[11px]"
      >
        <dt class="flex-[0_0_48px] text-xs text-ink-muted">描述</dt>
        <dd
          class="detail-list__description m-0 flex-1 whitespace-pre-wrap break-words text-[13px] leading-[1.65] text-ink-secondary"
        >
          {{ schedule.description }}
        </dd>
      </div>
      <div class="detail-list__meta flex gap-3.5 border-b-0 border-dashed border-line py-[11px]">
        <dt class="flex-[0_0_48px] text-xs text-ink-muted">记录</dt>
        <dd class="m-0 flex-1 text-[11px] leading-[1.8] text-ink-muted">
          创建于 {{ formatLocalDateTime(schedule.created_at) }}<br />
          更新于 {{ formatLocalDateTime(schedule.updated_at) }}
        </dd>
      </div>
    </dl>

    <footer class="detail-panel__actions mt-auto flex flex-wrap items-center gap-4 pt-3">
      <el-button type="primary" :icon="EditPen" @click="emit('edit')">编辑</el-button>
      <button
        type="button"
        class="detail-panel__delete cursor-pointer border-0 bg-transparent p-0 text-xs text-danger underline-offset-4 hover:underline disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="deleting"
        @click="emit('delete')"
      >
        {{ deleting ? '删除中...' : '删除这个日程' }}
      </button>
    </footer>
  </article>
</template>
