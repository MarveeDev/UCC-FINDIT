import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from 'react'
import { ChevronDown, Search, X } from 'lucide-react'
import type { CampusLocation } from '../types'

interface LocationComboboxProps {
  id?: string
  label?: string
  value: string
  onChange: (value: string) => void
  locations: CampusLocation[]
  error?: string
  required?: boolean
}

export function LocationCombobox({
  id,
  label,
  value,
  onChange,
  locations,
  error,
  required,
}: LocationComboboxProps) {
  const [open, setOpen] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [highlighted, setHighlighted] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selected = useMemo(
    () => locations.find((l) => String(l.id) === value) ?? null,
    [locations, value],
  )

  const filtered = useMemo(() => {
    const q = inputValue.trim().toLowerCase()
    if (!q) return locations
    return locations.filter((l) => l.name.toLowerCase().includes(q))
  }, [locations, inputValue])

  // Close and reset the displayed text when clicking outside the component.
  useEffect(() => {
    function onDocMouseDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
        setInputValue(selected?.name ?? '')
      }
    }
    document.addEventListener('mousedown', onDocMouseDown)
    return () => document.removeEventListener('mousedown', onDocMouseDown)
  }, [selected])

  function selectLocation(loc: CampusLocation) {
    onChange(String(loc.id))
    setInputValue(loc.name)
    setOpen(false)
  }

  function clearSelection() {
    onChange('')
    setInputValue('')
    setOpen(true)
    setHighlighted(0)
    inputRef.current?.focus()
  }

  function handleKeyDown(e: ReactKeyboardEvent<HTMLInputElement>) {
    if (!open) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        e.preventDefault()
        setOpen(true)
      }
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlighted((h) => Math.min(h + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlighted((h) => Math.max(h - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (filtered[highlighted]) selectLocation(filtered[highlighted])
    } else if (e.key === 'Escape') {
      setOpen(false)
      setInputValue(selected?.name ?? '')
    }
  }

  return (
    <div ref={containerRef} className="relative flex flex-col gap-1">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-midnight">
          {label}
        </label>
      )}
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-midnight/40" />
        <input
          ref={inputRef}
          id={id}
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-controls={id ? `${id}-listbox` : undefined}
          aria-autocomplete="list"
          aria-activedescendant={
            open && filtered[highlighted] ? `${id}-option-${filtered[highlighted].id}` : undefined
          }
          className={`w-full rounded-lg border bg-white py-2.5 pl-9 pr-8 text-sm text-midnight placeholder:text-midnight/40 focus:outline-none focus:ring-2 focus:ring-brand ${
            error ? 'border-red-400' : 'border-midnight/15'
          }`}
          placeholder="Search for a campus location…"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value)
            setOpen(true)
            setHighlighted(0)
          }}
          onFocus={() => {
            setOpen(true)
            setInputValue('')
            setHighlighted(0)
          }}
          onKeyDown={handleKeyDown}
          required={required}
        />
        {selected ? (
          <button
            type="button"
            onClick={clearSelection}
            className="absolute right-2 top-2.5 text-midnight/40 transition hover:text-brand"
            aria-label="Clear location"
          >
            <X className="h-4 w-4" />
          </button>
        ) : (
          <ChevronDown className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-midnight/40" />
        )}
      </div>

      {open && (
        <ul
          id={id ? `${id}-listbox` : undefined}
          role="listbox"
          className="absolute top-full z-20 mt-1 max-h-56 w-full overflow-auto rounded-lg border border-midnight/10 bg-white shadow-md"
        >
          {filtered.length === 0 ? (
            <li className="px-3 py-2 text-sm text-midnight/50">No locations found</li>
          ) : (
            filtered.map((loc, i) => (
              <li
                key={loc.id}
                id={`${id}-option-${loc.id}`}
                role="option"
                aria-selected={String(loc.id) === value}
                onMouseDown={(e) => {
                  e.preventDefault()
                  selectLocation(loc)
                }}
                onMouseEnter={() => setHighlighted(i)}
                className={`cursor-pointer px-3 py-2 text-sm ${
                  i === highlighted ? 'bg-mint-soft text-midnight' : 'text-midnight'
                } ${String(loc.id) === value ? 'font-semibold text-brand' : ''}`}
              >
                {loc.name}
              </li>
            ))
          )}
        </ul>
      )}
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  )
}
