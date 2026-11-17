export type ThemeId = 'teal' | 'moss' | 'ochre'

export interface ThemeDefinition {
  id: ThemeId
  label: string
  description: string
  color: string
  softColor: string
}

export const DEFAULT_THEME: ThemeId = 'ochre'

export const THEMES: ThemeDefinition[] = [
  {
    id: 'teal',
    label: '青墨',
    description: '安静克制的蓝绿',
    color: '#3d6b7d',
    softColor: '#ecf1f3',
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
    description: '默认主题，陶土红，接近 Claude 配色',
    color: '#c96442',
    softColor: '#f9ece6',
  },
]

export function isThemeId(value: string | null): value is ThemeId {
  return THEMES.some((theme) => theme.id === value)
}
