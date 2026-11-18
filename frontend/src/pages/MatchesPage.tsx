import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { getMatches } from '../lib/resources'
import type { Match } from '../types'

export function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMatches()
      .then(setMatches)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold text-midnight">Possible Matches</h1>
      <p className="text-sm text-midnight/60">
        Potential links between lost and found reports, ranked by score.
      </p>

      {loading ? (
        <div className="py-16 text-center text-midnight/50">Loading…</div>
      ) : matches.length === 0 ? (
        <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-midnight/15 bg-white py-16 text-center">
          <Sparkles className="h-10 w-10 text-mint" />
          <h2 className="mt-4 text-lg font-semibold text-midnight">No matches yet</h2>
          <p className="mt-1 text-sm text-midnight/60">
            When a lost and found report look alike, they&apos;ll appear here.
          </p>
        </div>
      ) : (
        <ul className="mt-6 flex flex-col gap-4">
          {matches.map((match) => (
            <li key={match.id} className="rounded-2xl border border-midnight/10 bg-white p-5">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-brand px-2.5 py-0.5 text-xs font-semibold text-white">
                  {match.score}% match
                </span>
                <span className="text-xs text-midnight/50">
                  {new Date(match.created_at).toLocaleDateString()}
                </span>
              </div>
              {match.reasons.length > 0 && (
                <ul className="mt-3 flex flex-wrap gap-2">
                  {match.reasons.map((reason) => (
                    <li key={reason} className="rounded-full bg-mint-soft px-2.5 py-0.5 text-xs text-brand">
                      {reason}
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <Link
                  to={`/items/${match.lost_report.id}`}
                  className="rounded-xl border border-amber-200 bg-amber-50 p-3 hover:border-amber-400"
                >
                  <p className="text-xs font-semibold uppercase text-amber-700">Lost</p>
                  <p className="mt-1 font-medium text-midnight">{match.lost_report.item_name}</p>
                  <p className="text-xs text-midnight/50">{match.lost_report.location_name}</p>
                </Link>
                <Link
                  to={`/items/${match.found_report.id}`}
                  className="rounded-xl border border-mint bg-mint-soft/50 p-3 hover:border-mint"
                >
                  <p className="text-xs font-semibold uppercase text-brand">Found</p>
                  <p className="mt-1 font-medium text-midnight">{match.found_report.item_name}</p>
                  <p className="text-xs text-midnight/50">{match.found_report.location_name}</p>
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
