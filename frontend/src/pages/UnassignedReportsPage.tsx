import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Inbox, MapPin, PackageSearch, Search } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'
import { getErrorMessage } from '../lib/api'
import {
  assignReport,
  getAuditLogs,
  getLocations,
  getUnassignedReports,
} from '../lib/resources'
import type { AuditLog, CampusLocation, Paginated, ReportSummary } from '../types'

export function UnassignedReportsPage() {
  const [result, setResult] = useState<Paginated<ReportSummary> | null>(null)
  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [recentAssignments, setRecentAssignments] = useState<AuditLog[]>([])
  const [page, setPage] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [reportType, setReportType] = useState('')
  const [sort, setSort] = useState<'newest' | 'oldest'>('newest')
  const [assigningId, setAssigningId] = useState<number | null>(null)
  const [assignLocationId, setAssignLocationId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  function refresh() {
    getUnassignedReports({
      page,
      search: search || undefined,
      report_type: (reportType || undefined) as 'lost' | 'found' | undefined,
      sort,
    })
      .then(setResult)
      .catch(() => setResult(null))
  }

  useEffect(() => {
    getUnassignedReports({
      page,
      search: search || undefined,
      report_type: (reportType || undefined) as 'lost' | 'found' | undefined,
      sort,
    })
      .then(setResult)
      .catch(() => setResult(null))
      .finally(() => setLoading(false))
  }, [page, search, reportType, sort])

  useEffect(() => {
    getLocations()
      .then(setLocations)
      .catch(() => setLocations([]))
    getAuditLogs({ action: 'REPORT_ASSIGNED' })
      .then((d) => setRecentAssignments(d.items))
      .catch(() => setRecentAssignments([]))
  }, [])

  function handleSearch(e: FormEvent) {
    e.preventDefault()
    setPage(1)
    setSearch(searchInput)
  }

  async function handleAssign(reportId: number) {
    if (!assignLocationId) return
    setError(null)
    setSuccess(null)
    try {
      const assigned = await assignReport(reportId, Number(assignLocationId))
      setSuccess(`"${assigned.item_name}" assigned to ${assigned.location_name}.`)
      setAssigningId(null)
      setAssignLocationId('')
      getAuditLogs({ action: 'REPORT_ASSIGNED' })
        .then((d) => setRecentAssignments(d.items))
        .catch(() => undefined)
      refresh()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const total = result?.total ?? 0

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold text-midnight">Unassigned Reports</h1>
      <p className="text-sm text-midnight/60">
        {total} report{total === 1 ? '' : 's'} awaiting a campus location.
      </p>

      <form
        onSubmit={handleSearch}
        className="mt-4 grid grid-cols-1 gap-3 rounded-2xl border border-midnight/10 bg-white p-4 sm:grid-cols-3"
      >
        <div className="relative sm:col-span-3">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-midnight/40" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by item name or location…"
            className="w-full rounded-lg border border-midnight/15 bg-white py-2.5 pl-9 pr-3 text-sm text-midnight focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>
        <Select
          value={reportType}
          onChange={(e) => {
            setReportType(e.target.value)
            setPage(1)
          }}
        >
          <option value="">All types</option>
          <option value="lost">Lost</option>
          <option value="found">Found</option>
        </Select>
        <Select
          value={sort}
          onChange={(e) => {
            setSort(e.target.value as 'newest' | 'oldest')
            setPage(1)
          }}
        >
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
        </Select>
        <Button type="submit" variant="secondary">
          Search
        </Button>
      </form>

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
      )}
      {success && (
        <div className="mt-4 rounded-lg bg-mint-soft px-3 py-2 text-sm text-brand">{success}</div>
      )}

      {loading ? (
        <div className="py-16 text-center text-midnight/50">Loading…</div>
      ) : !result || result.items.length === 0 ? (
        <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-midnight/15 bg-white py-16 text-center">
          <Inbox className="h-10 w-10 text-mint" />
          <h2 className="mt-4 text-lg font-semibold text-midnight">No unassigned reports</h2>
          <p className="mt-1 text-sm text-midnight/60">
            Reports submitted without a campus location will appear here.
          </p>
        </div>
      ) : (
        <ul className="mt-6 flex flex-col gap-3">
          {result.items.map((report) => (
            <li key={report.id} className="rounded-2xl border border-midnight/10 bg-white p-5">
              <div className="flex items-start justify-between">
                <div>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      report.report_type === 'LOST'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-mint-soft text-brand'
                    }`}
                  >
                    {report.report_type === 'LOST' ? 'Lost' : 'Found'}
                  </span>
                  <Link
                    to={`/items/${report.id}`}
                    className="ml-2 font-semibold text-midnight hover:text-brand"
                  >
                    {report.item_name}
                  </Link>
                </div>
                <span className="text-xs text-midnight/50">{report.category}</span>
              </div>

              <p className="mt-2 flex items-center gap-1 text-sm text-midnight/70">
                <PackageSearch className="h-4 w-4 text-midnight/40" />
                {report.location_description ?? 'No description'}
              </p>

              {report.latitude != null && report.longitude != null && (
                <p className="mt-1 flex items-center gap-1 text-xs text-midnight/50">
                  <MapPin className="h-3.5 w-3.5" />
                  {report.latitude.toFixed(5)}, {report.longitude.toFixed(5)}
                </p>
              )}

              {report.image_url && (
                <img
                  src={report.image_url}
                  alt={report.item_name}
                  className="mt-3 h-32 w-full rounded-lg object-cover"
                />
              )}

              {assigningId === report.id ? (
                <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-midnight/10 pt-3">
                  <Select
                    className="min-w-[200px] flex-1"
                    value={assignLocationId}
                    onChange={(e) => setAssignLocationId(e.target.value)}
                  >
                    <option value="">Select a campus location</option>
                    {locations.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </Select>
                  <Button onClick={() => handleAssign(report.id)} disabled={!assignLocationId}>
                    Confirm assign
                  </Button>
                  <Button variant="ghost" onClick={() => setAssigningId(null)}>
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button
                  variant="secondary"
                  className="mt-3"
                  onClick={() => {
                    setAssigningId(report.id)
                    setAssignLocationId('')
                  }}
                >
                  Assign location
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}

      {result && result.pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-4">
          <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="text-sm text-midnight/60">
            Page {result.page} of {result.pages}
          </span>
          <Button
            variant="secondary"
            disabled={page >= result.pages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}

      {recentAssignments.length > 0 && (
        <section className="mt-8 rounded-2xl border border-midnight/10 bg-white p-5">
          <h2 className="text-lg font-semibold text-midnight">Recent assignments</h2>
          <ul className="mt-3 flex flex-col gap-2">
            {recentAssignments.slice(0, 10).map((log) => (
              <li key={log.id} className="flex items-center justify-between text-sm">
                <span className="text-midnight/70">
                  Report #{log.entity_id} assigned
                  {log.actor ? ` by ${log.actor.first_name} ${log.actor.last_name}` : ''}
                </span>
                <span className="text-xs text-midnight/40">
                  {new Date(log.created_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
