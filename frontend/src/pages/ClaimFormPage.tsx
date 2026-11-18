import { useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { AuthShell } from '../components/AuthShell'
import { Button } from '../components/ui/Button'
import { Textarea } from '../components/ui/Textarea'
import { getErrorMessage } from '../lib/api'
import { createClaim } from '../lib/resources'

export function ClaimFormPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const reportId = searchParams.get('report_id')

  const [evidence, setEvidence] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!reportId) return
    setError(null)
    setSubmitting(true)
    try {
      await createClaim(Number(reportId), evidence)
      navigate('/claims/mine')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      title="Claim this item"
      subtitle="Provide details only the owner would know"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && (
          <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
        )}
        <Textarea
          id="evidence"
          label="Ownership evidence"
          rows={4}
          placeholder="e.g. It has a sticker on the bottom, a scratch on the lid, a name inside…"
          value={evidence}
          onChange={(e) => setEvidence(e.target.value)}
          required
        />
        <p className="text-xs text-midnight/50">
          Your evidence is private and only visible to authorized reviewers.
        </p>
        <div className="flex gap-3">
          <Button type="submit" disabled={submitting || !reportId}>
            {submitting ? 'Submitting…' : 'Submit claim'}
          </Button>
          <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
            Cancel
          </Button>
        </div>
      </form>
    </AuthShell>
  )
}
