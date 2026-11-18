import type { ReactNode } from 'react'

interface AuthShellProps {
  title: string
  subtitle?: string
  children: ReactNode
  footer?: ReactNode
}

export function AuthShell({ title, subtitle, children, footer }: AuthShellProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-mint-soft px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center">
          <span className="text-2xl font-extrabold tracking-tight text-midnight">
            UCC <span className="text-brand">FINDIT</span>
          </span>
        </div>
        <div className="rounded-2xl border border-midnight/10 bg-white p-8 shadow-sm">
          <h1 className="text-xl font-bold text-midnight">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-midnight/60">{subtitle}</p>}
          <div className="mt-6">{children}</div>
        </div>
        {footer && (
          <div className="mt-6 text-center text-sm text-midnight/60">{footer}</div>
        )}
      </div>
    </div>
  )
}
