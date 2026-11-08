import { beforeEach, describe, expect, it } from 'vitest'

import { DEFAULT_THEME, THEMES, isThemeId } from '@/constants/theme'
import { initTheme, setTheme, useTheme } from '@/composables/useTheme'

describe('theme', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    setTheme(DEFAULT_THEME)
  })

  it('provides at least three low-saturation theme colors', () => {
    expect(THEMES.length).toBeGreaterThanOrEqual(3)
    expect(new Set(THEMES.map((theme) => theme.id)).size).toBe(THEMES.length)
    expect(new Set(THEMES.map((theme) => theme.color)).size).toBe(THEMES.length)
    expect(THEMES.map((theme) => theme.label)).toEqual(
      expect.arrayContaining(['青墨', '苔绿', '赭石']),
    )
  })

  it('applies the theme to the document and persists it', () => {
    setTheme('moss')

    expect(document.documentElement.dataset.theme).toBe('moss')
    expect(window.localStorage.getItem('digital-clone-theme')).toBe('moss')
    expect(useTheme().theme.value).toBe('moss')
  })

  it('validates known theme ids', () => {
    expect(isThemeId('teal')).toBe(true)
    expect(isThemeId('moss')).toBe(true)
    expect(isThemeId('ochre')).toBe(true)
    expect(isThemeId('unknown')).toBe(false)
    expect(isThemeId(null)).toBe(false)
  })

  it('re-applies the current theme on init', () => {
    setTheme('ochre')
    initTheme()

    expect(document.documentElement.dataset.theme).toBe('ochre')
  })
})
