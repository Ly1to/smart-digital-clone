<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { InputInstance } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const localError = ref('')
const statusLoading = ref(true)
const registrationEnabled = ref(false)
const usernameRef = ref<InputInstance>()

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
    registrationEnabled.value = status.registration_enabled
    if (!status.initialized) {
      await router.replace({ name: 'login' })
      return
    }
  }
  statusLoading.value = false
  await nextTick()
  if (registrationEnabled.value) {
    usernameRef.value?.focus()
  }
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
  if (name.length < 3) {
    localError.value = '用户名至少需要 3 个字符'
    return
  }
  if (!password.value) {
    localError.value = '请输入密码'
    return
  }
  if (password.value.length < 8) {
    localError.value = '密码至少需要 8 个字符'
    return
  }
  if (password.value !== confirmPassword.value) {
    localError.value = '两次输入的密码不一致'
    return
  }

  try {
    await auth.register(name, password.value)
    await router.replace(targetRoute())
  } catch {
    // 错误已由 auth store 写入 error。
  }
}
</script>

<template>
  <main
    class="auth-page relative grid min-h-dvh place-items-center overflow-hidden bg-canvas bg-[radial-gradient(circle_at_50%_-8%,rgb(201_100_66/10%),transparent_34rem),radial-gradient(circle_at_88%_100%,rgb(20_20_19/4%),transparent_30rem)] px-4 py-10 max-md:items-start max-md:px-3 max-md:pt-[9vh]"
  >
    <section
      class="auth-card relative z-10 w-[min(420px,100%)] rounded-[26px] border border-line bg-surface px-8 pb-6 pt-8 shadow-card max-md:rounded-3xl max-md:px-6 max-md:pb-5 max-md:pt-6"
      aria-labelledby="register-title"
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
          <span class="text-[11px] tracking-[0.02em] text-ink-muted">独立空间 · 私密日程</span>
        </div>
      </div>

      <div v-if="statusLoading" class="auth-loading flex flex-col gap-2.5 py-6" role="status">
        <span
          v-for="index in 3"
          :key="index"
          class="h-[42px] animate-pulse rounded-[10px] bg-canvas"
        ></span>
      </div>

      <template v-else-if="!registrationEnabled">
        <div class="auth-heading">
          <p
            class="auth-eyebrow mb-2 text-[10px] font-medium uppercase tracking-[0.2em] text-ink-muted"
          >
            注册未开放
          </p>
          <h1
            id="register-title"
            class="m-0 font-display text-[31px] font-semibold leading-[1.22] tracking-[-0.015em] text-ink"
          >
            当前部署不开放注册
          </h1>
          <p class="auth-description mb-5 mt-3 text-[12.5px] leading-[1.75] text-ink-secondary">
            请联系管理员开通账号，或返回登录页使用已有账号。
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
        <RouterLink
          :to="{ name: 'login', query: route.query }"
          class="text-[12px] text-focus underline-offset-4 hover:underline"
        >
          返回登录
        </RouterLink>
      </template>

      <template v-else>
        <div class="auth-heading">
          <p
            class="auth-eyebrow mb-2 text-[10px] font-medium uppercase tracking-[0.2em] text-ink-muted"
          >
            创建账号
          </p>
          <h1
            id="register-title"
            class="m-0 font-display text-[31px] font-semibold leading-[1.22] tracking-[-0.015em] text-ink max-md:text-[27px]"
          >
            注册你的日程空间
          </h1>
          <p class="auth-description mb-5 mt-3 text-[12.5px] leading-[1.75] text-ink-secondary">
            每个账号拥有独立的日程和暂存区，登录后即可开始安排时间。
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
              autocomplete="new-password"
              maxlength="128"
              placeholder="至少 8 个字符"
              @keyup.enter="submit"
            />
          </el-form-item>

          <el-form-item label="确认密码">
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
            创建账号并进入
          </el-button>
        </el-form>

        <div class="auth-footer mt-6 flex flex-col items-start gap-2">
          <RouterLink
            :to="{ name: 'login', query: route.query }"
            class="text-[12px] text-focus underline-offset-4 hover:underline"
          >
            已有账号，返回登录
          </RouterLink>
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
