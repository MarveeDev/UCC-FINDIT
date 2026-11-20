import { useEffect, useState, type FormEvent } from 'react'
import {
  Building2,
  CheckCircle,
  ClipboardList,
  Inbox,
  PackageSearch,
  PlusCircle,
  ShieldCheck,
  UserCog,
  Users,
} from 'lucide-react'
import { StatCard } from '../components/StatCard'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { getErrorMessage } from '../lib/api'
import {
  assignManager,
  createTheatre,
  getAdministrators,
  getLocations,
  getSuperAdminOverview,
  getTheatres,
  removeManager,
} from '../lib/resources'
import type {
  Administrator,
  CampusLocation,
  SuperAdminOverview,
  TheatreSummary,
} from '../types'

export function SuperAdminDashboardPage() {
  const [overview, setOverview] = useState<SuperAdminOverview | null>(null)
  const [theatres, setTheatres] = useState<TheatreSummary[]>([])
  const [administrators, setAdministrators] = useState<Administrator[]>([])
  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [loading, setLoading] = useState(true)

  const [theatreName, setTheatreName] = useState('')
  const [theatreDescription, setTheatreDescription] = useState('')
  const [theatreError, setTheatreError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  const [assignUserId, setAssignUserId] = useState('')
  const [assignLocationId, setAssignLocationId] = useState('')
  const [assignError, setAssignError] = useState<string | null>(null)
  const [assigning, setAssigning] = useState(false)

  function load(): Promise<void> {
    return Promise.all([
      getSuperAdminOverview().then(setOverview).catch(() => setOverview(null)),
      getTheatres().then(setTheatres).catch(() => setTheatres([])),
      getAdministrators().then(setAdministrators).catch(() => setAdministrators([])),
      getLocations().then(setLocations).catch(() => setLocations([])),
    ]).then(() => undefined)
  }

  useEffect(() => {
    load().finally(() => setLoading(false))
  }, [])

  async function handleCreateTheatre(e: FormEvent) {
    e.preventDefault()
    setTheatreError(null)
    setCreating(true)
    try {
      await createTheatre({ name: theatreName, description: theatreDescription || undefined })
      setTheatreName('')
      setTheatreDescription('')
      load()
    } catch (err) {
      setTheatreError(getErrorMessage(err))
    } finally {
      setCreating(false)
    }
  }

  async function handleAssignAdmin(e: FormEvent) {
    e.preventDefault()
    setAssignError(null)
    setAssigning(true)
    try {
      await assignManager(Number(assignLocationId), Number(assignUserId))
      setAssignUserId('')
      setAssignLocationId('')
      load()
    } catch (err) {
      setAssignError(getErrorMessage(err))
    } finally {
      setAssigning(false)
    }
  }

  async function handleRemoveAdmin(admin: Administrator) {
    if (!admin.location_id) return
    try {
      await removeManager(admin.location_id, admin.user.id)
      load()
    } catch (err) {
      setAssignError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-midnight">Super Admin Dashboard</h1>
        <p className="text-sm text-midnight/60">
          Platform overview, lecture theatres, and administrator assignments.
        </p>
      </div>

      {loading || !overview ? (
        <div className="py-16 text-center text-midnight/50">Loading…</div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-5">
            <StatCard label="Students" value={overview.total_students} icon={Users} />
            <StatCard label="Administrators" value={overview.total_administrators} icon={ShieldCheck} />
            <StatCard label="Staff" value={overview.total_staff} icon={UserCog} />
            <StatCard label="Lecture theatres" value={overview.total_theatres} icon={Building2} />
            <StatCard label="Lost reports" value={overview.total_lost} icon={PackageSearch} />
            <StatCard label="Found reports" value={overview.total_found} icon={PlusCircle} />
            <StatCard label="Pending claims" value={overview.pending_claims} icon={ClipboardList} />
            <StatCard label="Recovered" value={overview.recovered} icon={CheckCircle} />
            <StatCard label="Unassigned reports" value={overview.unassigned} icon={Inbox} />
          </div>

          <div className="mt-8 grid gap-6 xl:grid-cols-2">
            {/* Lecture theatres */}
            <section className="rounded-2xl border border-midnight/10 bg-white p-5">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-midnight">
                <Building2 className="h-5 w-5 text-brand" /> Lecture Theatres
              </h2>

              <form onSubmit={handleCreateTheatre} className="mt-4 flex flex-col gap-3">
                {theatreError && (
                  <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{theatreError}</div>
                )}
                <Input
                  label="Theatre name"
                  value={theatreName}
                  onChange={(e) => setTheatreName(e.target.value)}
                  placeholder="e.g. LT1 — New Maths Block"
                  required
                />
                <Input
                  label="Description (optional)"
                  value={theatreDescription}
                  onChange={(e) => setTheatreDescription(e.target.value)}
                />
                <Button type="submit" disabled={creating}>
                  {creating ? 'Creating…' : 'Create theatre'}
                </Button>
              </form>

              <ul className="mt-5 flex flex-col gap-3">
                {theatres.length === 0 && (
                  <p className="text-sm text-midnight/50">No theatres yet.</p>
                )}
                {theatres.map((t) => (
                  <li key={t.id} className="rounded-xl border border-midnight/10 bg-mint-soft/30 p-4">
                    <div className="flex items-center justify-between">
                      <p className="font-semibold text-midnight">{t.name}</p>
                      {!t.is_active && (
                        <span className="rounded-full bg-midnight/10 px-2 py-0.5 text-xs font-semibold text-midnight">
                          Inactive
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-midnight/50">
                      {t.administrator_count} admin(s) · {t.staff_count} staff · {t.lost_count} lost ·{' '}
                      {t.found_count} found
                    </p>
                    {t.administrators.length > 0 && (
                      <p className="mt-2 text-xs text-midnight/60">
                        Admins:{' '}
                        {t.administrators.map((a) => `${a.first_name} ${a.last_name}`).join(', ')}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </section>

            {/* Administrators */}
            <section className="rounded-2xl border border-midnight/10 bg-white p-5">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-midnight">
                <ShieldCheck className="h-5 w-5 text-brand" /> Administrators
              </h2>

              <form onSubmit={handleAssignAdmin} className="mt-4 flex flex-col gap-3">
                {assignError && (
                  <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{assignError}</div>
                )}
                <Select
                  label="Administrator"
                  value={assignUserId}
                  onChange={(e) => setAssignUserId(e.target.value)}
                  required
                >
                  <option value="">Select an administrator</option>
                  {administrators.map((a) => (
                    <option key={a.user.id} value={a.user.id}>
                      {a.user.first_name} {a.user.last_name} ({a.user.email})
                      {a.location_name ? ` — currently: ${a.location_name}` : ' — unassigned'}
                    </option>
                  ))}
                </Select>
                <Select
                  label="Lecture theatre"
                  value={assignLocationId}
                  onChange={(e) => setAssignLocationId(e.target.value)}
                  required
                >
                  <option value="">Select a theatre</option>
                  {locations.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name}
                    </option>
                  ))}
                </Select>
                <Button type="submit" disabled={assigning}>
                  {assigning ? 'Assigning…' : 'Assign administrator'}
                </Button>
              </form>

              <ul className="mt-5 flex flex-col gap-3">
                {administrators.length === 0 && (
                  <p className="text-sm text-midnight/50">No administrators yet.</p>
                )}
                {administrators.map((a) => (
                  <li key={a.user.id} className="rounded-xl border border-midnight/10 bg-mint-soft/30 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-midnight">
                          {a.user.first_name} {a.user.last_name}
                        </p>
                        <p className="text-xs text-midnight/50">{a.user.email}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                            a.location_name
                              ? 'bg-mint-soft text-brand'
                              : 'bg-midnight/10 text-midnight/60'
                          }`}
                        >
                          {a.location_name ?? 'Unassigned'}
                        </span>
                        {a.location_id && (
                          <button
                            type="button"
                            onClick={() => handleRemoveAdmin(a)}
                            className="text-xs font-semibold text-red-600 hover:text-red-700"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </>
      )}
    </div>
  )
}
