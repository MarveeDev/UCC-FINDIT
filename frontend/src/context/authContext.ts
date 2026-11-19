import { createContext, useContext } from 'react'
import type { User } from '../types'

export interface RegisterPayload {
  first_name: string
  last_name: string
  email: string
  password: string
}

export interface AuthContextValue {
  user: User | null
  loading: boolean
  register: (payload: RegisterPayload) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
