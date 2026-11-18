import type { SelectHTMLAttributes } from 'react'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
}

export function Select({ label, error, id, className = '', children, ...props }: SelectProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-midnight">
          {label}
        </label>
      )}
      <select
        id={id}
        className={`rounded-lg border bg-white px-3 py-2.5 text-sm text-midnight focus:outline-none focus:ring-2 focus:ring-brand ${
          error ? 'border-red-400' : 'border-midnight/15'
        } ${className}`}
        {...props}
      >
        {children}
      </select>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  )
}
