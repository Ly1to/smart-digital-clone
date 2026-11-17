<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Close } from '@element-plus/icons-vue'

import EmptyState from '@/components/common/EmptyState.vue'
import SourceSyncCard from '@/components/staging/SourceSyncCard.vue'
import { CATEGORY_META } from '@/constants/schedule'
import { useMediaQuery } from '@/composables/useMediaQuery'
import { useScheduleStore } from '@/stores/schedule'
import type { StagedSchedule } from '@/types/schedule'
import { getErrorMessage } from '@/utils/error'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  edit: [staged: StagedSchedule]
}>()

const store = useScheduleStore()
const isMobile = useMediaQuery('(max-width: 767px)')
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const approvingId = ref<number | null>(null)
const rejectingId = ref<number | null>(null)
const approvingAll = ref(false)
const syncMessage = ref('')
const syncTone = ref<'success' | 'warning' | 'error'>('success')

const pendingItems = computed(() =>
  store.stagedSchedules.filter((item) => item.status === 'pending'),
)
const emptyActionLabel = computed(() => {
  if (store.githubStatus?.configured) {
    return '同步 GitHub'
  }
  if (store.giteeStatus?.configured) {
    return '同步 Gitee'
  }
  return undefined
})
const today = dayjs().format('YYYY-MM-DD')

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      syncMessage.value = ''
      void store.fetchStaging()
      void store.fetchGithubStatus()
      void store.fetchGiteeStatus()
    }
  },
  { immediate: true },
)

function stagedTime(item: StagedSchedule): string {
  if (!item.start_at || !item.end_at) {
    return '今天暂无可安排时段'
  }
  if (item.all_day) {
    return `${item.start_at.slice(0, 10)} 全天`
  }
  return `建议 ${dayjs(item.start_at).format('HH:mm')}–${dayjs(item.end_at).format('HH:mm')}`
}

function sourceLabel(source: string): string {
  if (source === 'github') {
    return 'GitHub'
  }
  if (source === 'gitee') {
    return 'Gitee'
  }
  return source
}

function applySyncResult(result: Awaited<ReturnType<typeof store.syncGithub>>) {
  syncTone.value =
    result.no_slot > 0 || result.created + result.updated === 0 ? 'warning' : 'success'
  syncMessage.value = result.message
}

async function handleSyncGithub() {
  syncMessage.value = ''
  try {
    applySyncResult(await store.syncGithub())
  } catch (error) {
    syncTone.value = 'error'
    syncMessage.value = getErrorMessage(error)
  }
}

async function handleSyncGitee() {
  syncMessage.value = ''
  try {
    applySyncResult(await store.syncGitee())
  } catch (error) {
    syncTone.value = 'error'
    syncMessage.value = getErrorMessage(error)
  }
}

function handleEmptySync() {
  if (store.githubStatus?.configured) {
    void handleSyncGithub()
    return
  }
  if (store.giteeStatus?.configured) {
    void handleSyncGitee()
  }
}

async function handleApprove(item: StagedSchedule) {
  approvingId.value = item.id
  try {
    await store.approveStaged(item.id, today)
    ElMessage.success('已插入日程')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    approvingId.value = null
  }
}

async function handleApproveAll() {
  approvingAll.value = true
  try {
    const result = await store.approveAllStaged(today)
    const skipped = result.skipped.length
    if (skipped) {
      ElMessage.warning(`已插入 ${result.approved.length} 条，${skipped} 条今天没有空闲时间`)
    } else {
      ElMessage.success(`已插入 ${result.approved.length} 条日程`)
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    approvingAll.value = false
  }
}

async function handleReject(item: StagedSchedule) {
  try {
    await ElMessageBox.confirm(
      `丢弃「${item.title}」后，这条暂存日程不会写入日历。`,
      '丢弃暂存日程？',
      {
        confirmButtonText: '丢弃',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }

  rejectingId.value = item.id
  try {
    await store.rejectStaged(item.id)
    ElMessage.success('已丢弃暂存日程')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    rejectingId.value = null
  }
}
</script>

<template>
  <el-drawer
    v-model="visible"
    :direction="isMobile ? 'btt' : 'rtl'"
    :size="isMobile ? '92%' : '480px'"
    :with-header="false"
    class="staging-drawer"
  >
    <div
      class="staging flex h-full flex-col gap-3.5 overflow-y-auto px-5 pb-[calc(18px+env(safe-area-inset-bottom))] pt-[18px] max-md:px-3.5 max-md:pb-[calc(14px+env(safe-area-inset-bottom))] max-md:pt-3.5"
    >
      <header class="staging__header flex items-start justify-between gap-3">
        <div>
          <p class="staging__eyebrow mb-0.5 text-[11px] tracking-[0.12em] text-ink-muted">暂存区</p>
          <h2 class="m-0 font-display text-[21px] font-semibold text-ink">待确认日程</h2>
          <p class="staging__subtitle mt-[5px] text-xs leading-relaxed text-ink-muted">
            自动来源先进入这里，确认后才会写入日历。
          </p>
        </div>
        <button
          type="button"
          class="staging__close inline-flex h-[34px] w-[34px] flex-[0_0_auto] cursor-pointer items-center justify-center rounded-lg border-0 bg-transparent p-0 text-ink-muted hover:bg-canvas hover:text-ink"
          aria-label="关闭暂存区"
          @click="visible = false"
        >
          <el-icon><Close /></el-icon>
        </button>
      </header>

      <section class="source-cards flex flex-col gap-2.5">
        <SourceSyncCard
          title="GitHub 仓库更新"
          description="配置 GITHUB_USERNAME 后可同步最近 14 天仓库动态。"
          hint="私有仓库需要额外配置 GITHUB_TOKEN。"
          :username="store.githubStatus?.username ?? ''"
          :lookback-days="store.githubStatus?.lookback_days ?? 14"
          :configured="Boolean(store.githubStatus?.configured)"
          :token-configured="Boolean(store.githubStatus?.token_configured)"
          :loading="store.syncingGithub"
          @sync="handleSyncGithub"
        />
        <SourceSyncCard
          title="Gitee 仓库更新"
          description="配置 GITEE_USERNAME 后可同步最近 14 天仓库动态。"
          hint="私有仓库需要额外配置 GITEE_ACCESS_TOKEN。"
          :username="store.giteeStatus?.username ?? ''"
          :lookback-days="store.giteeStatus?.lookback_days ?? 14"
          :configured="Boolean(store.giteeStatus?.configured)"
          :token-configured="Boolean(store.giteeStatus?.token_configured)"
          :loading="store.syncingGitee"
          @sync="handleSyncGitee"
        />
      </section>

      <el-alert
        v-if="syncMessage"
        :title="syncMessage"
        :type="syncTone"
        :closable="false"
        show-icon
      />

      <div class="staging__toolbar flex items-center justify-between text-xs text-ink-muted">
        <span>{{ pendingItems.length }} 条待确认</span>
        <el-button
          v-if="pendingItems.length > 1"
          type="primary"
          text
          :loading="approvingAll"
          @click="handleApproveAll"
        >
          全部插入
        </el-button>
      </div>

      <el-alert
        v-if="store.stagingError"
        :title="store.stagingError"
        type="error"
        :closable="false"
        show-icon
      />

      <div
        v-if="store.stagingLoading && pendingItems.length === 0"
        class="staging__loading flex flex-col gap-2.5"
      >
        <span
          v-for="index in 3"
          :key="index"
          class="h-[92px] animate-pulse rounded-[10px] bg-canvas"
        ></span>
      </div>

      <EmptyState
        v-else-if="pendingItems.length === 0"
        title="暂存区为空"
        description="GitHub 或 Gitee 更新会先暂存在这里，等你确认后再安排到今天。"
        :action-label="emptyActionLabel"
        @action="handleEmptySync"
      />

      <ol v-else class="staged-list m-0 flex list-none flex-col gap-2.5 p-0">
        <li
          v-for="item in pendingItems"
          :key="item.id"
          class="staged-item rounded-[10px] border border-l-[3px] border-line border-l-line-strong bg-surface px-3.5 py-[13px]"
        >
          <div class="staged-item__top flex items-start gap-[9px]">
            <span
              class="staged-item__marker inline-flex h-6 flex-[0_0_24px] items-center justify-center rounded-md text-[10px] font-bold"
              :class="CATEGORY_META[item.category].badgeClass"
            >
              {{ CATEGORY_META[item.category].shortLabel }}
            </span>
            <div class="staged-item__heading min-w-0">
              <div class="staged-item__badges mb-[3px] flex flex-wrap items-center gap-1.5">
                <span
                  class="source-badge rounded-full border border-line bg-canvas px-[7px] py-px text-[10px] text-ink-secondary"
                >
                  {{ sourceLabel(item.source) }}
                </span>
                <span class="category-label text-[10px] text-ink-muted">
                  {{ CATEGORY_META[item.category].label }}
                </span>
              </div>
              <h3 class="m-0 break-words text-sm font-medium leading-[1.45] text-ink">
                {{ item.title }}
              </h3>
            </div>
          </div>

          <p class="staged-item__time ml-[33px] mt-2 text-[11px] tabular-nums text-focus">
            {{ stagedTime(item) }}
          </p>
          <p
            v-if="item.description"
            class="staged-item__description ml-[33px] mt-1.5 line-clamp-3 whitespace-pre-wrap text-[11px] leading-[1.65] text-ink-muted"
          >
            {{ item.description }}
          </p>

          <div
            class="staged-item__footer mt-2.5 flex flex-wrap items-center justify-between gap-2 border-t border-dashed border-line pt-2"
          >
            <a
              v-if="item.source_url"
              :href="item.source_url"
              target="_blank"
              rel="noreferrer"
              class="staged-item__link text-[11px] text-ink-muted no-underline hover:text-focus hover:underline"
            >
              查看仓库
            </a>
            <div
              class="staged-item__actions ml-auto flex flex-wrap gap-0.5 max-md:w-full max-md:justify-end"
            >
              <el-button text :disabled="approvingId === item.id" @click="emit('edit', item)">
                调整
              </el-button>
              <el-button
                text
                type="danger"
                :loading="rejectingId === item.id"
                @click="handleReject(item)"
              >
                丢弃
              </el-button>
              <el-button
                type="primary"
                :loading="approvingId === item.id"
                @click="handleApprove(item)"
              >
                插入日程
              </el-button>
            </div>
          </div>
        </li>
      </ol>
    </div>
  </el-drawer>
</template>
