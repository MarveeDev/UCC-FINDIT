import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/authContext'

export function GoogleCallbackPage() {
  const { completeGoogleLogin } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState('Signing you in…')
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true

    const code = searchParams.get('code')
    if (!code) {
      navigate('/login?error=google_sign_in_failed', { replace: true })
      return
    }
    completeGoogleLogin(code)
      .then(() => navigate('/feed', { replace: true }))
      .catch(() => {
        setStatus('Google sign-in failed. Redirecting…')
        navigate('/login?error=google_sign_in_failed', { replace: true })
      })
  }, [completeGoogleLogin, navigate, searchParams])

  return (
    <div className="flex min-h-screen items-center justify-center bg-mint-soft px-4 text-midnight">
      <p className="text-sm font-medium">{status}</p>
    </div>
  )
}
