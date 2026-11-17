<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { SwitchButton } from '@element-plus/icons-vue'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const loggingOut = ref(false)

async function handleLogout() {
  loggingOut.value = true
  try {
    await auth.logout()
    await router.replace({ name: 'login' })
  } finally {
    loggingOut.value = false
  }
}
</script>

<template>
  <section class="account-panel pt-0.5" aria-label="账号">
    <div class="account-panel__heading mb-2 flex items-center justify-between">
      <h3 class="m-0 text-xs font-semibold tracking-[0.08em] text-ink-secondary">账号</h3>
      <span class="text-[11px] text-ink-muted">已登录</span>
    </div>
    <div
      class="account-panel__body flex items-center gap-2 rounded-[9px] border border-line bg-surface px-[9px] py-2"
    >
      <span
        class="account-panel__avatar inline-flex h-[26px] w-[26px] flex-[0_0_26px] items-center justify-center rounded-full bg-focus text-[11px] font-semibold text-surface"
        aria-hidden="true"
      >
        {{ auth.user?.username.slice(0, 1).toUpperCase() }}
      </span>
      <span
        class="account-panel__name min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-xs text-ink-secondary"
      >
        {{ auth.user?.username }}
      </span>
      <button
        type="button"
        class="account-panel__logout inline-flex cursor-pointer items-center gap-[3px] rounded-[5px] border-0 bg-transparent px-1.5 py-1 text-[11px] text-danger hover:bg-danger-soft disabled:cursor-not-allowed disabled:opacity-55"
        :disabled="loggingOut"
        @click="handleLogout"
      >
        <el-icon><SwitchButton /></el-icon>
        {{ loggingOut ? '退出中' : '退出登录' }}
      </button>
    </div>
  </section>
</template>
