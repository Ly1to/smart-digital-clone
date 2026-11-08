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
    <div class="staging">
      <header class="staging__header">
        <div>
          <p class="staging__eyebrow">暂存区</p>
          <h2>待确认日程</h2>
          <p class="staging__subtitle">自动来源先进入这里，确认后才会写入日历。</p>
        </div>
        <button
          type="button"
          class="staging__close"
          aria-label="关闭暂存区"
          @click="visible = false"
        >
          <el-icon><Close /></el-icon>
        </button>
      </header>

      <section class="source-cards">
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

      <div class="staging__toolbar">
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

      <div v-if="store.stagingLoading && pendingItems.length === 0" class="staging__loading">
        <span v-for="index in 3" :key="index"></span>
      </div>

      <EmptyState
        v-else-if="pendingItems.length === 0"
        title="暂存区为空"
        description="GitHub 或 Gitee 更新会先暂存在这里，等你确认后再安排到今天。"
        :action-label="emptyActionLabel"
        @action="handleEmptySync"
      />

      <ol v-else class="staged-list">
        <li v-for="item in pendingItems" :key="item.id" class="staged-item">
          <div class="staged-item__top">
            <span
              class="staged-item__marker"
              :style="{
                color: CATEGORY_META[item.category].color,
                backgroundColor: CATEGORY_META[item.category].softColor,
              }"
            >
              {{ CATEGORY_META[item.category].shortLabel }}
            </span>
            <div class="staged-item__heading">
              <div class="staged-item__badges">
                <span class="source-badge">{{ sourceLabel(item.source) }}</span>
                <span class="category-label">{{ CATEGORY_META[item.category].label }}</span>
              </div>
              <h3>{{ item.title }}</h3>
            </div>
          </div>

          <p class="staged-item__time">{{ stagedTime(item) }}</p>
          <p v-if="item.description" class="staged-item__description">
            {{ item.description }}
          </p>

          <div class="staged-item__footer">
            <a
              v-if="item.source_url"
              :href="item.source_url"
              target="_blank"
              rel="noreferrer"
              class="staged-item__link"
            >
              查看仓库
            </a>
            <div class="staged-item__actions">
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

<style scoped>
.staging {
  display: flex;
  flex-direction: column;
  gap: 14px;
  height: 100%;
  padding: 18px 20px env(safe-area-inset-bottom);
  overflow-y: auto;
}

.staging__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.staging__eyebrow {
  margin: 0 0 2px;
  color: var(--color-ink-muted);
  font-size: 11px;
  letter-spacing: 0.12em;
}

.staging__header h2 {
  margin: 0;
  color: var(--color-ink);
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 600;
}

.staging__subtitle {
  margin: 5px 0 0;
  color: var(--color-ink-muted);
  font-size: 12px;
  line-height: 1.6;
}

.staging__close {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  color: var(--color-ink-muted);
  background: transparent;
  border: 0;
  border-radius: 8px;
  cursor: pointer;
}

.staging__close:hover {
  color: var(--color-ink);
  background: var(--color-canvas);
}

.staging__close:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 1px;
}

.source-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.staging__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--color-ink-muted);
  font-size: 12px;
}

.staging__loading {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.staging__loading span {
  height: 92px;
  background: var(--color-canvas);
  border-radius: 10px;
  animation: pulse 1.4s ease-in-out infinite;
}

.staged-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.staged-item {
  padding: 13px 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-left: 3px solid var(--color-line-strong);
  border-radius: 10px;
}

.staged-item__top {
  display: flex;
  gap: 9px;
  align-items: flex-start;
}

.staged-item__marker {
  display: inline-flex;
  flex: 0 0 24px;
  align-items: center;
  justify-content: center;
  height: 24px;
  font-size: 10px;
  font-weight: 700;
  border-radius: 6px;
}

.staged-item__heading {
  min-width: 0;
}

.staged-item__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 3px;
}

.source-badge {
  padding: 1px 7px;
  color: var(--color-ink-secondary);
  font-size: 10px;
  background: var(--color-canvas);
  border: 1px solid var(--color-line);
  border-radius: 999px;
}

.category-label {
  color: var(--color-ink-muted);
  font-size: 10px;
}

.staged-item h3 {
  margin: 0;
  color: var(--color-ink);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.45;
  word-break: break-word;
}

.staged-item__time {
  margin: 8px 0 0 33px;
  color: var(--color-focus);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.staged-item__description {
  display: -webkit-box;
  margin: 6px 0 0 33px;
  overflow: hidden;
  color: var(--color-ink-muted);
  font-size: 11px;
  line-height: 1.65;
  white-space: pre-wrap;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.staged-item__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-line);
}

.staged-item__link {
  color: var(--color-ink-muted);
  font-size: 11px;
  text-decoration: none;
}

.staged-item__link:hover {
  color: var(--color-focus);
  text-decoration: underline;
}

.staged-item__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-left: auto;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.65;
  }
  50% {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .staging__loading span {
    animation: none;
  }
}

@media (max-width: 767px) {
  .staging {
    padding: 14px 14px calc(14px + env(safe-area-inset-bottom));
  }

  .staged-item__actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
