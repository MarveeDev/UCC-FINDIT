import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PackageSearch } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Textarea } from '../components/ui/Textarea'
import { ITEM_CATEGORIES } from '../constants'
import { getErrorMessage } from '../lib/api'
import { getLocations, getQrByToken, reportFoundByToken } from '../lib/resources'
import type { CampusLocation, QrRegistration } from '../types'

export function QrRecoveryPage() {
  const { token } = useParams()
  const navigate = useNavigate()
  const [qr, setQr] = useState<QrRegistration | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [category, setCategory] = useState('')
  const [description, setDescription] = useState('')
  const [locationId, setLocationId] = useState('')
  const [eventDate, setEventDate] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!token) return
    getQrByToken(token)
      .then(setQr)
      .catch((err) => setError(getErrorMessage(err)))
    getLocations()
      .then(setLocations)
      .catch(() => setLocations([]))
  }, [token])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!token) return
    setError(null)
    setSubmitting(true)
    try {
      await reportFoundByToken(token, {
        report_type: 'FOUND',
        item_name: qr?.item_name ?? '',
        category,
        description,
        location_id: Number(locationId),
        location_description: description,
        event_date: eventDate,
      })
      navigate('/feed')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (error && !qr) {
    return (
      <div className="mx-auto max-w-md rounded-2xl border border-midnight/10 bg-white p-8 text-center">
        <p className="text-midnight/70">{error}</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-2xl border border-midnight/10 bg-white p-8 text-center">
        <PackageSearch className="mx-auto h-10 w-10 text-mint" />
        <h1 className="mt-4 text-xl font-bold text-midnight">
          {qr ? `Found a ${qr.item_name}?` : 'Loading…'}
        </h1>
        <p className="mt-2 text-sm text-midnight/60">
          This item is registered with UCC FINDIT. Report it as found and the owner
          will be notified privately — their contact details are never shared.
        </p>
        {qr && !showForm && (
          <Button className="mt-6" fullWidth onClick={() => setShowForm(true)}>
            I found this item
          </Button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3 rounded-2xl border border-midnight/10 bg-white p-5">
          {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
          <Select
            id="category"
            label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            required
          >
            <option value="">Select a category</option>
            {ITEM_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </Select>
          <Textarea
            id="description"
            label="Where did you find it?"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
          <Select
            id="location"
            label="Campus location"
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
            required
          >
            <option value="">Select a location</option>
            {locations.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </Select>
          <Input
            id="event_date"
            label="Date found"
            type="date"
            value={eventDate}
            onChange={(e) => setEventDate(e.target.value)}
            required
          />
          <div className="flex gap-2">
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit found report'}
            </Button>
            <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>
              Cancel
            </Button>
          </div>
        </form>
      )}
    </div>
  )
}
