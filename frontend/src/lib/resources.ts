import api from './api'
import type {
  Administrator,
  AnalyticsData,
  ApiEnvelope,
  AuditLog,
  CampusLocation,
  Claim,
  CustodyRecord,
  DashboardData,
  FeedParams,
  Inspection,
  Match,
  NotificationItem,
  Paginated,
  QrRegistration,
  ReportDetail,
  ReportPayload,
  ReportSummary,
  StaffMember,
  SuperAdminOverview,
  TheatreSummary,
  User,
} from '../types'

export async function getLocations(): Promise<CampusLocation[]> {
  const res = await api.get<ApiEnvelope<CampusLocation[]>>('/locations')
  return res.data.data ?? []
}

export async function getReport(id: number): Promise<ReportDetail> {
  const res = await api.get<ApiEnvelope<ReportDetail>>(`/reports/${id}`)
  return res.data.data as ReportDetail
}

export async function createReport(payload: ReportPayload): Promise<ReportSummary> {
  const res = await api.post<ApiEnvelope<ReportSummary>>('/reports', payload)
  return res.data.data as ReportSummary
}

export async function getFeed(params: FeedParams = {}): Promise<Paginated<ReportSummary>> {
  const res = await api.get<ApiEnvelope<Paginated<ReportSummary>>>('/feed', { params })
  return res.data.data as Paginated<ReportSummary>
}

export async function getNotifications(page = 1): Promise<Paginated<NotificationItem>> {
  const res = await api.get<ApiEnvelope<Paginated<NotificationItem>>>('/notifications', {
    params: { page },
  })
  return res.data.data as Paginated<NotificationItem>
}

export async function getUnreadCount(): Promise<number> {
  const res = await api.get<ApiEnvelope<{ count: number }>>('/notifications/unread-count')
  return res.data.data?.count ?? 0
}

export async function markNotificationRead(id: number): Promise<void> {
  await api.patch(`/notifications/${id}/read`)
}

export async function markAllNotificationsRead(): Promise<void> {
  await api.patch('/notifications/read-all')
}

export async function uploadImage(
  file: File,
): Promise<{ url: string; public_id: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post<ApiEnvelope<{ url: string; public_id: string }>>(
    '/uploads',
    form,
  )
  return res.data.data as { url: string; public_id: string }
}

export async function getMatches(): Promise<Match[]> {
  const res = await api.get<ApiEnvelope<Match[]>>('/matches')
  return res.data.data ?? []
}

export async function createClaim(reportId: number, evidence: string): Promise<Claim> {
  const res = await api.post<ApiEnvelope<Claim>>('/claims', {
    report_id: reportId,
    evidence,
  })
  return res.data.data as Claim
}

export async function getMyClaims(): Promise<Claim[]> {
  const res = await api.get<ApiEnvelope<Claim[]>>('/claims/mine')
  return res.data.data ?? []
}

export async function resubmitClaim(id: number, evidence: string): Promise<Claim> {
  const res = await api.post<ApiEnvelope<Claim>>(`/claims/${id}/resubmit`, { evidence })
  return res.data.data as Claim
}

export async function getClaims(status?: string): Promise<Claim[]> {
  const res = await api.get<ApiEnvelope<Claim[]>>('/claims', {
    params: status ? { status } : {},
  })
  return res.data.data ?? []
}

export async function getClaim(id: number): Promise<Claim> {
  const res = await api.get<ApiEnvelope<Claim>>(`/claims/${id}`)
  return res.data.data as Claim
}

export async function reviewClaim(
  id: number,
  decision: string,
  note?: string,
): Promise<Claim> {
  const res = await api.post<ApiEnvelope<Claim>>(`/claims/${id}/review`, {
    decision,
    note,
  })
  return res.data.data as Claim
}

export async function verifyHandover(claimId: number, code: string): Promise<void> {
  await api.post('/handover/verify', { claim_id: claimId, code })
}

export async function registerQr(itemName: string, description?: string): Promise<QrRegistration> {
  const res = await api.post<ApiEnvelope<QrRegistration>>('/qr', {
    item_name: itemName,
    description,
  })
  return res.data.data as QrRegistration
}

export async function getMyQr(): Promise<QrRegistration[]> {
  const res = await api.get<ApiEnvelope<QrRegistration[]>>('/qr/mine')
  return res.data.data ?? []
}

export async function deactivateQr(id: number): Promise<QrRegistration> {
  const res = await api.post<ApiEnvelope<QrRegistration>>(`/qr/${id}/deactivate`)
  return res.data.data as QrRegistration
}

export async function getQrByToken(token: string): Promise<QrRegistration> {
  const res = await api.get<ApiEnvelope<QrRegistration>>(`/qr/${token}`)
  return res.data.data as QrRegistration
}

export async function reportFoundByToken(
  token: string,
  payload: ReportPayload,
): Promise<ReportSummary> {
  const res = await api.post<ApiEnvelope<ReportSummary>>(`/qr/${token}/report-found`, payload)
  return res.data.data as ReportSummary
}

export async function getDashboard(
  params: { location_id?: number; date_from?: string; date_to?: string } = {},
): Promise<DashboardData> {
  const res = await api.get<ApiEnvelope<DashboardData>>('/dashboard', { params })
  return res.data.data as DashboardData
}

export async function getAnalytics(
  params: {
    location_id?: number
    date_from?: string
    date_to?: string
    category?: string
  } = {},
): Promise<AnalyticsData> {
  const res = await api.get<ApiEnvelope<AnalyticsData>>('/analytics', { params })
  return res.data.data as AnalyticsData
}

export async function getStaff(): Promise<StaffMember[]> {
  const res = await api.get<ApiEnvelope<StaffMember[]>>('/staff')
  return res.data.data ?? []
}

export async function createStaff(payload: {
  first_name: string
  last_name: string
  email: string
  password: string
  location_id: number
}): Promise<User> {
  const res = await api.post<ApiEnvelope<User>>('/staff', payload)
  return res.data.data as User
}

export async function removeStaffAssignment(
  userId: number,
  locationId: number,
): Promise<void> {
  await api.delete(`/staff/${userId}/assignments/${locationId}`)
}

export async function getStaffActivity(userId: number): Promise<{
  inspections: number
  found_reports: number
  custody_actions: number
}> {
  const res = await api.get<ApiEnvelope<Record<string, number>>>(`/staff/${userId}/activity`)
  return res.data.data as unknown as {
    inspections: number
    found_reports: number
    custody_actions: number
  }
}

export async function getManagerLocations(): Promise<CampusLocation[]> {
  const res = await api.get<ApiEnvelope<CampusLocation[]>>('/staff/locations/mine')
  return res.data.data ?? []
}

export async function getInspections(params: {
  location_id?: number
  status?: string
} = {}): Promise<Inspection[]> {
  const res = await api.get<ApiEnvelope<Inspection[]>>('/inspections', { params })
  return res.data.data ?? []
}

export async function createInspection(payload: {
  location_id: number
  item_description: string
  category: string
  colour?: string
  brand?: string
  notes?: string
}): Promise<Inspection> {
  const res = await api.post<ApiEnvelope<Inspection>>('/inspections', payload)
  return res.data.data as Inspection
}

export async function convertInspection(
  id: number,
): Promise<{ inspection: Inspection; report: ReportSummary }> {
  const res = await api.post<ApiEnvelope<{ inspection: Inspection; report: ReportSummary }>>(
    `/inspections/${id}/convert`,
  )
  return res.data.data as { inspection: Inspection; report: ReportSummary }
}

export async function getCustody(reportId: number): Promise<CustodyRecord[]> {
  const res = await api.get<ApiEnvelope<CustodyRecord[]>>(`/custody/${reportId}`)
  return res.data.data ?? []
}

export async function recordCustody(payload: {
  found_report_id: number
  event_type: 'RECEIVED' | 'TRANSFERRED'
  staff_id: number
  location_id: number
  note?: string
}): Promise<CustodyRecord> {
  const res = await api.post<ApiEnvelope<CustodyRecord>>('/custody', payload)
  return res.data.data as CustodyRecord
}

export async function getAuditLogs(params: {
  location_id?: number
  action?: string
  page?: number
} = {}): Promise<Paginated<AuditLog>> {
  const res = await api.get<ApiEnvelope<Paginated<AuditLog>>>('/audit-logs', { params })
  return res.data.data as Paginated<AuditLog>
}

export async function getUsers(role?: string): Promise<Paginated<User>> {
  const res = await api.get<ApiEnvelope<Paginated<User>>>('/users', {
    params: role ? { role } : {},
  })
  return res.data.data as Paginated<User>
}

export async function createUser(payload: {
  first_name: string
  last_name: string
  email: string
  password: string
  role: string
}): Promise<User> {
  const res = await api.post<ApiEnvelope<User>>('/users', payload)
  return res.data.data as User
}

export async function getUnassignedReports(
  params: {
    page?: number
    per_page?: number
    search?: string
    report_type?: 'lost' | 'found'
    status?: string
    sort?: 'newest' | 'oldest'
  } = {},
): Promise<Paginated<ReportSummary>> {
  const res = await api.get<ApiEnvelope<Paginated<ReportSummary>>>('/admin/unassigned-reports', {
    params,
  })
  return res.data.data as Paginated<ReportSummary>
}

export async function assignReport(
  reportId: number,
  locationId: number,
): Promise<ReportSummary> {
  const res = await api.post<ApiEnvelope<ReportSummary>>(
    `/admin/reports/${reportId}/assign`,
    { location_id: locationId },
  )
  return res.data.data as ReportSummary
}

export async function getSuperAdminOverview(): Promise<SuperAdminOverview> {
  const res = await api.get<ApiEnvelope<SuperAdminOverview>>('/admin/overview')
  return res.data.data as SuperAdminOverview
}

export async function getAdministrators(): Promise<Administrator[]> {
  const res = await api.get<ApiEnvelope<Administrator[]>>('/admin/administrators')
  return res.data.data ?? []
}

export async function getTheatres(): Promise<TheatreSummary[]> {
  const res = await api.get<ApiEnvelope<TheatreSummary[]>>('/admin/theatres')
  return res.data.data ?? []
}

export async function createTheatre(payload: {
  name: string
  description?: string
}): Promise<CampusLocation> {
  const res = await api.post<ApiEnvelope<CampusLocation>>('/locations', payload)
  return res.data.data as CampusLocation
}

export async function assignManager(
  locationId: number,
  userId: number,
): Promise<void> {
  await api.post(`/locations/${locationId}/managers`, { user_id: userId })
}

export async function removeManager(
  locationId: number,
  userId: number,
): Promise<void> {
  await api.delete(`/locations/${locationId}/managers/${userId}`)
}
