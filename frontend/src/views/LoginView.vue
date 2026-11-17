<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { InputInstance } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const mode = ref<'login' | 'setup'>('login')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const localError = ref('')
const statusLoading = ref(true)
const usernameRef = ref<InputInstance>()

const isSetup = computed(() => mode.value === 'setup')
const registrationEnabled = computed(() =>
  Boolean(auth.status?.initialized && auth.status.registration_enabled),
)
const displayError = computed(() => localError.value || auth.error)

function targetRoute(): string {
  const redirect = route.query.redirect
  const value = Array.isArray(redirect) ? redirect[0] : redirect
  if (typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')) {
    return value
  }
  return '/'
}

async function loadStatus() {
  statusLoading.value = true
  localError.value = ''
  const status = await auth.fetchStatus()
  if (status) {
    mode.value = status.initialized ? 'login' : 'setup'
  }
  statusLoading.value = false
  await nextTick()
  usernameRef.value?.focus()
}

onMounted(() => {
  void loadStatus()
})

async function submit() {
  localError.value = ''

  const name = username.value.trim()
  if (!name) {
    localError.value = '请输入用户名'
    return
  }
  if (isSetup.value && name.length < 3) {
    localError.value = '用户名至少需要 3 个字符'
    return
  }
  if (!password.value) {
    localError.value = '请输入密码'
    return
  }
  if (isSetup.value && password.value.length < 8) {
    localError.value = '密码至少需要 8 个字符'
    return
  }
  if (isSetup.value && password.value !== confirmPassword.value) {
    localError.value = '两次输入的密码不一致'
    return
  }

  try {
    if (isSetup.value) {
      await auth.setup(name, password.value)
    } else {
      await auth.login(name, password.value)
    }
    await router.replace(targetRoute())
  } catch {
    // 错误已由 auth store 写入 error。
  }
}

function toggleMode() {
  mode.value = isSetup.value ? 'login' : 'setup'
  localError.value = ''
  auth.error = ''
  confirmPassword.value = ''
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card" aria-labelledby="auth-title">
      <div class="auth-brand">
        <span class="auth-seal" aria-hidden="true">日</span>
        <div>
          <strong>个人日程</strong>
          <span>单用户 · 私有日历</span>
        </div>
      </div>

      <div v-if="statusLoading" class="auth-loading" role="status">
        <span></span>
        <span></span>
        <span></span>
      </div>

      <template v-else>
        <div class="auth-heading">
          <p class="auth-eyebrow">{{ isSetup ? '首次使用' : '欢迎回来' }}</p>
          <h1 id="auth-title">{{ isSetup ? '创建管理员账号' : '登录你的日程' }}</h1>
          <p class="auth-description">
            {{
              isSetup
                ? '系统只创建一个管理员账号，用于保护日程和自动来源数据。'
                : '登录后继续查看日历、暂存区和 GitHub 自动来源。'
            }}
          </p>
        </div>

        <el-alert
          v-if="displayError"
          :title="displayError"
          type="error"
          :closable="false"
          show-icon
          class="auth-error"
        />

        <el-form label-position="top" class="auth-form" @submit.prevent="submit">
          <el-form-item label="用户名">
            <el-input
              ref="usernameRef"
              v-model="username"
              :prefix-icon="User"
              autocomplete="username"
              maxlength="50"
              placeholder="输入用户名"
              @keyup.enter="submit"
            />
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="password"
              :prefix-icon="Lock"
              type="password"
              show-password
              :autocomplete="isSetup ? 'new-password' : 'current-password'"
              maxlength="128"
              placeholder="输入密码"
              @keyup.enter="submit"
            />
          </el-form-item>

          <el-form-item v-if="isSetup" label="确认密码">
            <el-input
              v-model="confirmPassword"
              :prefix-icon="Lock"
              type="password"
              show-password
              autocomplete="new-password"
              maxlength="128"
              placeholder="再次输入密码"
              @keyup.enter="submit"
            />
          </el-form-item>

          <el-button type="primary" class="auth-submit" :loading="auth.loading" @click="submit">
            {{ isSetup ? '创建并进入' : '登录' }}
          </el-button>
        </el-form>

        <div class="auth-footer">
          <button type="button" class="auth-link" @click="toggleMode">
            {{ isSetup ? '已有账号，去登录' : '首次使用？创建管理员账号' }}
          </button>
          <RouterLink
            v-if="registrationEnabled && !isSetup"
            :to="{ name: 'register', query: route.query }"
            class="auth-link"
          >
            没有账号？创建一个
          </RouterLink>
          <button
            v-if="!isSetup"
            type="button"
            class="auth-link auth-link--muted"
            @click="loadStatus"
          >
            重新检查登录状态
          </button>
        </div>
      </template>

      <p class="auth-note">账号仅保存在当前部署的数据库中。</p>
    </section>
  </main>
</template>

<style scoped>
.auth-page {
  display: grid;
  min-height: 100dvh;
  padding: 28px 16px;
  place-items: center;
  background:
    radial-gradient(circle at 12% 10%, rgb(47 111 136 / 8%), transparent 28rem),
    radial-gradient(circle at 92% 88%, rgb(138 90 68 / 7%), transparent 24rem), var(--color-canvas);
}

.auth-card {
  width: min(430px, 100%);
  padding: 24px 26px 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: 16px;
  box-shadow: 0 18px 50px rgb(55 46 35 / 10%);
}

.auth-brand {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 24px;
}

.auth-seal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  color: var(--color-surface);
  font-family: var(--font-display);
  font-size: 18px;
  background: var(--color-focus);
  border-radius: 11px;
}

.auth-brand div {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.auth-brand strong {
  color: var(--color-ink);
  font-size: 13px;
  letter-spacing: 0.04em;
}

.auth-brand span:last-child {
  color: var(--color-ink-muted);
  font-size: 11px;
}

.auth-eyebrow {
  margin: 0 0 4px;
  color: var(--color-ink-muted);
  font-size: 11px;
  letter-spacing: 0.12em;
}

.auth-heading h1 {
  margin: 0;
  color: var(--color-ink);
  font-family: var(--font-display);
  font-size: 27px;
  font-weight: 600;
  line-height: 1.3;
}

.auth-description {
  margin: 8px 0 18px;
  color: var(--color-ink-secondary);
  font-size: 12px;
  line-height: 1.7;
}

.auth-error {
  margin-bottom: 14px;
}

.auth-form :deep(.el-form-item) {
  margin-bottom: 15px;
}

.auth-form :deep(.el-form-item__label) {
  color: var(--color-ink-secondary);
  font-size: 12px;
}

.auth-submit {
  width: 100%;
  min-height: 42px;
  margin-top: 2px;
}

.auth-footer {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-start;
  margin-top: 16px;
}

.auth-link {
  padding: 0;
  color: var(--color-focus);
  font-size: 12px;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.auth-link--muted {
  color: var(--color-ink-muted);
}

.auth-link:hover {
  text-decoration: underline;
}

.auth-link:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.auth-note {
  padding-top: 14px;
  margin: 18px 0 0;
  color: var(--color-ink-muted);
  font-size: 10px;
  border-top: 1px dashed var(--color-line);
}

.auth-loading {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px 0;
}

.auth-loading span {
  height: 38px;
  background: var(--color-canvas);
  border-radius: 8px;
  animation: auth-pulse 1.3s ease-in-out infinite;
}

@keyframes auth-pulse {
  0%,
  100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth-loading span {
    animation: none;
  }
}

@media (max-width: 480px) {
  .auth-page {
    padding: 14px 10px;
    align-items: start;
    padding-top: 8vh;
  }

  .auth-card {
    padding: 20px 18px 14px;
    border-radius: 13px;
  }

  .auth-heading h1 {
    font-size: 23px;
  }
}
</style>
