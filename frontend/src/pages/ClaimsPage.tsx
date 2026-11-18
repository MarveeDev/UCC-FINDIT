import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle, XCircle, HelpCircle } from 'lucide-react'
import { useAuth } from '../context/authContext'
import { getErrorMessage } from '../lib/api'
import { getClaims, reviewClaim, verifyHandover } from '../lib/resources'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import type { Claim, ClaimStatus } from '../types'

const tabs: { key: string; label: string }[] = [
  { key: '', label: 'All' },
  { key: 'PENDING', label: 'Pending' },
  { key: 'APPROVED', label: 'Approved' },
  { key: 'REJECTED', label: 'Rejected' },
]

const statusStyles: Record<ClaimStatus, string> = {
  PENDING: 'bg-amber-100 text-amber-800',
  MORE_INFORMATION_REQUIRED: 'bg-blue-100 text-blue-800',
  APPROVED: 'bg-mint-soft text-brand',
  REJECTED: 'bg-red-100 text-red-700',
}

export function ClaimsPage() {
  const { user } = useAuth()
  const canReview = user?.role === 'LOCATION_MANAGER' || user?.role === 'SUPER_ADMIN'

  const [tab, setTab] = useState('')
  const [claims, setClaims] = useState<Claim[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [approvedCode, setApprovedCode] = useState<string | null>(null)
  const [handoverClaimId, setHandoverClaimId] = useState<number | null>(null)
  const [handoverCode, setHandoverCode] = useState('')
  const [handoverMessage, setHandoverMessage] = useState<string | null>(null)

  function refresh(status?: string) {
    getClaims(status ?? tab)
      .then(setClaims)
      .catch((err) => setError(getErrorMessage(err)))
  }

  useEffect(() => {
    getClaims(tab)
      .then(setClaims)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [tab])

  async function handleReview(claimId: number, decision: string) {
    setError(null)
    setApprovedCode(null)
    try {
      const result = await reviewClaim(claimId, decision)
      if (result.collection_code) setApprovedCode(result.collection_code)
      refresh()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function handleVerify(claimId: number) {
    setError(null)
    setHandoverMessage(null)
    try {
      await verifyHandover(claimId, handoverCode)
      setHandoverMessage('Handover complete — item marked as recovered.')
      setHandoverCode('')
      setHandoverClaimId(null)
      refresh()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold text-midnight">Claims</h1>
      <p className="text-sm text-midnight/60">
        {canReview ? 'Review ownership claims for your locations.' : 'Manage item handovers.'}
      </p>

      <div className="mt-4 flex gap-1 overflow-x-auto rounded-xl bg-white p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${
              tab === t.key ? 'bg-brand text-white' : 'text-midnight/70 hover:bg-mint-soft'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
      )}
      {handoverMessage && (
        <div className="mt-4 rounded-lg bg-mint-soft px-3 py-2 text-sm text-brand">{handoverMessage}</div>
      )}
      {approvedCode && (
        <div className="mt-4 rounded-lg bg-mint-soft p-3 text-center">
          <p className="text-xs text-brand">Collection code (give to the claimant)</p>
          <p className="mt-1 font-mono text-2xl font-bold tracking-widest text-midnight">{approvedCode}</p>
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center text-midnight/50">Loading…</div>
      ) : claims.length === 0 ? (
        <div className="mt-6 rounded-2xl border border-dashed border-midnight/15 bg-white py-16 text-center text-midnight/60">
          No claims found.
        </div>
      ) : (
        <ul className="mt-4 flex flex-col gap-3">
          {claims.map((claim) => (
            <li key={claim.id} className="rounded-2xl border border-midnight/10 bg-white p-5">
              <div className="flex items-center justify-between">
                <div>
                  <Link to={`/items/${claim.report_id}`} className="font-semibold text-midnight hover:text-brand">
                    {claim.report.item_name}
                  </Link>
                  <p className="text-xs text-midnight/50">Claimed by {claim.claimant_name}</p>
                </div>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusStyles[claim.status]}`}>
                  {claim.status.replaceAll('_', ' ')}
                </span>
              </div>

              {claim.evidence && (
                <div className="mt-3 rounded-lg bg-mint-soft/60 p-3 text-sm text-midnight">
                  <p className="text-xs font-medium text-brand">Ownership evidence</p>
                  <p className="mt-1">{claim.evidence}</p>
                </div>
              )}

              {canReview && (claim.status === 'PENDING' || claim.status === 'MORE_INFORMATION_REQUIRED') && (
                <div className="mt-4 flex gap-2">
                  <Button onClick={() => handleReview(claim.id, 'APPROVED')}>
                    <CheckCircle className="h-4 w-4" /> Approve
                  </Button>
                  <Button variant="secondary" onClick={() => handleReview(claim.id, 'MORE_INFORMATION_REQUIRED')}>
                    <HelpCircle className="h-4 w-4" /> Request info
                  </Button>
                  <Button variant="ghost" onClick={() => handleReview(claim.id, 'REJECTED')}>
                    <XCircle className="h-4 w-4" /> Reject
                  </Button>
                </div>
              )}

              {claim.status === 'APPROVED' && (
                <div className="mt-4">
                  {handoverClaimId === claim.id ? (
                    <div className="flex gap-2">
                      <Input
                        placeholder="Enter collection code"
                        value={handoverCode}
                        onChange={(e) => setHandoverCode(e.target.value)}
                      />
                      <Button onClick={() => handleVerify(claim.id)}>Verify</Button>
                      <Button variant="ghost" onClick={() => setHandoverClaimId(null)}>
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <Button variant="secondary" onClick={() => setHandoverClaimId(claim.id)}>
                      Complete handover
                    </Button>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
