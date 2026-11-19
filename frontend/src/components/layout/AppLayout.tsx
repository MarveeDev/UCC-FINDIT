import { useEffect, useState } from 'react'
import {
  BarChart3,
  Bell,
  Boxes,
  ClipboardList,
  FileCheck,
  Inbox,
  LayoutDashboard,
  LogOut,
  Menu,
  PackageCheck,
  PackageSearch,
  PlusCircle,
  QrCode,
  ScrollText,
  Sparkles,
  Users,
  X,
  type LucideIcon,
} from 'lucide-react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/authContext'
import { getUnreadCount } from '../../lib/resources'
import type { Role } from '../../types'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  roles?: Role[]
}

const MANAGER_OR_ADMIN: Role[] = ['LOCATION_MANAGER', 'SUPER_ADMIN']
const STAFF_OR_ABOVE: Role[] = ['LOCATION_STAFF', 'LOCATION_MANAGER', 'SUPER_ADMIN']

const navItems: NavItem[] = [
  { to: '/feed', label: 'Community Feed', icon: Boxes },
  { to: '/report-lost', label: 'Report Lost', icon: PackageSearch },
  { to: '/report-found', label: 'Report Found', icon: PlusCircle },
  { to: '/matches', label: 'Possible Matches', icon: Sparkles },
  { to: '/claims/mine', label: 'My Claims', icon: FileCheck, roles: ['STUDENT'] },
  { to: '/claims', label: 'Claims', icon: ClipboardList, roles: STAFF_OR_ABOVE },
  { to: '/qr', label: 'QR Codes', icon: QrCode },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: MANAGER_OR_ADMIN },
  { to: '/staff', label: 'Staff', icon: Users, roles: MANAGER_OR_ADMIN },
  { to: '/inspections', label: 'Inspections', icon: ClipboardList, roles: STAFF_OR_ABOVE },
  { to: '/custody', label: 'Custody', icon: PackageCheck, roles: STAFF_OR_ABOVE },
  { to: '/audit-logs', label: 'Audit Logs', icon: ScrollText, roles: MANAGER_OR_ADMIN },
  { to: '/analytics', label: 'Analytics', icon: BarChart3, roles: MANAGER_OR_ADMIN },
  { to: '/admin/unassigned', label: 'Unassigned Reports', icon: Inbox, roles: ['SUPER_ADMIN'] },
  { to: '/notifications', label: 'Notifications', icon: Bell },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [unread, setUnread] = useState(0)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    getUnreadCount()
      .then(setUnread)
      .catch(() => setUnread(0))
  }, [])

  // Close the drawer on Escape and lock body scroll while it is open.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setDrawerOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  useEffect(() => {
    document.body.style.overflow = drawerOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [drawerOpen])

  function handleLogout() {
    setDrawerOpen(false)
    logout()
    navigate('/login', { replace: true })
  }

  function closeDrawer() {
    setDrawerOpen(false)
  }

  const visibleItems = navItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role)),
  )

  const renderNav = (onNavigate?: () => void) =>
    visibleItems.map((item) => (
      <NavLink
        key={item.to}
        to={item.to}
        onClick={onNavigate}
        className={({ isActive }) =>
          `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
            isActive ? 'bg-brand text-white' : 'text-white/70 hover:bg-white/10'
          }`
        }
      >
        <item.icon className="h-5 w-5" />
        {item.label}
      </NavLink>
    ))

  const renderUser = () => (
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
  )

  return (
    <div className="flex min-h-screen bg-mint-soft/60">
      {/* Desktop sidebar (unchanged) */}
      <aside className="hidden w-64 flex-col bg-midnight text-white md:flex">
        <div className="flex items-center px-6 py-6">
          <span className="text-xl font-extrabold tracking-tight">
            UCC <span className="text-mint">FINDIT</span>
          </span>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3">{renderNav()}</nav>
        {renderUser()}
      </aside>

      {/* Mobile slide-out drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={closeDrawer}
            aria-hidden="true"
          />
          <aside className="absolute inset-y-0 left-0 flex w-72 max-w-[85%] flex-col bg-midnight text-white shadow-xl">
            <div className="flex items-center justify-between px-4 pb-4 pt-[calc(1rem+env(safe-area-inset-top))]">
              <span className="text-xl font-extrabold tracking-tight">
                UCC <span className="text-mint">FINDIT</span>
              </span>
              <button
                type="button"
                onClick={closeDrawer}
                aria-label="Close menu"
                className="rounded-lg p-2 text-white/70 transition hover:bg-white/10 hover:text-white"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <nav className="flex-1 space-y-1 overflow-y-auto px-3">{renderNav(closeDrawer)}</nav>
            <div className="pb-[env(safe-area-inset-bottom)]">{renderUser()}</div>
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile header */}
        <header className="flex items-center justify-between border-b border-midnight/10 bg-white px-4 py-3 md:hidden">
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open menu"
            className="rounded-lg p-2 text-midnight/70 transition hover:bg-mint-soft"
          >
            <Menu className="h-6 w-6" />
          </button>
          <span className="text-lg font-extrabold tracking-tight text-midnight">
            UCC <span className="text-brand">FINDIT</span>
          </span>
          <Link to="/notifications" className="relative text-midnight/60 hover:text-brand">
            <Bell className="h-5 w-5" />
            {unread > 0 && (
              <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand px-1 text-[10px] font-bold text-white">
                {unread > 9 ? '9+' : unread}
              </span>
            )}
          </Link>
        </header>

        {/* Desktop header */}
        <header className="hidden items-center justify-between border-b border-midnight/10 bg-white px-6 py-4 md:flex">
          <div className="text-sm font-medium text-midnight/60">
            {user?.role.replaceAll('_', ' ')}
          </div>
          <Link to="/notifications" className="relative text-midnight/60 hover:text-brand">
            <Bell className="h-5 w-5" />
            {unread > 0 && (
              <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand px-1 text-[10px] font-bold text-white">
                {unread > 9 ? '9+' : unread}
              </span>
            )}
          </Link>
        </header>

        <main className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
