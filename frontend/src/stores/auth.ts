import { defineStore } from 'pinia'

import * as authApi from '@/api/auth'
import { AUTH_TOKEN_KEY } from '@/constants/auth'
import type { AuthStatus, AuthUser } from '@/types/auth'
import { getErrorMessage } from '@/utils/error'

function readToken(): string | null {
  try {
    return window.localStorage.getItem(AUTH_TOKEN_KEY)
  } catch {
    return null
  }
}

function writeToken(token: string | null) {
  try {
    if (token) {
      window.localStorage.setItem(AUTH_TOKEN_KEY, token)
    } else {
      window.localStorage.removeItem(AUTH_TOKEN_KEY)
    }
  } catch {
    // 隐私模式下 localStorage 可能不可用，当前会话仍可继续使用。
  }
}

interface AuthState {
  token: string | null
  user: AuthUser | null
  status: AuthStatus | null
  initialized: boolean
  loading: boolean
  error: string
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: readToken(),
    user: null,
    status: null,
    initialized: false,
    loading: false,
    error: '',
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
  },

  actions: {
    applySession(token: string, user: AuthUser) {
      this.token = token
      this.user = user
      this.status = {
        initialized: true,
        registration_enabled: this.status?.registration_enabled ?? true,
      }
      this.initialized = true
      this.error = ''
      writeToken(token)
    },

    clearSession() {
      this.token = null
      this.user = null
      writeToken(null)
    },

    async bootstrap() {
      if (this.initialized) {
        return
      }
      if (this.token) {
        try {
          this.user = await authApi.fetchMe()
        } catch {
          this.clearSession()
        }
      }
      this.initialized = true
    },

    async fetchStatus() {
      try {
        this.status = await authApi.fetchAuthStatus()
        return this.status
      } catch (error) {
        this.error = getErrorMessage(error)
        return null
      }
    },

    async login(username: string, password: string) {
      this.loading = true
      this.error = ''
      try {
        const response = await authApi.login(username, password)
        this.applySession(response.access_token, response.user)
      } catch (error) {
        this.error = getErrorMessage(error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async setup(username: string, password: string) {
      this.loading = true
      this.error = ''
      try {
        const response = await authApi.setupAccount(username, password)
        this.applySession(response.access_token, response.user)
      } catch (error) {
        this.error = getErrorMessage(error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async register(username: string, password: string) {
      this.loading = true
      this.error = ''
      try {
        const response = await authApi.register(username, password)
        this.applySession(response.access_token, response.user)
      } catch (error) {
        this.error = getErrorMessage(error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async logout() {
      try {
        if (this.token) {
          await authApi.logout()
        }
      } catch {
        // 本地退出优先，不受服务端或网络状态影响。
      } finally {
        this.clearSession()
        this.status = this.status ?? { initialized: true, registration_enabled: true }
        this.error = ''
      }
    },
  },
})
