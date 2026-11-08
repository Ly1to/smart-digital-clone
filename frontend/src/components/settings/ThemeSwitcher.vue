<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'

const { theme, themes, setTheme } = useTheme()
</script>

<template>
  <section class="theme-switcher" aria-label="主题色">
    <div class="theme-switcher__heading">
      <h3>主题色</h3>
      <span>{{ themes.find((item) => item.id === theme)?.label }}</span>
    </div>

    <div class="theme-options" role="radiogroup" aria-label="选择主题色">
      <button
        v-for="option in themes"
        :key="option.id"
        type="button"
        role="radio"
        class="theme-option"
        :class="{ 'is-active': theme === option.id }"
        :aria-checked="theme === option.id"
        :title="option.description"
        @click="setTheme(option.id)"
      >
        <span
          class="theme-option__swatch"
          :style="{ backgroundColor: option.color }"
          aria-hidden="true"
        ></span>
        <span class="theme-option__label">{{ option.label }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.theme-switcher {
  padding-top: 2px;
}

.theme-switcher__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.theme-switcher__heading h3 {
  margin: 0;
  color: var(--color-ink-secondary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.theme-switcher__heading span {
  color: var(--color-ink-muted);
  font-size: 11px;
}

.theme-options {
  display: flex;
  gap: 6px;
}

.theme-option {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 5px;
  align-items: center;
  min-width: 0;
  padding: 8px 4px;
  color: var(--color-ink-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: 9px;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background-color 0.15s ease;
}

.theme-option:hover {
  border-color: var(--color-line-strong);
}

.theme-option.is-active {
  border-color: var(--color-focus);
  background: var(--color-surface-raised);
}

.theme-option:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.theme-option__swatch {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  box-shadow: inset 0 0 0 2px rgb(255 253 248 / 55%);
}

.theme-option__label {
  font-size: 11px;
  line-height: 1;
}

@media (max-width: 767px) {
  .theme-option {
    min-height: 56px;
  }
}
</style>
