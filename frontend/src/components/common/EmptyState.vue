<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  actionLabel?: string
}>()

const emit = defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="empty-state">
    <span class="empty-state__mark" aria-hidden="true">○</span>
    <p class="empty-state__title">{{ title }}</p>
    <p v-if="description" class="empty-state__description">{{ description }}</p>
    <el-button v-if="actionLabel" text type="primary" @click="emit('action')">
      {{ actionLabel }}
    </el-button>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28px 16px;
  text-align: center;
  color: var(--color-ink-muted);
}

.empty-state__mark {
  margin-bottom: 8px;
  font-size: 22px;
  color: var(--color-line-strong);
}

.empty-state__title {
  margin: 0;
  color: var(--color-ink-secondary);
  font-size: 14px;
}

.empty-state__description {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.6;
}
</style>
