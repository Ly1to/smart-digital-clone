<template>
  <div class="loading-state p-4" role="status" aria-label="加载日程中">
    <div class="loading-state__toolbar mb-4 flex items-center justify-between">
      <span
        class="loading-state__block loading-state__block--title block h-3.5 w-40 animate-pulse rounded-full bg-line"
      ></span>
      <span
        class="loading-state__block loading-state__block--action block h-3.5 w-24 animate-pulse rounded-full bg-line"
      ></span>
    </div>
    <div
      class="loading-state__grid grid grid-cols-7 gap-px overflow-hidden rounded-[10px] border border-line bg-line"
    >
      <span
        v-for="index in 35"
        :key="index"
        class="loading-state__cell min-h-[74px] p-2.5"
        :class="index % 7 === 0 ? 'is-soft bg-surface-raised' : 'bg-surface'"
      >
        <span
          class="loading-state__line block h-[7px] animate-pulse rounded-full bg-line"
          :style="{ width: `${30 + (index % 4) * 14}%` }"
        ></span>
      </span>
    </div>
  </div>
</template>
