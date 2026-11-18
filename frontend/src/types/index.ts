export type Role =
  | 'STUDENT'
  | 'LOCATION_STAFF'
  | 'LOCATION_MANAGER'
  | 'SUPER_ADMIN'

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
  role: Role
  email_verified: boolean
  created_at: string | null
}

export interface AuthResult {
  user: User
  access_token: string
}

export interface ApiEnvelope<T> {
  success: boolean
  data?: T
  message?: string
  errors?: Record<string, string>
  dev_otp?: string
  retry_after?: number
}
