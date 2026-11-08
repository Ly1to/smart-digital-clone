import { readonly, ref } from 'vue'

import { DEFAULT_THEME, isThemeId, THEMES, type ThemeId } from '@/constants/theme'

const STORAGE_KEY = 'digital-clone-theme'

function readStoredTheme(): ThemeId {
  if (typeof window === 'undefined') {
    return DEFAULT_THEME
  }
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    return isThemeId(stored) ? stored : DEFAULT_THEME
  } catch {
    return DEFAULT_THEME
  }
}

const currentTheme = ref<ThemeId>(readStoredTheme())

export function setTheme(theme: ThemeId) {
  currentTheme.value = theme
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = theme
  }
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      // 隐私模式下 localStorage 可能不可用，主题仍在当前会话生效。
    }
  }
}

export function initTheme() {
  setTheme(currentTheme.value)
}

export function useTheme() {
  return {
    theme: readonly(currentTheme),
    themes: THEMES,
    setTheme,
  }
}
