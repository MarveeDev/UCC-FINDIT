import { PackageSearch } from 'lucide-react'
import { useAuth } from '../context/authContext'

export function FeedPage() {
  const { user } = useAuth()

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-midnight">Community Feed</h1>
        <p className="text-sm text-midnight/60">
          Welcome back, {user?.first_name}. Campus-wide lost and found reports.
        </p>
      </div>
      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-midnight/15 bg-white py-20 text-center">
        <PackageSearch className="h-10 w-10 text-mint" />
        <h2 className="mt-4 text-lg font-semibold text-midnight">
          The feed is coming next
        </h2>
        <p className="mt-1 max-w-sm text-sm text-midnight/60">
          Authentication is working. Reporting and the campus-wide community feed
          are the next vertical slice.
        </p>
      </div>
    </div>
  )
}
