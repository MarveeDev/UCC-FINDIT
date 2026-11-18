import api from './api'
import type {
  ApiEnvelope,
  CampusLocation,
  FeedParams,
  NotificationItem,
  Paginated,
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
