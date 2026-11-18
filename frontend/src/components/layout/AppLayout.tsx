import { Bell, Boxes, LogOut, Search, type LucideIcon } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/authContext'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  disabled?: boolean
}

const navItems: NavItem[] = [
  { to: '/feed', label: 'Community Feed', icon: Boxes },
  { to: '/notifications', label: 'Notifications', icon: Bell, disabled: true },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex min-h-screen bg-mint-soft/60">
      <aside className="hidden w-64 flex-col bg-midnight text-white md:flex">
        <div className="flex items-center px-6 py-6">
          <span className="text-xl font-extrabold tracking-tight">
            UCC <span className="text-mint">FINDIT</span>
          </span>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {navItems.map((item) => {
            if (item.disabled) {
              return (
                <span
                  key={item.to}
                  className="flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-white/40"
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </span>
              )
            }
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                    isActive
                      ? 'bg-brand text-white'
                      : 'text-white/70 hover:bg-white/10'
                  }`
                }
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </NavLink>
            )
          })}
        </nav>
        <div className="border-t border-white/10 p-4">
          <div className="mb-3 px-1">
            <p className="truncate text-sm font-semibold">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="truncate text-xs text-white/50">{user?.email}</p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/70 transition hover:bg-white/10"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-midnight/10 bg-white px-6 py-4">
          <div className="flex items-center gap-2 text-sm text-midnight/60">
            <Search className="h-4 w-4" /> Search campus reports
          </div>
          <div className="text-xs font-semibold uppercase tracking-wide text-midnight/50">
            {user?.role.replaceAll('_', ' ')}
          </div>
        </header>
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
