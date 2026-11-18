import api from './api'
import type {
  ApiEnvelope,
  CampusLocation,
  Claim,
  FeedParams,
  Match,
  NotificationItem,
  Paginated,
  QrRegistration,
  ReportDetail,
  ReportPayload,
  ReportSummary,
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
): Promise<{ filename: string; url: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post<ApiEnvelope<{ filename: string; url: string }>>(
    '/uploads',
    form,
  )
  return res.data.data as { filename: string; url: string }
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
