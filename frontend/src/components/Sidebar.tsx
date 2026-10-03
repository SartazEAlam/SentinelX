import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  CheckCircle2,
  Laptop,
  ScrollText,
  Bell,
  TrendingUp,
  HeartPulse,
  Shield,
  History,
  Settings,
  type LucideIcon,
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
}

const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/events', label: 'Events', icon: Activity },
  { path: '/approvals', label: 'Approvals', icon: CheckCircle2 },
  { path: '/devices', label: 'Devices', icon: Laptop },
  { path: '/policies', label: 'Policies', icon: ScrollText },
  { path: '/alerts', label: 'Alerts', icon: Bell },
  { path: '/analytics', label: 'Analytics', icon: TrendingUp },
  { path: '/enforcement', label: 'Enforcement', icon: Shield },
  { path: '/audit', label: 'Audit Log', icon: History },
  { path: '/system-health', label: 'System Health', icon: HeartPulse },
  { path: '/settings', label: 'Settings', icon: Settings },
];

/**
 * Sidebar navigation with links to all application routes.
 * Active route is highlighted with a distinct accent.
 */
export default function Sidebar() {
  return (
    <aside className="sidebar" id="main-sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <img src="/favicon.svg" alt="SentinelX Logo" className="brand-img" />
        </div>
        <div className="brand-text">
          <span className="brand-name">SentinelX</span>
          <span className="brand-subtitle">DLP System</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'nav-item-active' : ''}`
              }
            >
              <span className="nav-icon">
                <Icon size={18} />
              </span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-version">v0.1.0 — Phase 7</div>
      </div>
    </aside>
  );
}
