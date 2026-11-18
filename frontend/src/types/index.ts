export type Role =
  | 'STUDENT'
  | 'LOCATION_STAFF'
  | 'LOCATION_MANAGER'
  | 'SUPER_ADMIN'

export type ReportType = 'LOST' | 'FOUND'

export type ItemStatus =
  | 'OPEN'
  | 'POSSIBLE_MATCH'
  | 'CLAIM_PENDING'
  | 'VERIFICATION_REQUIRED'
  | 'APPROVED_FOR_COLLECTION'
  | 'RECOVERED'
  | 'REJECTED'
  | 'CLOSED'

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

export interface CampusLocation {
  id: number
  name: string
  description: string | null
  is_active: boolean
  created_at: string | null
}

export interface ReportSummary {
  id: number
  report_type: ReportType
  item_name: string
  category: string
  description: string
  brand: string | null
  colour: string | null
  location_id: number
  location_name: string | null
  event_date: string | null
  event_time: string | null
  status: ItemStatus
  image_url: string | null
  reporter_name: string
  created_at: string
}

export interface ReportDetail extends ReportSummary {
  identifying_characteristics?: string | null
  custody_info?: string | null
}

export interface Paginated<T> {
  items: T[]
  page: number
  per_page: number
  total: number
  pages: number
}

export interface NotificationItem {
  id: number
  type: string
  title: string
  message: string
  report_id: number | null
  is_read: boolean
  created_at: string
}

export interface FeedParams {
  type?: 'all' | 'lost' | 'found' | 'recovered'
  search?: string
  location_id?: number
  category?: string
  date_from?: string
  date_to?: string
  sort?: 'newest' | 'oldest'
  page?: number
  per_page?: number
}

export interface ReportPayload {
  report_type: ReportType
  item_name: string
  category: string
  description: string
  brand?: string
  colour?: string
  identifying_characteristics?: string
  location_id: number
  event_date: string
  event_time?: string
  image_path?: string
  custody_info?: string
}

export interface ApiEnvelope<T> {
  success: boolean
  data?: T
  message?: string
  errors?: Record<string, string>
  dev_otp?: string
  retry_after?: number
}
