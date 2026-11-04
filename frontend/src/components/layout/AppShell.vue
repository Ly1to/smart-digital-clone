<template>
  <div class="app-shell">
    <slot name="topbar" />

    <div class="app-shell__body">
      <aside class="app-shell__sidebar">
        <slot name="sidebar" />
      </aside>

      <section class="app-shell__main">
        <slot />
      </section>

      <aside class="app-shell__panel">
        <slot name="panel" />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  overflow: hidden;
}

.app-shell__body {
  display: grid;
  flex: 1;
  grid-template-columns: 232px minmax(0, 1fr) 352px;
  gap: 16px;
  min-height: 0;
  padding: 16px 24px 24px;
}

.app-shell__sidebar {
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: thin;
}

.app-shell__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.app-shell__panel {
  min-height: 0;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: 12px;
}

@media (max-width: 1279px) {
  .app-shell__body {
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
    padding: 12px 16px 16px;
  }

  .app-shell__sidebar,
  .app-shell__panel {
    display: none;
  }
}

@media (max-width: 767px) {
  .app-shell__body {
    padding: 8px 10px calc(10px + env(safe-area-inset-bottom));
  }
}
</style>
