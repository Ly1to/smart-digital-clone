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
  <section class="source-card">
    <div class="source-card__heading">
      <div>
        <strong>{{ title }}</strong>
        <p v-if="configured">
          @{{ username || '当前 Token 账号' }} · 最近 {{ lookbackDays }} 天
          <span v-if="tokenConfigured" class="source-card__token">Token</span>
        </p>
        <p v-else>{{ description }}</p>
      </div>
      <el-button v-if="configured" :icon="Refresh" :loading="loading" @click="emit('sync')">
        同步
      </el-button>
    </div>
    <p v-if="!configured" class="source-card__hint">{{ hint }}</p>
  </section>
</template>

<style scoped>
.source-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 13px 14px;
  background: var(--color-canvas);
  border: 1px solid var(--color-line);
  border-radius: 11px;
}

.source-card__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.source-card__heading strong {
  color: var(--color-ink);
  font-size: 13px;
  font-weight: 600;
}

.source-card__heading p {
  margin: 4px 0 0;
  color: var(--color-ink-muted);
  font-size: 11px;
  line-height: 1.6;
}

.source-card__token {
  display: inline-block;
  padding: 0 5px;
  margin-left: 4px;
  color: var(--color-focus);
  font-size: 9px;
  border: 1px solid var(--color-line);
  border-radius: 999px;
}

.source-card__hint {
  margin: 0;
  color: var(--color-ink-muted);
  font-size: 11px;
  line-height: 1.6;
}
</style>
