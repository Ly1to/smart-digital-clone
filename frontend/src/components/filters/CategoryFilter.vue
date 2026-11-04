<script setup lang="ts">
import { computed } from 'vue'

import { ALL_CATEGORIES, CATEGORY_META } from '@/constants/schedule'
import { useScheduleStore } from '@/stores/schedule'
import type { ScheduleCategory } from '@/types/schedule'

const props = defineProps<{
  dayDate: string
}>()

const store = useScheduleStore()
const counts = computed(() => store.categoryCounts)
const nothingSelected = computed(() => store.filters.categories.length === 0)
const allSelected = computed(() => store.filters.categories.length === ALL_CATEGORIES.length)

function toggleCategory(category: ScheduleCategory) {
  const selected = store.filters.categories
  const categories = selected.includes(category)
    ? selected.filter((item) => item !== category)
    : [...selected, category]
  void store.applyFilters({ ...store.filters, categories }, props.dayDate)
}

function showAll() {
  void store.applyFilters({ ...store.filters, categories: [...ALL_CATEGORIES] }, props.dayDate)
}
</script>

<template>
  <section class="category-filter" aria-label="分类筛选">
    <div class="section-heading">
      <h3>分类</h3>
      <button v-if="!allSelected" type="button" class="text-action" @click="showAll">
        显示全部
      </button>
    </div>

    <button
      v-for="category in ALL_CATEGORIES"
      :key="category"
      type="button"
      class="category-option"
      :class="{ 'is-active': store.filters.categories.includes(category) }"
      :aria-pressed="store.filters.categories.includes(category)"
      @click="toggleCategory(category)"
    >
      <span
        class="category-option__dot"
        :style="{ backgroundColor: CATEGORY_META[category].color }"
        aria-hidden="true"
      ></span>
      <span class="category-option__label">{{ CATEGORY_META[category].label }}</span>
      <span class="category-option__count">{{ counts[category] }}</span>
    </button>

    <p v-if="nothingSelected" class="category-filter__hint">未选择分类时显示全部日程</p>
  </section>
</template>

<style scoped>
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.section-heading h3 {
  margin: 0;
  color: var(--color-ink-secondary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.text-action {
  padding: 2px 4px;
  color: var(--color-focus);
  font-size: 11px;
  background: transparent;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
}

.text-action:hover {
  text-decoration: underline;
}

.text-action:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 1px;
}

.category-option {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  min-height: 38px;
  padding: 4px 8px;
  color: var(--color-ink-secondary);
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  opacity: 0.5;
  transition:
    opacity 0.15s ease,
    background-color 0.15s ease;
}

.category-option.is-active {
  opacity: 1;
}

.category-option:hover {
  opacity: 1;
  background: var(--color-surface);
}

.category-option:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: -2px;
}

.category-option__dot {
  flex: 0 0 8px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.category-option__label {
  flex: 1;
  font-size: 13px;
}

.category-option__count {
  color: var(--color-ink-muted);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.category-filter__hint {
  margin: 6px 8px 0;
  color: var(--color-ink-muted);
  font-size: 11px;
  line-height: 1.5;
}

@media (max-width: 767px) {
  .category-option {
    min-height: 44px;
  }
}
</style>
