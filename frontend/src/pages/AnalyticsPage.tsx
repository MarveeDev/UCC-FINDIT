import { useEffect, useState } from 'react'
import { BarChart3 } from 'lucide-react'
import { StatCard } from '../components/StatCard'
import { getAnalytics } from '../lib/resources'
import type { AnalyticsData } from '../types'

function Bar({ value, max }: { value: number; max: number }) {
  const width = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-mint-soft">
      <div className="h-full rounded-full bg-brand" style={{ width: `${width}%` }} />
    </div>
  )
}

export function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAnalytics()
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="py-16 text-center text-midnight/50">Loading…</div>
  }

  if (!data) {
    return <div className="py-16 text-center text-midnight/50">Could not load analytics.</div>
  }

  const maxCategory = Math.max(0, ...data.by_category.map((c) => c.count))

  return (
    <div>
      <h1 className="text-2xl font-bold text-midnight">Analytics</h1>
      <p className="text-sm text-midnight/60">Real metrics from database records.</p>

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Lost" value={data.lost} icon={BarChart3} />
        <StatCard label="Found" value={data.found} icon={BarChart3} />
        <StatCard label="Recovered" value={data.recovered} icon={BarChart3} />
        <StatCard label="Recovery rate" value={`${data.recovery_rate}%`} icon={BarChart3} />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-midnight/10 bg-white p-5">
          <h2 className="text-lg font-semibold text-midnight">Items by category</h2>
          {data.by_category.length === 0 ? (
            <p className="mt-3 text-sm text-midnight/50">No data.</p>
          ) : (
            <ul className="mt-3 flex flex-col gap-3">
              {data.by_category.map((c) => (
                <li key={c.category}>
                  <div className="flex justify-between text-sm">
                    <span className="text-midnight">{c.category}</span>
                    <span className="text-midnight/50">{c.count}</span>
                  </div>
                  <Bar value={c.count} max={maxCategory} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-midnight/10 bg-white p-5">
          <h2 className="text-lg font-semibold text-midnight">Location performance</h2>
          {data.by_location.length === 0 ? (
            <p className="mt-3 text-sm text-midnight/50">No data.</p>
          ) : (
            <ul className="mt-3 flex flex-col gap-3">
              {data.by_location.map((l) => (
                <li key={l.location} className="rounded-lg bg-mint-soft/50 p-3">
                  <p className="text-sm font-medium text-midnight">{l.location}</p>
                  <p className="text-xs text-midnight/50">
                    {l.lost} lost · {l.found} found
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="mt-6 rounded-2xl border border-midnight/10 bg-white p-5">
        <h2 className="text-lg font-semibold text-midnight">Staff activity</h2>
        {data.staff_activity.length === 0 ? (
          <p className="mt-3 text-sm text-midnight/50">No staff activity.</p>
        ) : (
          <ul className="mt-3 flex flex-col gap-2">
            {data.staff_activity.map((s) => (
              <li key={s.staff_id} className="flex justify-between rounded-lg bg-mint-soft/50 p-3 text-sm">
                <span className="text-midnight">{s.staff_name}</span>
                <span className="text-midnight/50">
                  {s.inspections} inspections · {s.custody_actions} custody actions
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
