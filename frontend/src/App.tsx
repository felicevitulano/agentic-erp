import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Layout from './components/layout/Layout'
import LoginPage from './components/layout/LoginPage'
import DashboardPage from './components/dashboard/DashboardPage'
import PipelinePage from './components/sales/PipelinePage'
import ContactsPage from './components/sales/ContactsPage'
import ContractsPage from './components/sales/ContractsPage'
import FatturePage from './components/finance/FatturePage'
import ScadenzarioPage from './components/finance/ScadenzarioPage'
import CashFlowPage from './components/finance/CashFlowPage'
import CollaboratoriPage from './components/hr/CollaboratoriPage'
import ProgettiPage from './components/operations/ProgettiPage'
import CalendarioPage from './components/marketing/CalendarioPage'
import AuditLogPage from './components/audit/AuditLogPage'

export default function App() {
  const { user, loading, login, logout, isAuthenticated } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-gray-500 mt-4 text-sm">Caricamento...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated || !user) {
    return <LoginPage onLogin={login} />
  }

  return (
    <Routes>
      <Route element={<Layout user={user} onLogout={logout} />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/sales" element={<PipelinePage />} />
        <Route path="/contacts" element={<ContactsPage />} />
        <Route path="/contracts" element={<ContractsPage />} />
        <Route path="/finance" element={<FatturePage />} />
        <Route path="/scadenzario" element={<ScadenzarioPage />} />
        <Route path="/cash-flow" element={<CashFlowPage />} />
        <Route path="/hr" element={<CollaboratoriPage />} />
        <Route path="/operations" element={<ProgettiPage />} />
        <Route path="/marketing" element={<CalendarioPage />} />
        <Route path="/audit" element={<AuditLogPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
