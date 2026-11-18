import { useEffect, useState, type FormEvent } from 'react'
import { UserPlus, Users } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { getErrorMessage } from '../lib/api'
import {
  createStaff,
  getManagerLocations,
  getStaff,
  removeStaffAssignment,
} from '../lib/resources'
import type { CampusLocation, StaffMember } from '../types'

export function StaffManagementPage() {
  const [staff, setStaff] = useState<StaffMember[]>([])
  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [locationId, setLocationId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function load() {
    getStaff().then(setStaff).catch(() => setStaff([]))
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
      await createStaff({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        location_id: Number(locationId),
      })
      setFirstName('')
      setLastName('')
      setEmail('')
      setPassword('')
      setLocationId('')
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRemove(userId: number, locationId: number) {
    await removeStaffAssignment(userId, locationId)
    load()
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold text-midnight">Staff Management</h1>
      <p className="text-sm text-midnight/60">Create and manage staff across your locations.</p>

      <form
        onSubmit={handleSubmit}
        className="mt-6 flex flex-col gap-3 rounded-2xl border border-midnight/10 bg-white p-5"
      >
        <h2 className="flex items-center gap-2 font-semibold text-midnight">
          <UserPlus className="h-4 w-4" /> Register staff
        </h2>
        {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <div className="grid grid-cols-2 gap-3">
          <Input label="First name" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
          <Input label="Last name" value={lastName} onChange={(e) => setLastName(e.target.value)} required />
        </div>
        <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Input label="Temporary password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <Select label="Assign to location" value={locationId} onChange={(e) => setLocationId(e.target.value)} required>
          <option value="">Select a location</option>
          {locations.map((l) => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </Select>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Creating…' : 'Create staff'}
        </Button>
      </form>

      <div className="mt-8">
        <h2 className="flex items-center gap-2 font-semibold text-midnight">
          <Users className="h-4 w-4" /> Assigned staff
        </h2>
        {staff.length === 0 ? (
          <p className="mt-3 text-sm text-midnight/50">No staff assigned to your locations.</p>
        ) : (
          <ul className="mt-3 flex flex-col gap-3">
            {staff.map((s) => (
              <li key={s.user.id} className="rounded-2xl border border-midnight/10 bg-white p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-midnight">
                      {s.user.first_name} {s.user.last_name}
                    </p>
                    <p className="text-sm text-midnight/50">{s.user.email}</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {s.assignments.map((a) => (
                      <span
                        key={a.location_id}
                        className="inline-flex items-center gap-1 rounded-full bg-mint-soft px-2.5 py-0.5 text-xs text-brand"
                      >
                        {a.location_name}
                        <button
                          type="button"
                          onClick={() => handleRemove(s.user.id, a.location_id)}
                          className="ml-1 font-bold text-brand/60 hover:text-brand"
                          aria-label={`Remove from ${a.location_name}`}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
