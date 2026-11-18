import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileCheck } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Textarea } from '../components/ui/Textarea'
import { getMyClaims, resubmitClaim } from '../lib/resources'
import type { Claim, ClaimStatus } from '../types'

const statusStyles: Record<ClaimStatus, string> = {
  PENDING: 'bg-amber-100 text-amber-800',
  MORE_INFORMATION_REQUIRED: 'bg-blue-100 text-blue-800',
  APPROVED: 'bg-mint-soft text-brand',
  REJECTED: 'bg-red-100 text-red-700',
}

export function MyClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([])
  const [loading, setLoading] = useState(true)
  const [resubmitId, setResubmitId] = useState<number | null>(null)
  const [resubmitEvidence, setResubmitEvidence] = useState('')
  const [resubmitting, setResubmitting] = useState(false)

  function load() {
    getMyClaims()
      .then(setClaims)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  async function handleResubmit(claimId: number) {
    setResubmitting(true)
    try {
      await resubmitClaim(claimId, resubmitEvidence)
      setResubmitId(null)
      setResubmitEvidence('')
      load()
    } finally {
      setResubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-midnight">My Claims</h1>
      <p className="text-sm text-midnight/60">Track your ownership claims and collection codes.</p>

      {loading ? (
        <div className="py-16 text-center text-midnight/50">Loading…</div>
      ) : claims.length === 0 ? (
        <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-midnight/15 bg-white py-16 text-center">
          <FileCheck className="h-10 w-10 text-mint" />
          <h2 className="mt-4 text-lg font-semibold text-midnight">No claims yet</h2>
          <p className="mt-1 text-sm text-midnight/60">
            Use “This Is Mine” on a found item to claim it.
          </p>
        </div>
      ) : (
        <ul className="mt-6 flex flex-col gap-3">
          {claims.map((claim) => (
            <li key={claim.id} className="rounded-2xl border border-midnight/10 bg-white p-5">
              <div className="flex items-center justify-between">
                <Link to={`/items/${claim.report_id}`} className="font-semibold text-midnight hover:text-brand">
                  {claim.report.item_name}
                </Link>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusStyles[claim.status]}`}>
                  {claim.status.replaceAll('_', ' ')}
                </span>
              </div>
              {claim.review_note && (
                <p className="mt-2 text-sm text-midnight/60">Reviewer note: {claim.review_note}</p>
              )}
              {claim.status === 'MORE_INFORMATION_REQUIRED' && (
                <div className="mt-3">
                  {resubmitId === claim.id ? (
                    <div className="flex flex-col gap-2">
                      <Textarea
                        rows={2}
                        placeholder="Provide additional ownership evidence…"
                        value={resubmitEvidence}
                        onChange={(e) => setResubmitEvidence(e.target.value)}
                      />
                      <div className="flex gap-2">
                        <Button disabled={resubmitting} onClick={() => handleResubmit(claim.id)}>
                          Submit
                        </Button>
                        <Button variant="ghost" onClick={() => setResubmitId(null)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button variant="secondary" onClick={() => setResubmitId(claim.id)}>
                      Provide more information
                    </Button>
                  )}
                </div>
              )}
              {claim.status === 'APPROVED' && (
                <div className="mt-3 rounded-lg bg-mint-soft p-3 text-sm text-midnight">
                  <p className="font-medium text-brand">Approved for collection</p>
                  <p className="mt-1 text-midnight/70">
                    Your collection code will be provided at the collection office.
                  </p>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
