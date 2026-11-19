import { lazy, Suspense, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { LayoutList, Map as MapIcon, PackageSearch, PlusCircle, Search } from 'lucide-react'
import { ReportCard } from '../components/ReportCard'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { ITEM_CATEGORIES } from '../constants'
import { getFeed, getLocations } from '../lib/resources'
import type { CampusLocation, Paginated, ReportSummary } from '../types'

const ReportMap = lazy(() =>
  import('../components/map/ReportMap').then((m) => ({ default: m.ReportMap })),
)

type Tab = 'all' | 'lost' | 'found' | 'recovered'

const tabs: { key: Tab; label: string }[] = [
  { key: 'all', label: 'All Items' },
  { key: 'lost', label: 'Lost' },
  { key: 'found', label: 'Found' },
  { key: 'recovered', label: 'Recovered' },
]

export function FeedPage() {
  const [tab, setTab] = useState<Tab>('all')
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [locationId, setLocationId] = useState('')
  const [category, setCategory] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [sort, setSort] = useState<'newest' | 'oldest'>('newest')
  const [page, setPage] = useState(1)
  const [view, setView] = useState<'list' | 'map'>('list')

  const [locations, setLocations] = useState<CampusLocation[]>([])
  const [result, setResult] = useState<Paginated<ReportSummary> | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getLocations()
      .then(setLocations)
      .catch(() => setLocations([]))
  }, [])

  useEffect(() => {
    getFeed({
      type: tab,
      search: search || undefined,
      location_id: locationId ? Number(locationId) : undefined,
      category: category || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      sort,
      page,
    })
      .then(setResult)
      .catch(() => setResult(null))
      .finally(() => setLoading(false))
  }, [tab, search, locationId, category, dateFrom, dateTo, sort, page])

  function handleSearch(e: FormEvent) {
    e.preventDefault()
    setPage(1)
    setSearch(searchInput)
  }

  function resetAndSet(setter: (value: string) => void, value: string) {
    setter(value)
    setPage(1)
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-midnight">Community Feed</h1>
          <p className="text-sm text-midnight/60">Campus-wide lost and found reports.</p>
        </div>
        <div className="flex gap-2">
          <Link to="/report-lost">
            <Button variant="secondary">
              <PackageSearch className="h-4 w-4" /> Report Lost
            </Button>
          </Link>
          <Link to="/report-found">
            <Button>
              <PlusCircle className="h-4 w-4" /> Report Found
            </Button>
          </Link>
        </div>
      </div>

      <div className="mb-4 flex gap-1 overflow-x-auto rounded-xl bg-white p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => {
              setTab(t.key)
              setPage(1)
            }}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              tab === t.key ? 'bg-brand text-white' : 'text-midnight/70 hover:bg-mint-soft'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <form
        onSubmit={handleSearch}
        className="mb-6 grid grid-cols-1 gap-3 rounded-2xl border border-midnight/10 bg-white p-4 md:grid-cols-3"
      >
        <div className="md:col-span-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-midnight/40" />
              <input
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search items…"
                className="w-full rounded-lg border border-midnight/15 bg-white py-2.5 pl-9 pr-3 text-sm text-midnight focus:outline-none focus:ring-2 focus:ring-brand"
              />
            </div>
            <Button type="submit" variant="secondary">
              Search
            </Button>
          </div>
        </div>

        <Select
          id="location"
          value={locationId}
          onChange={(e) => resetAndSet(setLocationId, e.target.value)}
        >
          <option value="">All locations</option>
          {locations.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name}
            </option>
          ))}
        </Select>

        <Select
          id="category"
          value={category}
          onChange={(e) => resetAndSet(setCategory, e.target.value)}
        >
          <option value="">All categories</option>
          {ITEM_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </Select>

        <Select
          id="sort"
          value={sort}
          onChange={(e) => {
            setSort(e.target.value as 'newest' | 'oldest')
            setPage(1)
          }}
        >
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
        </Select>

        <Input
          id="date_from"
          type="date"
          label="From date"
          value={dateFrom}
          onChange={(e) => resetAndSet(setDateFrom, e.target.value)}
        />
        <Input
          id="date_to"
          type="date"
          label="To date"
          value={dateTo}
          onChange={(e) => resetAndSet(setDateTo, e.target.value)}
        />
      </form>

      <div className="mb-4 flex items-center gap-2">
        <span className="text-sm font-medium text-midnight/60">View:</span>
        <button
          type="button"
          onClick={() => setView('list')}
          className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold transition ${
            view === 'list' ? 'bg-brand text-white' : 'bg-white text-midnight/70 hover:bg-mint-soft'
          }`}
        >
          <LayoutList className="h-4 w-4" /> List
        </button>
        <button
          type="button"
          onClick={() => setView('map')}
          className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold transition ${
            view === 'map' ? 'bg-brand text-white' : 'bg-white text-midnight/70 hover:bg-mint-soft'
          }`}
        >
          <MapIcon className="h-4 w-4" /> Map
        </button>
      </div>

      {loading ? (
        <div className="py-16 text-center text-midnight/50">Loading reports…</div>
      ) : view === 'map' ? (
        <Suspense
          fallback={
            <div className="h-[420px] w-full rounded-xl border border-midnight/15 bg-mint-soft/50" />
          }
        >
          <ReportMap reports={result?.items ?? []} />
        </Suspense>
      ) : !result || result.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-midnight/15 bg-white py-16 text-center">
          <PackageSearch className="h-10 w-10 text-mint" />
          <h2 className="mt-4 text-lg font-semibold text-midnight">No reports found</h2>
          <p className="mt-1 max-w-sm text-sm text-midnight/60">
            Try adjusting your filters, or be the first to report an item.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {result.items.map((report) => (
            <ReportCard key={report.id} report={report} />
          ))}
        </div>
      )}

      {result && result.pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-4">
          <Button
            variant="secondary"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
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
    </div>
  )
}
