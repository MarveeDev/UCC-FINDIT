import type { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, id, className = '', ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-midnight">
          {label}
        </label>
      )}
      <input
        id={id}
        className={`rounded-lg border bg-white px-3 py-2.5 text-sm text-midnight placeholder:text-midnight/40 focus:outline-none focus:ring-2 focus:ring-brand ${
          error ? 'border-red-400' : 'border-midnight/15'
        } ${className}`}
        {...props}
      />
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  )
}
