import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import * as authApi from '@/api/auth'
import { AUTH_TOKEN_KEY } from '@/constants/auth'
import { useAuthStore } from '@/stores/auth'
import type { AuthUser, TokenResponse } from '@/types/auth'

vi.mock('@/api/auth', () => ({
  fetchAuthStatus: vi.fn(),
  login: vi.fn(),
  setupAccount: vi.fn(),
  fetchMe: vi.fn(),
  logout: vi.fn(),
}))

const user: AuthUser = {
  id: 1,
  username: 'owner',
  created_at: '2026-11-08T00:00:00Z',
}

const session: TokenResponse = {
  access_token: 'token-123',
  token_type: 'bearer',
  user,
}

describe('auth store', () => {
  beforeEach(() => {
    window.localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('logs in and persists the token', async () => {
    vi.mocked(authApi.login).mockResolvedValue(session)
    const auth = useAuthStore()

    await auth.login('owner', 'password-123')

    expect(auth.isAuthenticated).toBe(true)
    expect(auth.user?.username).toBe('owner')
    expect(auth.token).toBe('token-123')
    expect(window.localStorage.getItem(AUTH_TOKEN_KEY)).toBe('token-123')
  })

  it('sets up the first account and stores the session', async () => {
    vi.mocked(authApi.setupAccount).mockResolvedValue(session)
    const auth = useAuthStore()

    await auth.setup('owner', 'password-123')

    expect(auth.status?.initialized).toBe(true)
    expect(auth.initialized).toBe(true)
    expect(window.localStorage.getItem(AUTH_TOKEN_KEY)).toBe('token-123')
  })

  it('restores a session from the existing token', async () => {
    window.localStorage.setItem(AUTH_TOKEN_KEY, 'stored-token')
    vi.mocked(authApi.fetchMe).mockResolvedValue(user)
    setActivePinia(createPinia())
    const auth = useAuthStore()

    await auth.bootstrap()

    expect(auth.isAuthenticated).toBe(true)
    expect(auth.user).toEqual(user)
  })

  it('clears an invalid stored token', async () => {
    window.localStorage.setItem(AUTH_TOKEN_KEY, 'bad-token')
    vi.mocked(authApi.fetchMe).mockRejectedValue(new Error('登录已失效'))
    setActivePinia(createPinia())
    const auth = useAuthStore()

    await auth.bootstrap()

    expect(auth.isAuthenticated).toBe(false)
    expect(auth.token).toBeNull()
    expect(window.localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull()
  })

  it('stores a readable login error', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('用户名或密码不正确'))
    const auth = useAuthStore()

    await expect(auth.login('owner', 'wrong')).rejects.toThrow('用户名或密码不正确')

    expect(auth.error).toBe('用户名或密码不正确')
    expect(auth.loading).toBe(false)
  })

  it('logs out locally even if the API call fails', async () => {
    vi.mocked(authApi.login).mockResolvedValue(session)
    vi.mocked(authApi.logout).mockRejectedValue(new Error('network'))
    const auth = useAuthStore()
    await auth.login('owner', 'password-123')

    await auth.logout()

    expect(auth.isAuthenticated).toBe(false)
    expect(auth.token).toBeNull()
    expect(window.localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull()
  })
})
