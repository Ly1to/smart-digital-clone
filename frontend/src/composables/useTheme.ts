import { readonly, ref } from 'vue'

import { DEFAULT_THEME, isThemeId, THEMES, type ThemeId } from '@/constants/theme'

const STORAGE_KEY = 'digital-clone-theme'
const VERSION_KEY = 'digital-clone-theme-version'
// 提升版本号会让旧版本保存的主题一次性失效，回落到 DEFAULT_THEME。
export const THEME_VERSION = '1'

export function readStoredTheme(): ThemeId {
  if (typeof window === 'undefined') {
    return DEFAULT_THEME
  }
  try {
    if (window.localStorage.getItem(VERSION_KEY) !== THEME_VERSION) {
      return DEFAULT_THEME
    }
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
      window.localStorage.setItem(VERSION_KEY, THEME_VERSION)
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
