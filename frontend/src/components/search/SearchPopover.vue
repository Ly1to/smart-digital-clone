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
  <div ref="rootRef" class="search-popover relative">
    <button
      type="button"
      class="icon-button inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border bg-transparent p-0 text-[16px] text-ink-secondary transition-colors hover:border-line hover:bg-surface hover:shadow-soft max-md:h-11 max-md:w-11"
      :class="open ? 'is-active border-line bg-surface' : 'border-transparent'"
      aria-label="搜索日程"
      title="搜索日程（/）"
      @click="toggleSearch"
    >
      <el-icon><Search /></el-icon>
    </button>

    <div
      v-if="open"
      class="search-panel absolute right-0 top-[calc(100%+10px)] z-50 w-[400px] max-w-[calc(100vw-24px)] animate-[panel-in_0.16s_ease] rounded-2xl border border-line bg-surface-raised p-3.5 shadow-popover max-md:fixed max-md:left-3 max-md:right-3 max-md:top-[66px] max-md:w-auto max-md:max-w-none"
      role="dialog"
      aria-label="搜索日程"
    >
      <el-input
        ref="inputRef"
        v-model="keyword"
        placeholder="搜索标题或描述"
        clearable
        :prefix-icon="Search"
        @keydown.esc="closeSearch"
      >
        <template #suffix>
          <el-icon v-if="loading" class="animate-spin" aria-label="搜索中">
            <Loading />
          </el-icon>
        </template>
      </el-input>

      <div class="search-panel__body max-h-[min(56vh,480px)] overflow-y-auto pt-2.5">
        <p
          v-if="loading"
          class="search-hint m-0 px-2 py-[26px] text-center text-[13px] text-ink-muted"
        >
          搜索中...
        </p>
        <div
          v-else-if="error"
          class="search-error flex items-center justify-between gap-3 px-2 py-3 text-[13px] text-danger"
        >
          <span>{{ error }}</span>
          <el-button text type="primary" size="small" @click="runSearch">重试</el-button>
        </div>
        <p
          v-else-if="!keyword.trim()"
          class="search-hint m-0 px-2 py-[26px] text-center text-[13px] text-ink-muted"
        >
          输入关键词搜索标题或描述
        </p>
        <p
          v-else-if="groups.length === 0"
          class="search-hint m-0 px-2 py-[26px] text-center text-[13px] text-ink-muted"
        >
          没有找到匹配的日程
        </p>

        <div v-else class="search-results">
          <section v-for="group in groups" :key="group.date" class="search-group">
            <h4 class="m-0 px-2 pb-1.5 pt-2.5 text-xs font-medium text-ink-muted">
              {{ group.label }}
            </h4>
            <button
              v-for="item in group.items"
              :key="item.id"
              type="button"
              class="search-result flex w-full cursor-pointer items-start gap-2.5 rounded-xl border-0 bg-transparent px-2 py-2.5 text-left transition-colors hover:bg-canvas max-md:min-h-11"
              @click="selectSchedule(item)"
            >
              <span
                class="search-result__marker mt-px inline-flex h-6 flex-[0_0_24px] items-center justify-center rounded-md text-[11px] font-semibold"
                :class="CATEGORY_META[item.category].badgeClass"
              >
                {{ CATEGORY_META[item.category].shortLabel }}
              </span>
              <span class="search-result__text flex min-w-0 flex-col gap-[3px]">
                <strong
                  class="overflow-hidden text-ellipsis whitespace-nowrap text-[13px] font-medium text-ink"
                >
                  {{ item.title }}
                </strong>
                <small class="text-xs text-ink-muted">
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
