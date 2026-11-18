import { Calendar, MapPin } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { ReportSummary } from '../types'

export function ReportCard({ report }: { report: ReportSummary }) {
  const isLost = report.report_type === 'LOST'
  return (
    <Link
      to={`/items/${report.id}`}
      className="block rounded-2xl border border-midnight/10 bg-white p-5 transition hover:border-mint hover:shadow-sm"
    >
      <div className="flex items-center justify-between">
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
            isLost ? 'bg-amber-100 text-amber-800' : 'bg-mint-soft text-brand'
          }`}
        >
          {isLost ? 'Lost' : 'Found'}
        </span>
        {report.status === 'RECOVERED' && (
          <span className="rounded-full bg-midnight/10 px-2.5 py-0.5 text-xs font-semibold text-midnight">
            Recovered
          </span>
        )}
        <span className="text-xs text-midnight/50">{report.reporter_name}</span>
      </div>
      <h3 className="mt-3 text-lg font-semibold text-midnight">{report.item_name}</h3>
      <p className="mt-1 line-clamp-2 text-sm text-midnight/70">{report.description}</p>
      {report.image_url && (
        <img
          src={report.image_url}
          alt={report.item_name}
          className="mt-3 h-40 w-full rounded-lg object-cover"
        />
      )}
      <div className="mt-3 flex items-center gap-4 text-xs text-midnight/50">
        <span className="flex items-center gap-1">
          <MapPin className="h-3.5 w-3.5" />{' '}
          {report.location_description ?? report.location_name ?? 'Unknown location'}
        </span>
        {report.event_date && (
          <span className="flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" /> {report.event_date}
          </span>
        )}
        <span className="ml-auto font-medium text-brand">View details</span>
      </div>
    </Link>
  )
}
