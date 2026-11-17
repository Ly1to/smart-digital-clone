<template>
  <div class="app-shell flex h-dvh flex-col overflow-hidden">
    <slot name="topbar" />

    <div
      class="app-shell__body grid min-h-0 flex-1 gap-5 px-5 pb-5 pt-4 max-xl:grid-cols-1 max-xl:gap-2.5 max-xl:px-4 max-xl:pb-4 max-xl:pt-3 max-md:px-2.5 max-md:pb-[calc(10px+env(safe-area-inset-bottom))] max-md:pt-2 xl:grid-cols-[236px_minmax(0,1fr)_360px]"
    >
      <aside class="app-shell__sidebar hidden min-h-0 overflow-y-auto xl:block">
        <slot name="sidebar" />
      </aside>

      <section class="app-shell__main flex min-h-0 min-w-0 flex-col">
        <slot />
      </section>

      <aside
        class="app-shell__panel hidden min-h-0 overflow-hidden rounded-2xl border border-line bg-surface shadow-soft xl:block"
      >
        <slot name="panel" />
      </aside>
    </div>
  </div>
</template>
