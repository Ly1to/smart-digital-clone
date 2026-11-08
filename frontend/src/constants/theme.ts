export type ThemeId = 'teal' | 'moss' | 'ochre'

export interface ThemeDefinition {
  id: ThemeId
  label: string
  description: string
  color: string
  softColor: string
}

export const DEFAULT_THEME: ThemeId = 'teal'

export const THEMES: ThemeDefinition[] = [
  {
    id: 'teal',
    label: '青墨',
    description: '默认主题，安静克制',
    color: '#2f6f88',
    softColor: '#e8eff2',
  },
  {
    id: 'moss',
    label: '苔绿',
    description: '柔和自然，偏暖绿',
    color: '#4f6b52',
    softColor: '#edf2ee',
  },
  {
    id: 'ochre',
    label: '赭石',
    description: '温暖沉稳，偏陶土棕',
    color: '#8a5a44',
    softColor: '#f4ece7',
  },
]

export function isThemeId(value: string | null): value is ThemeId {
  return THEMES.some((theme) => theme.id === value)
}
