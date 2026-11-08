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
  <article class="detail-panel">
    <header class="detail-panel__header">
      <div class="detail-panel__heading">
        <span
          class="detail-panel__category"
          :style="{
            color: CATEGORY_META[schedule.category].color,
            backgroundColor: CATEGORY_META[schedule.category].softColor,
          }"
        >
          {{ CATEGORY_META[schedule.category].label }}
        </span>
        <span class="detail-panel__status" :class="STATUS_META[schedule.status].className">
          <span v-if="STATUS_META[schedule.status].icon" aria-hidden="true">
            {{ STATUS_META[schedule.status].icon }}
          </span>
          {{ STATUS_META[schedule.status].label }}
        </span>
      </div>
      <button
        type="button"
        class="detail-panel__close"
        aria-label="关闭日程详情"
        @click="emit('close')"
      >
        <el-icon><Close /></el-icon>
      </button>
    </header>

    <h2 class="detail-panel__title" :class="STATUS_META[schedule.status].className">
      {{ schedule.title }}
    </h2>

    <dl class="detail-list">
      <div>
        <dt>日期</dt>
        <dd>{{ formatScheduleDate(schedule) }}</dd>
      </div>
      <div>
        <dt>时间</dt>
        <dd>{{ formatScheduleTime(schedule) }}</dd>
      </div>
      <div v-if="schedule.location">
        <dt>地点</dt>
        <dd>{{ schedule.location }}</dd>
      </div>
      <div v-if="schedule.source && schedule.source !== 'manual'">
        <dt>来源</dt>
        <dd>
          <a
            v-if="schedule.source_url"
            :href="schedule.source_url"
            target="_blank"
            rel="noreferrer"
            class="detail-list__source"
          >
            {{ sourceLabel(schedule.source) }}
          </a>
          <span v-else>{{ sourceLabel(schedule.source) }}</span>
        </dd>
      </div>
      <div v-if="schedule.description">
        <dt>描述</dt>
        <dd class="detail-list__description">{{ schedule.description }}</dd>
      </div>
      <div class="detail-list__meta">
        <dt>记录</dt>
        <dd>
          创建于 {{ formatLocalDateTime(schedule.created_at) }}<br />
          更新于 {{ formatLocalDateTime(schedule.updated_at) }}
        </dd>
      </div>
    </dl>

    <footer class="detail-panel__actions">
      <el-button type="primary" :icon="EditPen" @click="emit('edit')">编辑</el-button>
      <button
        type="button"
        class="detail-panel__delete"
        :disabled="deleting"
        @click="emit('delete')"
      >
        {{ deleting ? '删除中...' : '删除这个日程' }}
      </button>
    </footer>
  </article>
</template>

<style scoped>
.detail-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 18px;
  overflow-y: auto;
}

.detail-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.detail-panel__heading {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.detail-panel__category,
.detail-panel__status {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding: 3px 9px;
  font-size: 11px;
  border-radius: 999px;
}

.detail-panel__status {
  color: var(--color-ink-muted);
  background: var(--color-canvas);
}

.detail-panel__status.status-completed {
  color: var(--color-success);
}

.detail-panel__status.status-cancelled {
  color: var(--color-danger);
}

.detail-panel__close {
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

.detail-panel__close:hover {
  color: var(--color-ink);
  background: var(--color-canvas);
}

.detail-panel__close:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 1px;
}

.detail-panel__title {
  margin: 14px 0 6px;
  color: var(--color-ink);
  font-size: 22px;
  font-weight: 600;
  line-height: 1.35;
  word-break: break-word;
}

.detail-panel__title.status-cancelled {
  color: var(--color-ink-muted);
  text-decoration: line-through;
}

.detail-panel__title.status-completed {
  color: var(--color-ink-secondary);
}

.detail-list {
  padding: 4px 0 0;
  margin: 0 0 24px;
}

.detail-list > div {
  display: flex;
  gap: 14px;
  padding: 11px 0;
  border-bottom: 1px dashed var(--color-line);
}

.detail-list dt {
  flex: 0 0 48px;
  color: var(--color-ink-muted);
  font-size: 12px;
}

.detail-list dd {
  flex: 1;
  margin: 0;
  color: var(--color-ink-secondary);
  font-size: 13px;
  line-height: 1.65;
  word-break: break-word;
}

.detail-list__description {
  white-space: pre-wrap;
}

.detail-list__source {
  color: var(--color-focus);
  text-decoration: none;
}

.detail-list__source:hover {
  text-decoration: underline;
}

.detail-list__meta {
  border-bottom: 0 !important;
}

.detail-list__meta dd {
  color: var(--color-ink-muted);
  font-size: 11px;
  line-height: 1.8;
}

.detail-panel__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-top: auto;
  padding-top: 12px;
}

.detail-panel__delete {
  padding: 4px 0;
  color: var(--color-danger);
  font-size: 12px;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.detail-panel__delete:hover {
  text-decoration: underline;
}

.detail-panel__delete:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.detail-panel__delete:focus-visible {
  outline: 2px solid var(--color-danger);
  outline-offset: 2px;
}
</style>
