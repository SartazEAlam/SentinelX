import { Outlet } from 'react-router-dom';
import { LogOut, User } from 'lucide-react';
import Sidebar from './Sidebar';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';

/**
 * Main application layout with sidebar navigation and content area.
 * The header bar shows the current application status and user.
 */
export default function Layout() {
  const { user, logout } = useAuth();
  const { isConnected } = useWebSocket();

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
            <span className="header-status mr-4">
              <span className={isConnected ? 'status-dot-live' : 'h-2 w-2 rounded-full bg-red-500 mr-2'} />
              {isConnected ? 'System Active' : 'Disconnected'}
            </span>
            <div className="flex items-center gap-4 border-l border-gray-700 pl-4">
              <div className="flex items-center gap-2 text-sm text-gray-300">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-900/50 text-cyan-400">
                  <User size={16} />
                </div>
                <div className="hidden flex-col md:flex">
                  <span className="font-medium text-white">{user?.username}</span>
                  <span className="text-xs text-gray-500">{user?.role}</span>
                </div>
              </div>
              <button
                onClick={logout}
                className="rounded-md p-2 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
                title="Logout"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </header>
        <main className="page-content" id="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
