import { http } from './http'
import type { AuthStatus, AuthUser, TokenResponse } from '@/types/auth'

export async function fetchAuthStatus(): Promise<AuthStatus> {
  const { data } = await http.get<AuthStatus>('/auth/status')
  return data
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  const { data } = await http.post<TokenResponse>('/auth/login', { username, password })
  return data
}

export async function setupAccount(username: string, password: string): Promise<TokenResponse> {
  const { data } = await http.post<TokenResponse>('/auth/setup', { username, password })
  return data
}

export async function register(username: string, password: string): Promise<TokenResponse> {
  const { data } = await http.post<TokenResponse>('/auth/register', { username, password })
  return data
}

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await http.get<AuthUser>('/auth/me')
  return data
}

export async function logout(): Promise<void> {
  await http.post('/auth/logout')
}
