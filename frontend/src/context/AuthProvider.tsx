import { useCallback, useEffect, useState, type ReactNode } from 'react'
import api from '../lib/api'
import { clearSession, getStoredUser, getToken, setSession } from '../lib/auth'
import type { ApiEnvelope, AuthResult, User } from '../types'
import { AuthContext, type RegisterPayload } from './authContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getStoredUser())
  const [loading, setLoading] = useState(() => Boolean(getToken()))

  useEffect(() => {
    if (!getToken()) return
    let cancelled = false
    api
      .get<ApiEnvelope<User>>('/users/me')
      .then((res) => {
        if (!cancelled) setUser(res.data.data ?? null)
      })
      .catch(() => {
        if (!cancelled) {
          clearSession()
          setUser(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function register(payload: RegisterPayload): Promise<void> {
    await api.post<ApiEnvelope<User>>('/auth/register', payload)
  }

  async function login(email: string, password: string): Promise<void> {
    const res = await api.post<ApiEnvelope<AuthResult>>('/auth/login', {
      email,
      password,
    })
    const result = res.data.data
    if (result) {
      setSession(result.access_token, result.user)
      setUser(result.user)
    }
  }

  function logout(): void {
    clearSession()
    setUser(null)
  }

  const completeGoogleLogin = useCallback(async (code: string): Promise<void> => {
    const res = await api.post<ApiEnvelope<AuthResult>>('/auth/google/exchange', {
      code,
    })
    const result = res.data.data
    if (result) {
      setSession(result.access_token, result.user)
      setUser(result.user)
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{ user, loading, register, login, completeGoogleLogin, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}
