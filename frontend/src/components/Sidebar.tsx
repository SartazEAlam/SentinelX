import { NavLink } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/events', label: 'Events', icon: '📋' },
  { path: '/approvals', label: 'Approvals', icon: '✅' },
  { path: '/devices', label: 'Devices', icon: '💻' },
  { path: '/policies', label: 'Policies', icon: '📜' },
  { path: '/alerts', label: 'Alerts', icon: '🔔' },
  { path: '/analytics', label: 'Analytics', icon: '📈' },
  { path: '/system-health', label: 'System Health', icon: '🩺' },
];

/**
 * Sidebar navigation with links to all application routes.
 * Active route is highlighted with a distinct accent.
 */
export default function Sidebar() {
  return (
    <aside className="sidebar" id="main-sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">🛡</div>
        <div className="brand-text">
          <span className="brand-name">SentinelX</span>
          <span className="brand-subtitle">DLP System</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'nav-item-active' : ''}`
            }
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-version">v0.1.0 — Phase 0</div>
      </div>
    </aside>
  );
}
