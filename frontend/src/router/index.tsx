import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { ProtectedRoute } from '../components/ProtectedRoute'
import { AnalyticsPage } from '../pages/AnalyticsPage'
import { AuditLogsPage } from '../pages/AuditLogsPage'
import { ClaimFormPage } from '../pages/ClaimFormPage'
import { ClaimsPage } from '../pages/ClaimsPage'
import { CustodyPage } from '../pages/CustodyPage'
import { FeedPage } from '../pages/FeedPage'
import { InspectionsPage } from '../pages/InspectionsPage'
import { ItemDetailPage } from '../pages/ItemDetailPage'
import { LoginPage } from '../pages/LoginPage'
import { ManagerDashboardPage } from '../pages/ManagerDashboardPage'
import { MatchesPage } from '../pages/MatchesPage'
import { MyClaimsPage } from '../pages/MyClaimsPage'
import { MyQrPage } from '../pages/MyQrPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { NotificationsPage } from '../pages/NotificationsPage'
import { QrRecoveryPage } from '../pages/QrRecoveryPage'
import { RegisterPage } from '../pages/RegisterPage'
import { ReportPage } from '../pages/ReportPage'
import { StaffManagementPage } from '../pages/StaffManagementPage'
import { UnassignedReportsPage } from '../pages/UnassignedReportsPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
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
          { path: '/matches', element: <MatchesPage /> },
          { path: '/claims/new', element: <ClaimFormPage /> },
          { path: '/claims/mine', element: <MyClaimsPage /> },
          { path: '/claims', element: <ClaimsPage /> },
          { path: '/qr', element: <MyQrPage /> },
          { path: '/dashboard', element: <ManagerDashboardPage /> },
          { path: '/staff', element: <StaffManagementPage /> },
          { path: '/inspections', element: <InspectionsPage /> },
          { path: '/custody', element: <CustodyPage /> },
          { path: '/audit-logs', element: <AuditLogsPage /> },
          { path: '/analytics', element: <AnalyticsPage /> },
          { path: '/admin/unassigned', element: <UnassignedReportsPage /> },
          { path: '/notifications', element: <NotificationsPage /> },
        ],
      },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [{ path: '/recover/:token', element: <QrRecoveryPage /> }],
  },
  { path: '*', element: <NotFoundPage /> },
])
