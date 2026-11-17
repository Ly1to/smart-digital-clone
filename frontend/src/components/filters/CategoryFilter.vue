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
  <section
    class="category-filter rounded-2xl border border-line bg-surface p-3.5 shadow-soft"
    aria-label="分类筛选"
  >
    <div class="section-heading mb-2 flex items-center justify-between">
      <h3 class="m-0 text-xs font-semibold tracking-[0.08em] text-ink-secondary">分类</h3>
      <button
        v-if="!allSelected"
        type="button"
        class="text-action cursor-pointer rounded border-0 bg-transparent px-1 py-0.5 text-[11px] text-focus hover:underline"
        @click="showAll"
      >
        显示全部
      </button>
    </div>

    <button
      v-for="category in ALL_CATEGORIES"
      :key="category"
      type="button"
      class="category-option flex min-h-[38px] w-full cursor-pointer items-center gap-2.5 rounded-full border border-transparent px-2.5 py-1 text-left text-ink-secondary transition-colors hover:bg-canvas hover:opacity-100 max-md:min-h-11"
      :class="store.filters.categories.includes(category) ? 'is-active opacity-100' : 'opacity-50'"
      :aria-pressed="store.filters.categories.includes(category)"
      @click="toggleCategory(category)"
    >
      <span
        class="category-option__dot h-2 w-2 flex-[0_0_8px] rounded-full"
        :class="CATEGORY_META[category].dotClass"
        aria-hidden="true"
      ></span>
      <span class="category-option__label flex-1 text-[13px]">
        {{ CATEGORY_META[category].label }}
      </span>
      <span class="category-option__count text-[11px] tabular-nums text-ink-muted">
        {{ counts[category] }}
      </span>
    </button>

    <p
      v-if="nothingSelected"
      class="category-filter__hint mx-2 mt-1.5 text-[11px] leading-normal text-ink-muted"
    >
      未选择分类时显示全部日程
    </p>
  </section>
</template>
