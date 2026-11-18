import type { ReactNode } from 'react'

interface AuthShellProps {
  title: string
  subtitle?: string
  children: ReactNode
  footer?: ReactNode
}

export function AuthShell({ title, subtitle, children, footer }: AuthShellProps) {
  return (
    <div
      className="flex min-h-screen items-center justify-center px-4 py-10"
      style={{
        backgroundImage:
          'linear-gradient(rgba(9, 47, 43, 0.75), rgba(9, 47, 43, 0.75)), url("/images/ucc-campus-background.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <div className="w-full max-w-md">
        <div className="mb-4 flex items-center justify-center">
          <div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-full bg-white p-2 shadow-lg sm:h-24 sm:w-24">
            <img
              src="/images/ucc-official-logo.png"
              alt="University of Cape Coast logo"
              className="h-full w-full object-contain"
            />
          </div>
        </div>
        <div className="mb-6 flex items-center justify-center">
          <span className="text-2xl font-extrabold tracking-tight text-white">
            UCC <span className="text-mint">FINDIT</span>
          </span>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white p-8 shadow-lg">
          <h1 className="text-xl font-bold text-midnight">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-midnight/60">{subtitle}</p>}
          <div className="mt-6">{children}</div>
        </div>
        {footer && (
          <div className="mt-6 text-center text-sm text-white/70">{footer}</div>
        )}
      </div>
    </div>
  )
}
