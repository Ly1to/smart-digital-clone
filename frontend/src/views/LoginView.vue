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
  <main
    class="auth-page relative grid min-h-dvh place-items-center overflow-hidden bg-canvas bg-[radial-gradient(circle_at_50%_-8%,rgb(201_100_66/10%),transparent_34rem),radial-gradient(circle_at_88%_100%,rgb(20_20_19/4%),transparent_30rem)] px-4 py-10 max-md:items-start max-md:px-3 max-md:pt-[9vh]"
  >
    <section
      class="auth-card relative z-10 w-[min(420px,100%)] rounded-[26px] border border-line bg-surface px-8 pb-6 pt-8 shadow-card max-md:rounded-3xl max-md:px-6 max-md:pb-5 max-md:pt-6"
      aria-labelledby="auth-title"
    >
      <div class="auth-brand mb-7 flex items-center gap-3">
        <span
          class="auth-seal inline-flex h-9 w-9 items-center justify-center rounded-[11px] bg-focus font-display text-[17px] text-surface shadow-[0_1px_2px_rgb(169_79_50/25%)]"
          aria-hidden="true"
        >
          日
        </span>
        <div class="flex flex-col gap-px">
          <strong class="font-display text-[15px] font-semibold tracking-[0.01em] text-ink">
            个人日程
          </strong>
          <span class="text-[11px] tracking-[0.02em] text-ink-muted">私有日历 · 安静安排</span>
        </div>
      </div>

      <div v-if="statusLoading" class="auth-loading flex flex-col gap-2.5 py-6" role="status">
        <span
          v-for="index in 3"
          :key="index"
          class="h-[42px] animate-pulse rounded-[10px] bg-canvas"
        ></span>
      </div>

      <template v-else>
        <div class="auth-heading">
          <p
            class="auth-eyebrow mb-2 text-[10px] font-medium uppercase tracking-[0.2em] text-ink-muted"
          >
            {{ isSetup ? '首次使用' : '欢迎回来' }}
          </p>
          <h1
            id="auth-title"
            class="m-0 font-display text-[31px] font-semibold leading-[1.22] tracking-[-0.015em] text-ink max-md:text-[27px]"
          >
            {{ isSetup ? '创建管理员账号' : '登录你的日程' }}
          </h1>
          <p class="auth-description mb-5 mt-3 text-[12.5px] leading-[1.75] text-ink-secondary">
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
          class="mb-4"
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

          <el-button
            type="primary"
            class="mt-1.5 min-h-[44px]! w-full text-[13px]!"
            :loading="auth.loading"
            @click="submit"
          >
            {{ isSetup ? '创建并进入' : '登录' }}
          </el-button>
        </el-form>

        <div class="auth-footer mt-6 flex flex-col items-start gap-2">
          <button
            type="button"
            class="auth-link cursor-pointer border-0 bg-transparent p-0 text-[12px] text-focus underline-offset-4 hover:underline"
            @click="toggleMode"
          >
            {{ isSetup ? '已有账号，去登录' : '首次使用？创建管理员账号' }}
          </button>
          <RouterLink
            v-if="registrationEnabled && !isSetup"
            :to="{ name: 'register', query: route.query }"
            class="text-[12px] text-focus underline-offset-4 hover:underline"
          >
            没有账号？创建一个
          </RouterLink>
          <button
            v-if="!isSetup"
            type="button"
            class="auth-link auth-link--muted cursor-pointer border-0 bg-transparent p-0 text-[12px] text-ink-muted underline-offset-4 hover:underline"
            @click="loadStatus"
          >
            重新检查登录状态
          </button>
        </div>
      </template>

      <p
        class="auth-note mt-6 border-t border-line pt-4 text-[10.5px] leading-relaxed text-ink-muted"
      >
        账号仅保存在当前部署的数据库中。
      </p>
    </section>
  </main>
</template>
