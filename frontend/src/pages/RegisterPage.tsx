import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AuthShell } from '../components/AuthShell'
import { GoogleSignInButton } from '../components/GoogleSignInButton'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { useAuth } from '../context/authContext'
import { getErrorMessage, getFieldErrors } from '../lib/api'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setFieldErrors({})
    setSubmitting(true)
    try {
      await register({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
      })
      navigate('/login', { state: { success: 'Account created. You can now sign in.' } })
    } catch (err) {
      setFieldErrors(getFieldErrors(err))
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Join the UCC campus lost and found network"
      footer={
        <>
          Already have an account?{' '}
          <Link className="font-semibold text-mint hover:text-white hover:underline" to="/login">
            Sign in
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
        <div className="grid grid-cols-2 gap-4">
          <Input
            id="first_name"
            label="First name"
            autoComplete="given-name"
            value={firstName}
            error={fieldErrors.first_name}
            onChange={(e) => setFirstName(e.target.value)}
            required
          />
          <Input
            id="last_name"
            label="Last name"
            autoComplete="family-name"
            value={lastName}
            error={fieldErrors.last_name}
            onChange={(e) => setLastName(e.target.value)}
            required
          />
        </div>
        <Input
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          error={fieldErrors.email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          id="password"
          label="Password"
          type="password"
          autoComplete="new-password"
          value={password}
          error={fieldErrors.password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <Button type="submit" fullWidth disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
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
