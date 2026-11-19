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
  latitude: number | null
  longitude: number | null
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
  location_id: number | null
  location_name: string | null
  location_description: string | null
  latitude: number | null
  longitude: number | null
  location_latitude: number | null
  location_longitude: number | null
  event_date: string | null
  event_time: string | null
  status: ItemStatus
  image_url: string | null
  reporter_name: string
  created_at: string
}

export interface ReportDetail extends ReportSummary {
  is_reporter?: boolean
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
  location_id?: number
  location_description: string
  latitude?: number
  longitude?: number
  event_date: string
  event_time?: string
  image_url?: string
  image_public_id?: string
  custody_info?: string
}

export type ClaimStatus =
  | 'PENDING'
  | 'MORE_INFORMATION_REQUIRED'
  | 'APPROVED'
  | 'REJECTED'

export interface Match {
  id: number
  score: number
  reasons: string[]
  lost_report: ReportSummary
  found_report: ReportSummary
  created_at: string
}

export interface Claim {
  id: number
  report_id: number
  status: ClaimStatus
  claimant_name: string
  review_note: string | null
  created_at: string
  reviewed_at: string | null
  report: ReportSummary
  evidence?: string
  collection_code?: string
}

export interface QrRegistration {
  id: number
  item_name: string
  description: string | null
  is_active: boolean
  created_at: string | null
  token?: string
  qr_url?: string
}

export interface DashboardMetrics {
  lost: number
  found: number
  recovered: number
  awaiting_collection: number
  pending_claims: number
  active_staff: number
  unassigned: number
}

export interface PendingClaimSummary {
  id: number
  report_id: number
  item_name: string
  claimant_name: string
  created_at: string
}

export interface DashboardData {
  metrics: DashboardMetrics
  recent_reports: ReportSummary[]
  pending_claim_summaries: PendingClaimSummary[]
}

export type InspectionStatus = 'OPEN' | 'CONVERTED'

export interface Inspection {
  id: number
  reference: string
  location_id: number
  location_name: string | null
  staff_id: number
  staff_name: string
  inspected_at: string
  item_description: string
  category: string
  colour: string | null
  brand: string | null
  image_url: string | null
  notes: string | null
  found_report_id: number | null
  status: InspectionStatus
  created_at: string
}

export type CustodyEventType = 'RECEIVED' | 'TRANSFERRED' | 'RELEASED'

export interface CustodyRecord {
  id: number
  found_report_id: number
  event_type: CustodyEventType
  staff_id: number | null
  staff_name: string | null
  location_id: number | null
  location_name: string | null
  authorized_by: number | null
  authorizer_name: string | null
  note: string | null
  created_at: string
}

export interface AuditLog {
  id: number
  actor: User | null
  action: string
  entity_type: string
  entity_id: number | null
  location_id: number | null
  metadata: Record<string, unknown> | null
  created_at: string
}

export interface StaffMember {
  user: User
  assignments: {
    location_id: number
    location_name: string | null
    created_at: string | null
  }[]
}

export interface AnalyticsData {
  lost: number
  found: number
  recovered: number
  recovery_rate: number
  pending_claims: number
  avg_recovery_days: number | null
  by_location: { location: string; lost: number; found: number }[]
  by_category: { category: string; count: number }[]
  staff_activity: {
    staff_id: number
    staff_name: string
    inspections: number
    custody_actions: number
  }[]
}

export interface ApiEnvelope<T> {
  success: boolean
  data?: T
  message?: string
  errors?: Record<string, string>
  retry_after?: number
}
