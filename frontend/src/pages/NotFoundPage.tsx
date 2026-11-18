import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-mint-soft px-4 text-center">
      <h1 className="text-5xl font-extrabold text-midnight">404</h1>
      <p className="mt-2 text-midnight/60">This page could not be found.</p>
      <Link to="/feed" className="mt-6 font-semibold text-brand hover:underline">
        Go to the feed
      </Link>
    </div>
  )
}
