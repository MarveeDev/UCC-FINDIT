import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  label: string
  value: number | string
  icon: LucideIcon
}

export function StatCard({ label, value, icon: Icon }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-midnight/10 bg-white p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-midnight/60">{label}</p>
        <Icon className="h-5 w-5 text-mint" />
      </div>
      <p className="mt-2 text-3xl font-bold text-midnight">{value}</p>
    </div>
  )
}
