<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'

const { theme, themes, setTheme } = useTheme()
</script>

<template>
  <section class="theme-switcher pt-0.5" aria-label="主题色">
    <div class="theme-switcher__heading mb-2 flex items-center justify-between">
      <h3 class="m-0 text-xs font-semibold tracking-[0.08em] text-ink-secondary">主题色</h3>
      <span class="text-[11px] text-ink-muted">
        {{ themes.find((item) => item.id === theme)?.label }}
      </span>
    </div>

    <div class="theme-options flex gap-1.5" role="radiogroup" aria-label="选择主题色">
      <button
        v-for="option in themes"
        :key="option.id"
        type="button"
        role="radio"
        class="theme-option flex min-w-0 flex-1 cursor-pointer flex-col items-center gap-1.5 rounded-[9px] border px-1 py-2 text-ink-secondary transition-colors hover:border-line-strong max-md:min-h-14"
        :class="theme === option.id ? 'border-focus bg-surface-raised' : 'border-line bg-surface'"
        :aria-checked="theme === option.id"
        :title="option.description"
        @click="setTheme(option.id)"
      >
        <span
          class="theme-option__swatch h-[18px] w-[18px] rounded-full shadow-[inset_0_0_0_2px_rgb(255_253_248/55%)]"
          :style="{ backgroundColor: option.color }"
          aria-hidden="true"
        ></span>
        <span class="theme-option__label text-[11px] leading-none">{{ option.label }}</span>
      </button>
    </div>
  </section>
</template>
