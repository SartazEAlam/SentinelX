import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

/**
 * Main application layout with sidebar navigation and content area.
 * The header bar shows the current application status.
 */
export default function Layout() {
  return (
    <div className="app-layout" id="app-layout">
      <Sidebar />
      <div className="main-content">
        <header className="top-header" id="top-header">
          <div className="header-left">
            <h1 className="header-title">SentinelX</h1>
            <span className="header-env-badge">DEVELOPMENT</span>
          </div>
          <div className="header-right">
            <span className="header-status">
              <span className="status-dot-live" />
              System Active
            </span>
          </div>
        </header>
        <main className="page-content" id="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
