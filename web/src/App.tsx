import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom'

import EventsPage from './pages/EventsPage'
import DashboardPage from './pages/DashboardPage'
import SettingsPage from './pages/SettingsPage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import BillingPage from './pages/BillingPage'
import UsagePage from './pages/UsagePage'
import TracesPage from './pages/TracesPage'
import TraceView from './pages/TraceView'
import AlertsPage from './pages/AlertsPage'
import PromptsPage from './pages/PromptsPage'
import PromptDetailPage from './pages/PromptDetailPage'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { ProjectProvider } from './hooks/useProject'
import ProjectSelector from './components/ProjectSelector'

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

const Layout = ({ children }: { children: React.ReactNode }) => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-8">
            <span className="text-xl font-bold text-indigo-600">WatchLLM</span>
            <div className="flex gap-4 text-sm font-medium text-gray-600">
              <Link to="/" className="hover:text-indigo-600">Dashboard</Link>
              <Link to="/events" className="hover:text-indigo-600">Events</Link>
              <Link to="/traces" className="hover:text-indigo-600">Traces</Link>
              <Link to="/prompts" className="hover:text-indigo-600">Prompts</Link>
              <Link to="/alerts" className="hover:text-indigo-600">Alerts</Link>
              <Link to="/usage" className="hover:text-indigo-600">Usage</Link>
              <Link to="/settings" className="hover:text-indigo-600">Settings</Link>
              <Link to="/billing" className="hover:text-indigo-600">Billing</Link>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <ProjectSelector />
            <span className="text-sm text-gray-500">{user?.email}</span>
            <button
              onClick={() => logout()}
              className="text-sm text-gray-500 hover:text-red-600"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto">
        {children}
      </main>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Layout><DashboardPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/events" element={
        <ProtectedRoute>
          <Layout><EventsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/traces" element={
        <ProtectedRoute>
          <Layout><TracesPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/traces/:traceId" element={
        <ProtectedRoute>
          <Layout><TraceView /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/alerts" element={
        <ProtectedRoute>
          <Layout><AlertsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/prompts" element={
        <ProtectedRoute>
          <Layout><PromptsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/prompts/:promptName" element={
        <ProtectedRoute>
          <Layout><PromptDetailPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute>
          <Layout><SettingsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/billing" element={
        <ProtectedRoute>
          <Layout><BillingPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/usage" element={
        <ProtectedRoute>
          <Layout><UsagePage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <ProjectProvider>
        <Router>
          <AppRoutes />
        </Router>
      </ProjectProvider>
    </AuthProvider>
  );
}

export default App