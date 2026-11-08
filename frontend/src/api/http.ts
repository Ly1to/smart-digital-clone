import axios, { type AxiosError } from 'axios'

import { AUTH_TOKEN_KEY } from '@/constants/auth'

interface ErrorBody {
  detail?: unknown
}

function extractDetail(detail: unknown): string | null {
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'object' && item !== null && 'msg' in item) {
          return String((item as { msg: unknown }).msg)
        }
        return null
      })
      .filter((item): item is string => Boolean(item))
    return messages.length ? messages.join('；') : null
  }
  return null
}

function readToken(): string | null {
  try {
    return window.localStorage.getItem(AUTH_TOKEN_KEY)
  } catch {
    return null
  }
}

export const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

http.interceptors.request.use((config) => {
  const token = readToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorBody>) => {
    if (error.response?.status === 401) {
      const url = error.config?.url ?? ''
      if (!url.startsWith('/auth/')) {
        try {
          window.localStorage.removeItem(AUTH_TOKEN_KEY)
        } catch {
          // 忽略 localStorage 不可用
        }
        window.dispatchEvent(new CustomEvent('auth:unauthorized'))
      }
    }

    const detail = extractDetail(error.response?.data?.detail)
    if (detail) {
      return Promise.reject(new Error(detail))
    }
    if (!error.response) {
      return Promise.reject(new Error('无法连接后端服务，请确认服务已启动'))
    }
    if (error.response.status === 401) {
      return Promise.reject(new Error('登录已失效，请重新登录'))
    }
    return Promise.reject(new Error(`请求失败（${error.response.status}）`))
  },
)
