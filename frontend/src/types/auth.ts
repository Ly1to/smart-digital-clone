export interface AuthUser {
  id: number
  username: string
  created_at: string
}

export interface AuthStatus {
  initialized: boolean
  registration_enabled: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: AuthUser
}
