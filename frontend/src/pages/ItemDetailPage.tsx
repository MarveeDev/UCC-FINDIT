import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Calendar, MapPin } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { getErrorMessage } from '../lib/api'
import { getReport } from '../lib/resources'
import type { ReportDetail } from '../types'

export function ItemDetailPage() {
  const { id } = useParams()
  const [report, setReport] = useState<ReportDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    getReport(Number(id))
      .then((r) => {
        setReport(r)
        setError(null)
      })
      .catch((err) => {
        setError(getErrorMessage(err))
        setReport(null)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return <div className="text-midnight/60">Loading…</div>
  }

  if (error || !report) {
    return (
      <div className="rounded-2xl border border-midnight/10 bg-white p-8 text-center">
        <p className="text-midnight/70">{error ?? 'Report not found'}</p>
        <Link to="/feed" className="mt-4 inline-block font-medium text-brand hover:underline">
          Back to the feed
        </Link>
      </div>
    )
  }

  const isLost = report.report_type === 'LOST'

  return (
    <div className="mx-auto max-w-2xl">
      <Link
        to="/feed"
        className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-brand hover:underline"
      >
        <ArrowLeft className="h-4 w-4" /> Back to the feed
      </Link>

      <div className="overflow-hidden rounded-2xl border border-midnight/10 bg-white">
        {report.image_url && (
          <img src={report.image_url} alt={report.item_name} className="h-64 w-full object-cover" />
        )}
        <div className="p-6">
          <div className="flex items-center gap-2">
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                isLost ? 'bg-amber-100 text-amber-800' : 'bg-mint-soft text-brand'
              }`}
            >
              {isLost ? 'Lost' : 'Found'}
            </span>
            <span className="rounded-full bg-midnight/10 px-2.5 py-0.5 text-xs font-semibold text-midnight">
              {report.category}
            </span>
          </div>

          <h1 className="mt-4 text-2xl font-bold text-midnight">{report.item_name}</h1>
          <p className="mt-1 text-sm text-midnight/50">
            Reported by {report.reporter_name} on{' '}
            {new Date(report.created_at).toLocaleDateString()}
          </p>

          <p className="mt-4 text-midnight/80">{report.description}</p>

          {!isLost && !report.is_reporter && (
            <div className="mt-6 rounded-xl border border-mint bg-mint-soft/50 p-4">
              <p className="text-sm font-semibold text-midnight">Is this yours?</p>
              <p className="mt-1 text-sm text-midnight/60">
                Submit a private claim with proof of ownership.
              </p>
              <Link to={`/claims/new?report_id=${report.id}`}>
                <Button className="mt-3">This Is Mine</Button>
              </Link>
            </div>
          )}

          <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
            {report.brand && (
              <div>
                <dt className="font-medium text-midnight/50">Brand / model</dt>
                <dd className="text-midnight">{report.brand}</dd>
              </div>
            )}
            {report.colour && (
              <div>
                <dt className="font-medium text-midnight/50">Colour</dt>
                <dd className="text-midnight">{report.colour}</dd>
              </div>
            )}
            <div>
              <dt className="font-medium text-midnight/50">Location</dt>
              <dd className="text-midnight">
                {report.location_description ?? 'Unknown'}
              </dd>
              {report.location_name && (
                <dd className="mt-0.5 flex items-center gap-1 text-sm text-midnight/60">
                  <MapPin className="h-3.5 w-3.5" /> {report.location_name}
                </dd>
              )}
            </div>
            <div>
              <dt className="font-medium text-midnight/50">Date {isLost ? 'lost' : 'found'}</dt>
              <dd className="flex items-center gap-1 text-midnight">
                <Calendar className="h-3.5 w-3.5" /> {report.event_date ?? '—'}
              </dd>
            </div>
          </dl>

          {report.custody_info && (
            <div className="mt-6 rounded-lg bg-mint-soft p-4">
              <dt className="text-sm font-medium text-brand">Custody information</dt>
              <dd className="mt-1 text-sm text-midnight">{report.custody_info}</dd>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
