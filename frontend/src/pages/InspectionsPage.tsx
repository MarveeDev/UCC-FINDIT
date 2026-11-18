import { useEffect, useState, type FormEvent } from 'react'
import { ClipboardList, PackagePlus } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'
import { Textarea } from '../components/ui/Textarea'
import { ITEM_CATEGORIES } from '../constants'
import { getErrorMessage } from '../lib/api'
import {
  convertInspection,
  createInspection,
  getInspections,
  getManagerLocations,
} from '../lib/resources'
import type { CampusLocation, Inspection } from '../types'

export function InspectionsPage() {
  const [inspections, setInspections] = useState<Inspection[]>([])
  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [locationId, setLocationId] = useState('')
  const [itemDescription, setItemDescription] = useState('')
  const [category, setCategory] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function load() {
    getInspections().then(setInspections).catch(() => setInspections([]))
    getManagerLocations().then(setLocations).catch(() => setLocations([]))
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await createInspection({
        location_id: Number(locationId),
        item_description: itemDescription,
        category,
        notes: notes || undefined,
      })
      setItemDescription('')
      setCategory('')
      setNotes('')
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleConvert(id: number) {
    setError(null)
    try {
      await convertInspection(id)
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold text-midnight">Inspections</h1>
      <p className="text-sm text-midnight/60">Record items discovered during campus inspections.</p>

      <form
        onSubmit={handleSubmit}
        className="mt-6 flex flex-col gap-3 rounded-2xl border border-midnight/10 bg-white p-5"
      >
        <h2 className="flex items-center gap-2 font-semibold text-midnight">
          <ClipboardList className="h-4 w-4" /> New inspection record
        </h2>
        {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <Select label="Location" value={locationId} onChange={(e) => setLocationId(e.target.value)} required>
          <option value="">Select a location</option>
          {locations.map((l) => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </Select>
        <Textarea
          label="Item description"
          rows={2}
          value={itemDescription}
          onChange={(e) => setItemDescription(e.target.value)}
          required
        />
        <Select label="Category" value={category} onChange={(e) => setCategory(e.target.value)} required>
          <option value="">Select a category</option>
          {ITEM_CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </Select>
        <Textarea label="Notes (optional)" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Recording…' : 'Record inspection'}
        </Button>
      </form>

      <div className="mt-8">
        <h2 className="font-semibold text-midnight">Inspection records</h2>
        {inspections.length === 0 ? (
          <p className="mt-3 text-sm text-midnight/50">No inspection records yet.</p>
        ) : (
          <ul className="mt-3 flex flex-col gap-3">
            {inspections.map((i) => (
              <li key={i.id} className="rounded-2xl border border-midnight/10 bg-white p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-mono text-xs text-midnight/50">{i.reference}</p>
                    <p className="font-semibold text-midnight">{i.item_description}</p>
                    <p className="text-xs text-midnight/50">
                      {i.location_name} · {i.category} · by {i.staff_name}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      i.status === 'CONVERTED' ? 'bg-mint-soft text-brand' : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {i.status}
                  </span>
                </div>
                {i.status === 'OPEN' && (
                  <Button
                    variant="secondary"
                    className="mt-3"
                    onClick={() => handleConvert(i.id)}
                  >
                    <PackagePlus className="h-4 w-4" /> Convert to found report
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
