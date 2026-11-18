import { lazy, Suspense, useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { LocationCombobox } from '../components/LocationCombobox'
import type { MapPosition } from '../components/map/MapPicker'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Textarea } from '../components/ui/Textarea'
import { ITEM_CATEGORIES } from '../constants'
import { getErrorMessage, getFieldErrors } from '../lib/api'
import { createReport, getLocations, uploadImage } from '../lib/resources'
import type { CampusLocation, ReportType } from '../types'

const MapPicker = lazy(() =>
  import('../components/map/MapPicker').then((m) => ({ default: m.MapPicker })),
)

interface ReportPageProps {
  mode: ReportType
}

export function ReportPage({ mode }: ReportPageProps) {
  const navigate = useNavigate()
  const isLost = mode === 'LOST'

  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [itemName, setItemName] = useState('')
  const [category, setCategory] = useState('')
  const [description, setDescription] = useState('')
  const [brand, setBrand] = useState('')
  const [colour, setColour] = useState('')
  const [identifying, setIdentifying] = useState('')
  const [custody, setCustody] = useState('')
  const [locationId, setLocationId] = useState('')
  const [locationDescription, setLocationDescription] = useState('')
  const [position, setPosition] = useState<MapPosition | null>(null)
  const [eventDate, setEventDate] = useState('')
  const [eventTime, setEventTime] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    getLocations()
      .then(setLocations)
      .catch(() => setLocations([]))
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setFieldErrors({})
    if (!locationDescription.trim()) {
      setFieldErrors({ location_description: 'Please describe the location' })
      return
    }
    setSubmitting(true)
    try {
      let imagePath: string | undefined
      if (image) {
        const uploaded = await uploadImage(image)
        imagePath = uploaded.filename
      }
      const report = await createReport({
        report_type: mode,
        item_name: itemName,
        category,
        description,
        brand: brand || undefined,
        colour: colour || undefined,
        identifying_characteristics: identifying || undefined,
        custody_info: !isLost && custody ? custody : undefined,
        location_id: locationId ? Number(locationId) : undefined,
        location_description: locationDescription,
        latitude: position?.latitude,
        longitude: position?.longitude,
        event_date: eventDate,
        event_time: eventTime || undefined,
        image_path: imagePath,
      })
      navigate(`/items/${report.id}`)
    } catch (err) {
      setFieldErrors(getFieldErrors(err))
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-midnight">
          Report a {isLost ? 'Lost' : 'Found'} Item
        </h1>
        <p className="text-sm text-midnight/60">
          {isLost
            ? 'Describe the item you lost so the campus can help find it.'
            : 'Report an item you found so its owner can claim it.'}
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4 rounded-2xl border border-midnight/10 bg-white p-6"
      >
        {error && (
          <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
        )}

        <Input
          id="item_name"
          label="Item name"
          placeholder="e.g. Black Dell laptop"
          value={itemName}
          error={fieldErrors.item_name}
          onChange={(e) => setItemName(e.target.value)}
          required
        />

        <Select
          id="category"
          label="Category"
          value={category}
          error={fieldErrors.category}
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
          label="Description"
          rows={3}
          placeholder="Describe the item in a few sentences"
          value={description}
          error={fieldErrors.description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            id="brand"
            label="Brand / model (optional)"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
          />
          <Input
            id="colour"
            label="Colour (optional)"
            value={colour}
            onChange={(e) => setColour(e.target.value)}
          />
        </div>

        <Textarea
          id="identifying"
          label="Identifying characteristics (private, optional)"
          rows={2}
          placeholder="Distinguishing marks that only the owner would know"
          value={identifying}
          onChange={(e) => setIdentifying(e.target.value)}
        />

        {!isLost && (
          <Textarea
            id="custody"
            label="Custody information (optional)"
            rows={2}
            placeholder="Where the item is being held"
            value={custody}
            onChange={(e) => setCustody(e.target.value)}
          />
        )}

        <Input
          id="location_description"
          label="Describe the location"
          placeholder="e.g. Behind the Science Building"
          value={locationDescription}
          error={fieldErrors.location_description}
          onChange={(e) => setLocationDescription(e.target.value)}
          required
        />

        <LocationCombobox
          id="location"
          label="Campus location (optional)"
          value={locationId}
          onChange={setLocationId}
          locations={locations}
        />

        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-midnight">
            Pin the exact spot (optional)
          </label>
          <Suspense
            fallback={
              <div className="h-64 w-full rounded-xl border border-midnight/15 bg-mint-soft/50" />
            }
          >
            <MapPicker value={position} onChange={setPosition} />
          </Suspense>
          {position && (
            <p className="text-xs text-midnight/50">
              Pin: {position.latitude.toFixed(5)}, {position.longitude.toFixed(5)}{' '}
              <button
                type="button"
                onClick={() => setPosition(null)}
                className="font-medium text-brand hover:underline"
              >
                Clear
              </button>
            </p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            id="event_date"
            label={`Date ${isLost ? 'lost' : 'found'}`}
            type="date"
            value={eventDate}
            error={fieldErrors.event_date}
            onChange={(e) => setEventDate(e.target.value)}
            required
          />
          <Input
            id="event_time"
            label="Approximate time (optional)"
            type="time"
            value={eventTime}
            onChange={(e) => setEventTime(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="image" className="text-sm font-medium text-midnight">
            Photo (optional)
          </label>
          <input
            id="image"
            type="file"
            accept="image/*"
            onChange={(e) => setImage(e.target.files?.[0] ?? null)}
          />
        </div>

        <div className="flex gap-3">
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit report'}
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate('/feed')}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
