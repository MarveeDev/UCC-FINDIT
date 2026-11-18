import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Boxes,
  CheckCircle,
  ClipboardList,
  Inbox,
  PackageCheck,
  PackageSearch,
  Users,
} from 'lucide-react'
import { StatCard } from '../components/StatCard'
import { useAuth } from '../context/authContext'
import { getDashboard } from '../lib/resources'
import type { DashboardData } from '../types'

export function ManagerDashboardPage() {
  const { user } = useAuth()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard()
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="py-16 text-center text-midnight/50">Loading…</div>
  }

  if (!data) {
    return <div className="py-16 text-center text-midnight/50">Could not load dashboard.</div>
  }

  const m = data.metrics

  return (
    <div>
      <h1 className="text-2xl font-bold text-midnight">Dashboard</h1>
      <p className="text-sm text-midnight/60">Overview of lost and found operations.</p>

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label="Lost reports" value={m.lost} icon={PackageSearch} />
        <StatCard label="Found reports" value={m.found} icon={Boxes} />
        <StatCard label="Recovered items" value={m.recovered} icon={CheckCircle} />
        <StatCard label="Awaiting collection" value={m.awaiting_collection} icon={PackageCheck} />
        <StatCard label="Pending claims" value={m.pending_claims} icon={ClipboardList} />
        <StatCard label="Active staff" value={m.active_staff} icon={Users} />
        {user?.role === 'SUPER_ADMIN' && (
          <Link to="/admin/unassigned" className="transition hover:opacity-90">
            <StatCard label="Unassigned reports" value={m.unassigned} icon={Inbox} />
          </Link>
        )}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-midnight/10 bg-white p-5">
          <h2 className="text-lg font-semibold text-midnight">Recent reports</h2>
          {data.recent_reports.length === 0 ? (
            <p className="mt-3 text-sm text-midnight/50">No recent reports.</p>
          ) : (
            <ul className="mt-3 flex flex-col gap-2">
              {data.recent_reports.map((r) => (
                <li key={r.id}>
                  <Link to={`/items/${r.id}`} className="block rounded-lg bg-mint-soft/50 p-3 hover:bg-mint-soft">
                    <span className="text-sm font-medium text-midnight">{r.item_name}</span>
                    <span className="ml-2 text-xs text-midnight/50">
                      {r.report_type} · {r.location_name}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-midnight/10 bg-white p-5">
          <h2 className="text-lg font-semibold text-midnight">Pending claims</h2>
          {data.pending_claim_summaries.length === 0 ? (
            <p className="mt-3 text-sm text-midnight/50">No pending claims.</p>
          ) : (
            <ul className="mt-3 flex flex-col gap-2">
              {data.pending_claim_summaries.map((c) => (
                <li key={c.id} className="rounded-lg bg-mint-soft/50 p-3">
                  <p className="text-sm font-medium text-midnight">{c.item_name}</p>
                  <p className="text-xs text-midnight/50">Claimed by {c.claimant_name}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
