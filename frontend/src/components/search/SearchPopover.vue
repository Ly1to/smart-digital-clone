<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { Loading, Search } from '@element-plus/icons-vue'

import { fetchSchedules } from '@/api/schedules'
import { CATEGORY_META } from '@/constants/schedule'
import type { Schedule, SearchGroup } from '@/types/schedule'
import { formatScheduleTime, groupSchedulesByDate } from '@/utils/date'
import { getErrorMessage } from '@/utils/error'

const emit = defineEmits<{
  select: [schedule: Schedule]
}>()

const rootRef = ref<HTMLElement>()
const inputRef = ref<{ focus: () => void }>()
const open = ref(false)
const keyword = ref('')
const groups = ref<SearchGroup[]>([])
const loading = ref(false)
const error = ref('')

let timer: number | null = null
let requestToken = 0

function clearTimer() {
  if (timer !== null) {
    window.clearTimeout(timer)
    timer = null
  }
}

async function runSearch() {
  const query = keyword.value.trim()
  const token = ++requestToken
  if (!query) {
    groups.value = []
    loading.value = false
    error.value = ''
    return
  }

  loading.value = true
  error.value = ''
  try {
    const schedules = await fetchSchedules({ keyword: query })
    if (token === requestToken) {
      groups.value = groupSchedulesByDate(schedules)
    }
  } catch (err) {
    if (token === requestToken) {
      groups.value = []
      error.value = getErrorMessage(err)
    }
  } finally {
    if (token === requestToken) {
      loading.value = false
    }
  }
}

watch(keyword, () => {
  clearTimer()
  if (!keyword.value.trim()) {
    requestToken += 1
    groups.value = []
    loading.value = false
    error.value = ''
    return
  }
  loading.value = true
  timer = window.setTimeout(runSearch, 300)
})

async function openSearch() {
  open.value = true
  await nextTick()
  inputRef.value?.focus()
  if (keyword.value.trim()) {
    void runSearch()
  }
}

function closeSearch() {
  open.value = false
}

function toggleSearch() {
  if (open.value) {
    closeSearch()
    return
  }
  void openSearch()
}

function selectSchedule(schedule: Schedule) {
  emit('select', schedule)
  closeSearch()
}

function handleDocumentPointerDown(event: MouseEvent) {
  if (!open.value) {
    return
  }
  const target = event.target as Node | null
  if (target && rootRef.value && !rootRef.value.contains(target)) {
    closeSearch()
  }
}

function handleDocumentKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && open.value) {
    closeSearch()
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleDocumentPointerDown)
  document.addEventListener('keydown', handleDocumentKeydown)
})

onUnmounted(() => {
  clearTimer()
  document.removeEventListener('mousedown', handleDocumentPointerDown)
  document.removeEventListener('keydown', handleDocumentKeydown)
})

defineExpose({ focusSearch: openSearch, closeSearch })
</script>

<template>
  <div ref="rootRef" class="search-popover">
    <button
      type="button"
      class="icon-button"
      :class="{ 'is-active': open }"
      aria-label="搜索日程"
      title="搜索日程（/）"
      @click="toggleSearch"
    >
      <el-icon><Search /></el-icon>
    </button>

    <div v-if="open" class="search-panel" role="dialog" aria-label="搜索日程">
      <el-input
        ref="inputRef"
        v-model="keyword"
        placeholder="搜索标题或描述"
        clearable
        :prefix-icon="Search"
        @keydown.esc="closeSearch"
      >
        <template #suffix>
          <el-icon v-if="loading" class="search-spinner" aria-label="搜索中">
            <Loading />
          </el-icon>
        </template>
      </el-input>

      <div class="search-panel__body">
        <p v-if="loading" class="search-hint">搜索中...</p>
        <div v-else-if="error" class="search-error">
          <span>{{ error }}</span>
          <el-button text type="primary" size="small" @click="runSearch">重试</el-button>
        </div>
        <p v-else-if="!keyword.trim()" class="search-hint">输入关键词搜索标题或描述</p>
        <p v-else-if="groups.length === 0" class="search-hint">没有找到匹配的日程</p>

        <div v-else class="search-results">
          <section v-for="group in groups" :key="group.date" class="search-group">
            <h4>{{ group.label }}</h4>
            <button
              v-for="item in group.items"
              :key="item.id"
              type="button"
              class="search-result"
              @click="selectSchedule(item)"
            >
              <span
                class="search-result__marker"
                :style="{
                  color: CATEGORY_META[item.category].color,
                  backgroundColor: CATEGORY_META[item.category].softColor,
                }"
              >
                {{ CATEGORY_META[item.category].shortLabel }}
              </span>
              <span class="search-result__text">
                <strong>{{ item.title }}</strong>
                <small>
                  {{ CATEGORY_META[item.category].label }} · {{ formatScheduleTime(item) }}
                </small>
              </span>
            </button>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-popover {
  position: relative;
}

.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  padding: 0;
  color: var(--color-ink-secondary);
  font-size: 17px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease;
}

.icon-button:hover,
.icon-button.is-active {
  background: var(--color-surface);
  border-color: var(--color-line);
}

.icon-button:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.search-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 50;
  width: 400px;
  max-width: calc(100vw - 24px);
  padding: 14px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-line);
  border-radius: 14px;
  box-shadow: 0 16px 40px rgb(55 46 35 / 14%);
  animation: panel-in 0.16s ease;
}

.search-panel__body {
  max-height: min(56vh, 480px);
  padding-top: 10px;
  overflow-y: auto;
}

.search-spinner {
  animation: search-spin 0.9s linear infinite;
}

@keyframes search-spin {
  to {
    transform: rotate(360deg);
  }
}

.search-hint {
  padding: 26px 8px;
  margin: 0;
  color: var(--color-ink-muted);
  font-size: 13px;
  text-align: center;
}

.search-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 8px;
  color: var(--color-danger);
  font-size: 13px;
}

.search-group h4 {
  padding: 10px 8px 6px;
  margin: 0;
  color: var(--color-ink-muted);
  font-size: 12px;
  font-weight: 500;
}

.search-result {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  width: 100%;
  padding: 9px 8px;
  text-align: left;
  background: transparent;
  border: 0;
  border-radius: 8px;
  cursor: pointer;
}

.search-result:hover {
  background: var(--color-canvas);
}

.search-result:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: -2px;
}

.search-result__marker {
  display: inline-flex;
  flex: 0 0 24px;
  align-items: center;
  justify-content: center;
  height: 24px;
  margin-top: 1px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 6px;
}

.search-result__text {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.search-result__text strong {
  overflow: hidden;
  color: var(--color-ink);
  font-size: 13px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-result__text small {
  color: var(--color-ink-muted);
  font-size: 12px;
}

@keyframes panel-in {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 767px) {
  .search-panel {
    position: fixed;
    top: 66px;
    right: 12px;
    left: 12px;
    width: auto;
    max-width: none;
  }

  .icon-button {
    width: 44px;
    height: 44px;
  }

  .search-result {
    min-height: 44px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .search-panel {
    animation: none;
  }

  .search-spinner {
    animation: none;
  }
}
</style>
