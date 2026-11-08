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
  <section class="account-panel" aria-label="账号">
    <div class="account-panel__heading">
      <h3>账号</h3>
      <span>已登录</span>
    </div>
    <div class="account-panel__body">
      <span class="account-panel__avatar" aria-hidden="true">
        {{ auth.user?.username.slice(0, 1).toUpperCase() }}
      </span>
      <span class="account-panel__name">{{ auth.user?.username }}</span>
      <button
        type="button"
        class="account-panel__logout"
        :disabled="loggingOut"
        @click="handleLogout"
      >
        <el-icon><SwitchButton /></el-icon>
        {{ loggingOut ? '退出中' : '退出登录' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.account-panel {
  padding-top: 2px;
}

.account-panel__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.account-panel__heading h3 {
  margin: 0;
  color: var(--color-ink-secondary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.account-panel__heading span {
  color: var(--color-ink-muted);
  font-size: 11px;
}

.account-panel__body {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 9px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: 9px;
}

.account-panel__avatar {
  display: inline-flex;
  flex: 0 0 26px;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  color: var(--color-surface);
  font-size: 11px;
  font-weight: 600;
  background: var(--color-focus);
  border-radius: 50%;
}

.account-panel__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: var(--color-ink-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-panel__logout {
  display: inline-flex;
  gap: 3px;
  align-items: center;
  padding: 4px 6px;
  color: var(--color-danger);
  font-size: 11px;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
}

.account-panel__logout:hover {
  background: #f9efed;
}

.account-panel__logout:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.account-panel__logout:focus-visible {
  outline: 2px solid var(--color-danger);
  outline-offset: 1px;
}
</style>
