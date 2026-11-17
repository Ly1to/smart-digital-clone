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
    class="auth-page grid min-h-dvh place-items-center bg-canvas bg-[radial-gradient(circle_at_12%_10%,rgb(47_111_136/8%),transparent_28rem),radial-gradient(circle_at_92%_88%,rgb(138_90_68/7%),transparent_24rem)] px-4 py-7 max-md:items-start max-md:px-2.5 max-md:pt-[8vh]"
  >
    <section
      class="auth-card w-[min(430px,100%)] rounded-2xl border border-line bg-surface px-[26px] pb-[18px] pt-6 shadow-card max-md:rounded-[13px] max-md:px-[18px] max-md:pb-3.5 max-md:pt-5"
      aria-labelledby="auth-title"
    >
      <div class="auth-brand mb-6 flex items-center gap-2.5">
        <span
          class="auth-seal inline-flex h-[38px] w-[38px] items-center justify-center rounded-[11px] bg-focus font-display text-lg text-surface"
          aria-hidden="true"
        >
          日
        </span>
        <div class="flex flex-col gap-px">
          <strong class="text-[13px] tracking-[0.04em] text-ink">个人日程</strong>
          <span class="text-[11px] text-ink-muted">单用户 · 私有日历</span>
        </div>
      </div>

      <div v-if="statusLoading" class="auth-loading flex flex-col gap-2.5 py-5" role="status">
        <span
          v-for="index in 3"
          :key="index"
          class="h-[38px] animate-pulse rounded-lg bg-canvas"
        ></span>
      </div>

      <template v-else>
        <div class="auth-heading">
          <p class="auth-eyebrow mb-1 text-[11px] tracking-[0.12em] text-ink-muted">
            {{ isSetup ? '首次使用' : '欢迎回来' }}
          </p>
          <h1
            id="auth-title"
            class="m-0 font-display text-[27px] font-semibold leading-[1.3] text-ink max-md:text-[23px]"
          >
            {{ isSetup ? '创建管理员账号' : '登录你的日程' }}
          </h1>
          <p class="auth-description mb-[18px] mt-2 text-xs leading-[1.7] text-ink-secondary">
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
          class="mb-3.5"
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
            class="mt-0.5 min-h-[42px]! w-full"
            :loading="auth.loading"
            @click="submit"
          >
            {{ isSetup ? '创建并进入' : '登录' }}
          </el-button>
        </el-form>

        <div class="auth-footer mt-4 flex flex-col items-start gap-1.5">
          <button
            type="button"
            class="auth-link cursor-pointer border-0 bg-transparent p-0 text-xs text-focus hover:underline"
            @click="toggleMode"
          >
            {{ isSetup ? '已有账号，去登录' : '首次使用？创建管理员账号' }}
          </button>
          <RouterLink
            v-if="registrationEnabled && !isSetup"
            :to="{ name: 'register', query: route.query }"
            class="text-xs text-focus hover:underline"
          >
            没有账号？创建一个
          </RouterLink>
          <button
            v-if="!isSetup"
            type="button"
            class="auth-link auth-link--muted cursor-pointer border-0 bg-transparent p-0 text-xs text-ink-muted hover:underline"
            @click="loadStatus"
          >
            重新检查登录状态
          </button>
        </div>
      </template>

      <p
        class="auth-note mt-[18px] border-t border-dashed border-line pt-3.5 text-[10px] text-ink-muted"
      >
        账号仅保存在当前部署的数据库中。
      </p>
    </section>
  </main>
</template>
