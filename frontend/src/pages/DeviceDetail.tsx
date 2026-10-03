import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { devicesApi, eventsApi } from '../services/api';
import type { Device, SecurityEvent, PaginatedResponse } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import { ArrowLeft, Monitor, Activity, ShieldAlert, Clock, Info } from 'lucide-react';

export default function DeviceDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [device, setDevice] = useState<Device | null>(null);
  const [events, setEvents] = useState<PaginatedResponse<SecurityEvent> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDeviceData = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const deviceData = await devicesApi.get(id);
        setDevice(deviceData);

        // Fetch recent events for this device
        try {
          const eventsData = await eventsApi.list({ device_id: id, size: 50 });
          setEvents(eventsData);
        } catch (eErr) {
          console.warn('Failed to fetch events for device', eErr);
        }

      } catch (err) {
        console.error('Failed to fetch device', err);
        setError('Failed to load device details.');
      } finally {
        setLoading(false);
      }
    };
    fetchDeviceData();
  }, [id]);

  if (loading) return <LoadingSpinner message="Loading device details..." />;
  if (error || !device) return <div className="p-8 text-center text-red-500">{error || 'Device not found'}</div>;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ONLINE':
        return <span className="rounded bg-emerald-500/20 px-2 py-1 text-xs font-medium text-emerald-500">ONLINE</span>;
      case 'OFFLINE':
        return <span className="rounded bg-gray-500/20 px-2 py-1 text-xs font-medium text-gray-400">OFFLINE</span>;
      default:
        return <span className="rounded bg-amber-500/20 px-2 py-1 text-xs font-medium text-amber-500">{status}</span>;
    }
  };

  const highRiskEvents = events?.items.filter(e => (e.risk_score || 0) >= 70) || [];
  const blockedEvents = events?.items.filter(e => e.decision === 'BLOCK') || [];

  return (
    <div className="flex h-full flex-col p-8 overflow-y-auto space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/devices')}
          className="rounded-full p-2 text-gray-400 hover:bg-gray-800 hover:text-white"
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            Device Information
          </h2>
          <p className="text-sm text-gray-400 mt-1">{device.device_name} ({device.device_id})</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Device Profile */}
        <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl lg:col-span-1 h-fit">
          <h3 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
            <Monitor size={18} className="text-blue-400" />
            Profile
          </h3>
          <div className="space-y-4 text-sm text-gray-300">
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">Status</span>
              {getStatusBadge(device.status)}
            </div>
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">IP Address</span>
              <span className="font-mono">{device.ip_address || 'Unknown'}</span>
            </div>
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">OS</span>
              <span>{device.operating_system} {device.os_version}</span>
            </div>
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">Agent Version</span>
              <span>v{device.agent_version}</span>
            </div>
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">Registered</span>
              <span>{new Date(device.registered_at).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">Last Seen</span>
              <span>{device.last_seen_at ? new Date(device.last_seen_at).toLocaleString() : 'Never'}</span>
            </div>
          </div>
        </div>

        {/* Security Summary */}
        <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl lg:col-span-2">
          <h3 className="mb-6 text-lg font-semibold text-white flex items-center gap-2">
            <ShieldAlert size={18} className="text-amber-400" />
            Security Overview (Last 50 Events)
          </h3>
          
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 text-center">
              <div className="text-3xl font-bold text-white mb-1">{events?.total || 0}</div>
              <div className="text-xs text-gray-400 uppercase">Total Events</div>
            </div>
            <div className="bg-red-900/20 rounded-lg p-4 border border-red-900/30 text-center">
              <div className="text-3xl font-bold text-red-500 mb-1">{highRiskEvents.length}</div>
              <div className="text-xs text-gray-400 uppercase">High Risk</div>
            </div>
            <div className="bg-amber-900/20 rounded-lg p-4 border border-amber-900/30 text-center">
              <div className="text-3xl font-bold text-amber-500 mb-1">{blockedEvents.length}</div>
              <div className="text-xs text-gray-400 uppercase">Blocked Operations</div>
            </div>
          </div>

          <h4 className="text-sm font-medium text-gray-400 mb-4 flex items-center gap-2">
            <Activity size={16} />
            Recent Activity
          </h4>

          {events && events.items.length > 0 ? (
            <div className="space-y-3">
              {events.items.slice(0, 5).map(evt => (
                <div key={evt.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded border border-gray-700/50 cursor-pointer hover:bg-gray-800"
                     onClick={() => navigate(`/events/${evt.event_id}`)}>
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      evt.risk_score && evt.risk_score >= 70 ? 'bg-red-500' :
                      evt.risk_score && evt.risk_score >= 40 ? 'bg-amber-500' : 'bg-emerald-500'
                    }`} />
                    <div>
                      <div className="text-sm font-medium text-gray-200">{evt.action || evt.event_type}</div>
                      <div className="text-xs text-gray-500 font-mono mt-0.5">{evt.file_name || evt.destination || 'System Event'}</div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      evt.decision === 'BLOCK' ? 'bg-red-500/20 text-red-500' :
                      evt.decision === 'HOLD' ? 'bg-amber-500/20 text-amber-500' : 'bg-emerald-500/20 text-emerald-500'
                    }`}>
                      {evt.decision}
                    </span>
                    <span className="flex items-center gap-1 text-[10px] text-gray-500">
                      <Clock size={10} />
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-gray-500 text-sm flex flex-col items-center">
              <Info size={24} className="mb-2 text-gray-600" />
              No recent security activity found for this device.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
