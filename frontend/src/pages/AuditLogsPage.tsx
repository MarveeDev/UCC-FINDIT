import { useEffect, useState } from 'react'
import { ScrollText } from 'lucide-react'
import { getAuditLogs } from '../lib/resources'
import type { AuditLog, Paginated } from '../types'

export function AuditLogsPage() {
  const [data, setData] = useState<Paginated<AuditLog> | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAuditLogs()
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold text-midnight">Audit Logs</h1>
      <p className="text-sm text-midnight/60">A secure trail of operational actions.</p>

      {loading ? (
        <div className="py-16 text-center text-midnight/50">Loading…</div>
      ) : !data || data.items.length === 0 ? (
        <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-midnight/15 bg-white py-16 text-center">
          <ScrollText className="h-10 w-10 text-mint" />
          <h2 className="mt-4 text-lg font-semibold text-midnight">No audit entries</h2>
        </div>
      ) : (
        <ul className="mt-6 flex flex-col gap-2">
          {data.items.map((log) => (
            <li key={log.id} className="rounded-xl border border-midnight/10 bg-white p-4">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-mint-soft px-2.5 py-0.5 text-xs font-semibold text-brand">
                  {log.action.replaceAll('_', ' ')}
                </span>
                <span className="text-xs text-midnight/50">
                  {new Date(log.created_at).toLocaleString()}
                </span>
              </div>
              <p className="mt-1 text-sm text-midnight/70">
                {log.actor ? `${log.actor.first_name} ${log.actor.last_name}` : 'System'}{' '}
                · {log.entity_type}
                {log.entity_id ? ` #${log.entity_id}` : ''}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
