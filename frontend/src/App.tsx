import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Events from './pages/Events';
import Approvals from './pages/Approvals';
import Devices from './pages/Devices';
import Policies from './pages/Policies';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';
import SystemHealth from './pages/SystemHealth';

/**
 * SentinelX application root with routing.
 */
export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/events" element={<Events />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/devices" element={<Devices />} />
            <Route path="/policies" element={<Policies />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/system-health" element={<SystemHealth />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
