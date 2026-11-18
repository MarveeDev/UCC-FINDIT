import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AuthShell } from '../components/AuthShell'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { useAuth } from '../context/authContext'
import { getErrorMessage } from '../lib/api'

interface VerifyLocationState {
  email?: string
  devOtp?: string
}

export function VerifyEmailPage() {
  const { verifyEmail, resendOtp } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as VerifyLocationState | null

  const [email, setEmail] = useState(state?.email ?? '')
  const [otp, setOtp] = useState('')
  const [devOtp, setDevOtp] = useState(state?.devOtp)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setNotice(null)
    setSubmitting(true)
    try {
      await verifyEmail(email, otp)
      navigate('/feed', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleResend() {
    setError(null)
    setNotice(null)
    try {
      const nextOtp = await resendOtp(email)
      if (nextOtp) setDevOtp(nextOtp)
      setNotice('A new verification code has been sent.')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <AuthShell
      title="Verify your email"
      subtitle="Enter the 6-digit code sent to your inbox"
      footer={
        <>
          Wrong email?{' '}
          <Link className="font-semibold text-brand hover:underline" to="/register">
            Register again
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && (
          <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
        {notice && (
          <div className="rounded-lg bg-mint-soft px-3 py-2 text-sm text-brand">
            {notice}
          </div>
        )}
        {devOtp && (
          <div className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
            Development mode: your verification code is {devOtp}
          </div>
        )}
        <Input
          id="email"
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          id="otp"
          label="Verification code"
          inputMode="numeric"
          maxLength={6}
          placeholder="000000"
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
          required
        />
        <Button type="submit" fullWidth disabled={submitting}>
          {submitting ? 'Verifying…' : 'Verify email'}
        </Button>
        <button
          type="button"
          onClick={handleResend}
          className="text-center text-sm font-medium text-brand hover:underline"
        >
          Resend code
        </button>
      </form>
    </AuthShell>
  )
}
