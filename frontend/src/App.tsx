import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Events from './pages/Events';
import EventDetail from './pages/EventDetail';
import Approvals from './pages/Approvals';
import Devices from './pages/Devices';
import DeviceDetail from './pages/DeviceDetail';
import Policies from './pages/Policies';
import PolicyDetail from './pages/PolicyDetail';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';
import SystemHealth from './pages/SystemHealth';
import Enforcement from './pages/Enforcement';
import Audit from './pages/Audit';
import Settings from './pages/Settings';

/**
 * SentinelX application root with routing.
 */
export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            {/* Protected Routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/events" element={<Events />} />
                <Route path="/events/:id" element={<EventDetail />} />
                <Route path="/approvals" element={<Approvals />} />
                <Route path="/devices" element={<Devices />} />
                <Route path="/devices/:id" element={<DeviceDetail />} />
                <Route path="/policies" element={<Policies />} />
                <Route path="/policies/:id" element={<PolicyDetail />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/system-health" element={<SystemHealth />} />
                <Route path="/enforcement" element={<Enforcement />} />
                <Route path="/audit" element={<Audit />} />
                <Route path="/settings" element={<Settings />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}
