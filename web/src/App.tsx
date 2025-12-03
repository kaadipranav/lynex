import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'

import EventsPage from './pages/EventsPage'
import DashboardPage from './pages/DashboardPage'

const Layout = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen bg-gray-50">
    <nav className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold text-indigo-600">SentryAI</span>
          <div className="flex gap-4 text-sm font-medium text-gray-600">
            <a href="/" className="hover:text-indigo-600">Dashboard</a>
            <a href="/events" className="hover:text-indigo-600">Events</a>
          </div>
        </div>
        <div className="text-sm text-gray-500">
          Project: Demo
        </div>
      </div>
    </nav>
    <main className="max-w-7xl mx-auto">
      {children}
    </main>
  </div>
)

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>