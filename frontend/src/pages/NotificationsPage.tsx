import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell, CheckCheck } from 'lucide-react'
import { Button } from '../components/ui/Button'
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../lib/resources'
import type { NotificationItem, Paginated } from '../types'

export function NotificationsPage() {
  const [data, setData] = useState<Paginated<NotificationItem> | null>(null)
  const [loading, setLoading] = useState(true)

  function load() {
    getNotifications().then(setData)
  }

  useEffect(() => {
    getNotifications()
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  async function handleMarkAll() {
    await markAllNotificationsRead()
    load()
  }

  async function handleClick(notification: NotificationItem) {
    if (!notification.is_read) {
      await markNotificationRead(notification.id)
      load()
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-midnight">Notifications</h1>
        {data && data.items.some((n) => !n.is_read) && (
          <Button variant="secondary" onClick={handleMarkAll}>
            <CheckCheck className="h-4 w-4" /> Mark all read
          </Button>
        )}
      </div>

      {loading ? (
        <div className="py-16 text-center text-midnight/50">Loading…</div>
      ) : !data || data.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-midnight/15 bg-white py-16 text-center">
          <Bell className="h-10 w-10 text-mint" />
          <h2 className="mt-4 text-lg font-semibold text-midnight">No notifications</h2>
          <p className="mt-1 text-sm text-midnight/60">You&apos;re all caught up.</p>
        </div>
      ) : (
        <ul className="flex flex-col gap-2">
          {data.items.map((notification) => {
            const body = (
              <div
                className={`rounded-2xl border p-4 transition hover:border-mint ${
                  notification.is_read
                    ? 'border-midnight/10 bg-white'
                    : 'border-mint bg-mint-soft/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-midnight">{notification.title}</p>
                  {!notification.is_read && (
                    <span className="h-2.5 w-2.5 rounded-full bg-brand" />
                  )}
                </div>
                <p className="mt-1 text-sm text-midnight/70">{notification.message}</p>
                <p className="mt-2 text-xs text-midnight/40">
                  {new Date(notification.created_at).toLocaleString()}
                </p>
              </div>
            )
            return notification.report_id ? (
              <li key={notification.id}>
                <Link to={`/items/${notification.report_id}`} onClick={() => handleClick(notification)}>
                  {body}
                </Link>
              </li>
            ) : (
              <li key={notification.id}>{body}</li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
