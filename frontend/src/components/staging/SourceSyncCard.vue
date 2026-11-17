<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'

defineProps<{
  title: string
  description: string
  hint: string
  username: string
  lookbackDays: number
  configured: boolean
  tokenConfigured: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  sync: []
}>()
</script>

<template>
  <section
    class="source-card flex flex-col gap-2.5 rounded-xl border border-line bg-canvas px-3.5 py-3.5"
  >
    <div class="source-card__heading flex items-start justify-between gap-3">
      <div>
        <strong class="text-[13px] font-semibold text-ink">{{ title }}</strong>
        <p v-if="configured" class="mt-1 text-[11px] leading-relaxed text-ink-muted">
          @{{ username || '当前 Token 账号' }} · 最近 {{ lookbackDays }} 天
          <span
            v-if="tokenConfigured"
            class="source-card__token ml-1 inline-block rounded-full border border-line px-[5px] text-[9px] text-focus"
          >
            Token
          </span>
        </p>
        <p v-else class="mt-1 text-[11px] leading-relaxed text-ink-muted">{{ description }}</p>
      </div>
      <el-button v-if="configured" :icon="Refresh" :loading="loading" @click="emit('sync')">
        同步
      </el-button>
    </div>
    <p v-if="!configured" class="source-card__hint m-0 text-[11px] leading-relaxed text-ink-muted">
      {{ hint }}
    </p>
  </section>
</template>
