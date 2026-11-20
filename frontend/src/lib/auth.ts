import type { User } from '../types'

const TOKEN_KEY = 'uccfindit_token'
const USER_KEY = 'uccfindit_user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setSession(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getStoredUser(): User | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export function getGoogleSignInUrl(): string {
  const base = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1').replace(/\/+$/, '')
  return `${base}/auth/google`
}
