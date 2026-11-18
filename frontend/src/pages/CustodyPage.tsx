import { useEffect, useState, type FormEvent } from 'react'
import { PackageCheck, ShieldCheck } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { useAuth } from '../context/authContext'
import { getErrorMessage } from '../lib/api'
import { getCustody, getManagerLocations, recordCustody } from '../lib/resources'
import type { CampusLocation, CustodyRecord } from '../types'

export function CustodyPage() {
  const { user } = useAuth()
  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [reportId, setReportId] = useState('')
  const [eventType, setEventType] = useState<'RECEIVED' | 'TRANSFERRED'>('RECEIVED')
  const [locationId, setLocationId] = useState('')
  const [note, setNote] = useState('')
  const [history, setHistory] = useState<CustodyRecord[]>([])
  const [historyId, setHistoryId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    getManagerLocations().then(setLocations).catch(() => setLocations([]))
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await recordCustody({
        found_report_id: Number(reportId),
        event_type: eventType,
        staff_id: user?.id ?? 0,
        location_id: Number(locationId),
        note: note || undefined,
      })
      setNote('')
      setReportId('')
      setHistoryId(String(reportId))
      await loadHistory(Number(reportId))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function loadHistory(id: number) {
    setError(null)
    try {
      setHistory(await getCustody(id))
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold text-midnight">Custody Management</h1>
      <p className="text-sm text-midnight/60">Track where found items are held and transferred.</p>

      <form
        onSubmit={handleSubmit}
        className="mt-6 flex flex-col gap-3 rounded-2xl border border-midnight/10 bg-white p-5"
      >
        <h2 className="flex items-center gap-2 font-semibold text-midnight">
          <PackageCheck className="h-4 w-4" /> Record custody
        </h2>
        {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <Input
          label="Found report ID"
          type="number"
          value={reportId}
          onChange={(e) => setReportId(e.target.value)}
          required
        />
        <Select
          label="Event type"
          value={eventType}
          onChange={(e) => setEventType(e.target.value as 'RECEIVED' | 'TRANSFERRED')}
        >
          <option value="RECEIVED">Received</option>
          <option value="TRANSFERRED">Transferred</option>
        </Select>
        <Select label="Storage location" value={locationId} onChange={(e) => setLocationId(e.target.value)} required>
          <option value="">Select a location</option>
          {locations.map((l) => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </Select>
        <Input label="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Recording…' : 'Record custody'}
        </Button>
      </form>

      <div className="mt-8">
        <h2 className="flex items-center gap-2 font-semibold text-midnight">
          <ShieldCheck className="h-4 w-4" /> Custody history
        </h2>
        <div className="mt-3 flex gap-2">
          <Input
            placeholder="Found report ID"
            type="number"
            value={historyId}
            onChange={(e) => setHistoryId(e.target.value)}
          />
          <Button variant="secondary" onClick={() => historyId && loadHistory(Number(historyId))}>
            View
          </Button>
        </div>
        {history.length === 0 ? (
          <p className="mt-3 text-sm text-midnight/50">No custody records.</p>
        ) : (
          <ul className="mt-3 flex flex-col gap-2">
            {history.map((r) => (
              <li key={r.id} className="rounded-xl border border-midnight/10 bg-white p-4">
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-mint-soft px-2.5 py-0.5 text-xs font-semibold text-brand">
                    {r.event_type}
                  </span>
                  <span className="text-xs text-midnight/50">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="mt-1 text-sm text-midnight">
                  {r.staff_name ? `Held by ${r.staff_name}` : ''}
                  {r.location_name ? ` at ${r.location_name}` : ''}
                </p>
                {r.note && <p className="mt-1 text-xs text-midnight/50">{r.note}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
