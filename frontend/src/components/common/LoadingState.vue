<template>
  <div class="loading-state" role="status" aria-label="加载日程中">
    <div class="loading-state__toolbar">
      <span class="loading-state__block loading-state__block--title"></span>
      <span class="loading-state__block loading-state__block--action"></span>
    </div>
    <div class="loading-state__grid">
      <span
        v-for="index in 35"
        :key="index"
        class="loading-state__cell"
        :class="{ 'is-soft': index % 7 === 0 }"
      >
        <span class="loading-state__line" :style="{ width: `${30 + (index % 4) * 14}%` }"></span>
      </span>
    </div>
  </div>
</template>

<style scoped>
.loading-state {
  padding: 16px;
}

.loading-state__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.loading-state__block,
.loading-state__line,
.loading-state__cell {
  background: linear-gradient(90deg, var(--color-line) 25%, #f7f1e7 37%, var(--color-line) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}

.loading-state__block {
  display: block;
  height: 14px;
  border-radius: 999px;
}

.loading-state__block--title {
  width: 160px;
}

.loading-state__block--action {
  width: 92px;
}

.loading-state__grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  background: var(--color-line);
  border: 1px solid var(--color-line);
  border-radius: 10px;
}

.loading-state__cell {
  min-height: 74px;
  padding: 10px 6px;
  background-color: var(--color-surface);
  background-image: none;
  animation: none;
}

.loading-state__cell.is-soft {
  background-color: var(--color-surface-raised);
}

.loading-state__line {
  display: block;
  height: 7px;
  border-radius: 999px;
}

@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .loading-state__block,
  .loading-state__line {
    animation: none;
  }
}
</style>
