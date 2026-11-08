import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'

import ThemeSwitcher from '@/components/settings/ThemeSwitcher.vue'
import { DEFAULT_THEME } from '@/constants/theme'
import { setTheme } from '@/composables/useTheme'

describe('ThemeSwitcher', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    setTheme(DEFAULT_THEME)
  })

  it('renders three theme options and switches the active theme', async () => {
    const wrapper = mount(ThemeSwitcher)

    const options = wrapper.findAll('.theme-option')
    expect(options).toHaveLength(3)
    expect(wrapper.text()).toContain('青墨')
    expect(wrapper.text()).toContain('苔绿')
    expect(wrapper.text()).toContain('赭石')

    const moss = options.find((option) => option.text().includes('苔绿'))
    expect(moss).toBeTruthy()
    await moss!.trigger('click')

    expect(moss!.attributes('aria-checked')).toBe('true')
    expect(document.documentElement.dataset.theme).toBe('moss')
    expect(window.localStorage.getItem('digital-clone-theme')).toBe('moss')
  })
})
