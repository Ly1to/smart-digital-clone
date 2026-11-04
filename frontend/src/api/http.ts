import axios, { type AxiosError } from 'axios'

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

export const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorBody>) => {
    const detail = extractDetail(error.response?.data?.detail)
    if (detail) {
      return Promise.reject(new Error(detail))
    }
    if (!error.response) {
      return Promise.reject(new Error('无法连接后端服务，请确认服务已启动'))
    }
    return Promise.reject(new Error(`请求失败（${error.response.status}）`))
  },
)
