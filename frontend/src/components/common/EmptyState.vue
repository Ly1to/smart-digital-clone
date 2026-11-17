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
  <div
    class="empty-state flex flex-col items-center justify-center px-4 py-7 text-center text-ink-muted"
  >
    <span class="empty-state__mark mb-2 text-[22px] text-line-strong" aria-hidden="true">○</span>
    <p class="empty-state__title m-0 text-sm text-ink-secondary">{{ title }}</p>
    <p v-if="description" class="empty-state__description mt-1.5 text-xs leading-relaxed">
      {{ description }}
    </p>
    <el-button v-if="actionLabel" text type="primary" @click="emit('action')">
      {{ actionLabel }}
    </el-button>
  </div>
</template>
