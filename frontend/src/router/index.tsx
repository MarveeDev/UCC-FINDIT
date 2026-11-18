import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { ProtectedRoute } from '../components/ProtectedRoute'
import { FeedPage } from '../pages/FeedPage'
import { ItemDetailPage } from '../pages/ItemDetailPage'
import { LoginPage } from '../pages/LoginPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { NotificationsPage } from '../pages/NotificationsPage'
import { RegisterPage } from '../pages/RegisterPage'
import { ReportPage } from '../pages/ReportPage'
import { VerifyEmailPage } from '../pages/VerifyEmailPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/verify-email', element: <VerifyEmailPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <FeedPage /> },
          { path: '/feed', element: <FeedPage /> },
          { path: '/report-lost', element: <ReportPage mode="LOST" /> },
          { path: '/report-found', element: <ReportPage mode="FOUND" /> },
          { path: '/items/:id', element: <ItemDetailPage /> },
          { path: '/notifications', element: <NotificationsPage /> },
        ],
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
])
