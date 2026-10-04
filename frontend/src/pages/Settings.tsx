import { Settings as SettingsIcon, Shield, Bell, User, Database } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="flex h-full flex-col p-8 overflow-y-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <SettingsIcon className="text-cyan-400" />
          Settings
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Settings */}
        <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl space-y-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <User size={18} className="text-blue-400" />
            Profile Settings
          </h3>
          <div className="space-y-4 text-sm">
            <div>
              <label className="block text-gray-400 mb-1">Username</label>
              <input type="text" disabled value={user?.username || ''} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-500 cursor-not-allowed" />
            </div>
            <div>
              <label className="block text-gray-400 mb-1">Full Name</label>
              <input type="text" defaultValue={user?.full_name || ''} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
            </div>
            <div>
              <label className="block text-gray-400 mb-1">Email</label>
              <input type="email" defaultValue={user?.email || ''} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500" />
            </div>
            <button className="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded text-sm font-medium transition-colors">
              Update Profile
            </button>
          </div>
        </div>

        {/* Notification Preferences */}
        <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl space-y-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Bell size={18} className="text-amber-400" />
            Notifications
          </h3>
          <div className="space-y-4 text-sm text-gray-300">
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="form-checkbox h-4 w-4 text-cyan-500 bg-gray-800 border-gray-600 rounded focus:ring-cyan-500 focus:ring-offset-gray-900" />
              <span>Email alerts for CRITICAL severity events</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="form-checkbox h-4 w-4 text-cyan-500 bg-gray-800 border-gray-600 rounded focus:ring-cyan-500 focus:ring-offset-gray-900" />
              <span>Email alerts for pending approvals</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" className="form-checkbox h-4 w-4 text-cyan-500 bg-gray-800 border-gray-600 rounded focus:ring-cyan-500 focus:ring-offset-gray-900" />
              <span>Daily digest of security events</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="form-checkbox h-4 w-4 text-cyan-500 bg-gray-800 border-gray-600 rounded focus:ring-cyan-500 focus:ring-offset-gray-900" />
              <span>Browser notifications for active alerts</span>
            </label>
            <button className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors mt-4">
              Save Preferences
            </button>
          </div>
        </div>

        {/* System Settings */}
        {user?.role === 'ADMIN' && (
          <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl space-y-6 lg:col-span-1">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Database size={18} className="text-purple-400" />
              System Administration
            </h3>
            <div className="space-y-4 text-sm">
              <div>
                <label className="block text-gray-400 mb-1">Data Retention Period (Days)</label>
                <input type="number" defaultValue={90} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Default Risk Threshold for Block</label>
                <input type="number" defaultValue={70} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500" />
              </div>
              <div className="pt-4 border-t border-gray-800">
                <button className="bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 border border-purple-500/30 px-4 py-2 rounded text-sm font-medium transition-colors w-full flex items-center justify-center gap-2">
                  <Shield size={16} />
                  Force Reload Policies
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
