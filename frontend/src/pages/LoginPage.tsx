import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AuthShell } from '../components/AuthShell'
import { GoogleSignInButton } from '../components/GoogleSignInButton'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { useAuth } from '../context/authContext'
import { getErrorMessage } from '../lib/api'

const GOOGLE_ERROR_MESSAGES: Record<string, string> = {
  google_sign_in_failed: 'Google sign-in failed. Please try again.',
  google_sign_in_disabled: 'Google sign-in is not available right now.',
  ucc_email_required: 'Please sign in with your official UCC email address.',
  google_email_unverified: 'Your Google account email is not verified.',
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const success = (location.state as { success?: string } | null)?.success
  const googleError = new URLSearchParams(location.search).get('error')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const displayError = googleError
    ? (GOOGLE_ERROR_MESSAGES[googleError] ?? GOOGLE_ERROR_MESSAGES.google_sign_in_failed)
    : error

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/feed', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to your UCC FINDIT account"
      footer={
        <>
          Don&apos;t have an account?{' '}
          <Link className="font-semibold text-mint hover:text-white hover:underline" to="/register">
            Create one
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {success && (
          <div className="rounded-lg bg-mint-soft px-3 py-2 text-sm text-brand">
            {success}
          </div>
        )}
        {displayError && (
          <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {displayError}
          </div>
        )}
        <Input
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          id="password"
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <Button type="submit" fullWidth disabled={submitting}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
      <div className="mt-5 flex items-center gap-3">
        <div className="h-px flex-1 bg-midnight/10" />
        <span className="text-xs text-midnight/50">or</span>
        <div className="h-px flex-1 bg-midnight/10" />
      </div>
      <div className="mt-4">
        <GoogleSignInButton />
      </div>
    </AuthShell>
  )
}
