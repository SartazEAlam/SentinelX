import React, { useEffect, useState, useCallback } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Laptop,
  ShieldAlert,
  TrendingUp,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { dashboardApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { OverviewStats, WSMessage } from '../types';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchStats = async () => {
    try {
      const data = await dashboardApi.overview();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch dashboard stats', err);
      setError('Failed to load dashboard statistics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // 1-minute fallback polling
    return () => clearInterval(interval);
  }, []);

  const handleWsMessage = useCallback((msg: WSMessage) => {
    // If a new event comes in, refresh the stats
    if (msg.type === 'SECURITY_EVENT' || msg.type === 'HIGH_RISK_ALERT') {
      fetchStats();
    }
  }, []);

  useWebSocket({ onMessage: handleWsMessage });

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-cyan-400 flex flex-col items-center">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent"></div>
          <p className="mt-4 text-sm font-medium">Loading intelligence...</p>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="rounded-lg bg-red-900/20 p-4 border border-red-500/30 text-red-400">
        <div className="flex items-center gap-2">
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  // Format data for charts
  const trendData = stats.events_trend.map((point) => {
    const d = new Date(point.timestamp);
    return {
      time: `${d.getHours().toString().padStart(2, '0')}:00`,
      events: point.count,
    };
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white tracking-tight">Security Center Overview</h2>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Activity size={16} className="text-cyan-400" />
          <span>Live Updates Active</span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl bg-gray-800 p-5 shadow-lg border border-gray-700/50">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-cyan-900/50 p-3 text-cyan-400">
              <Laptop size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-400">Active Devices</p>
              <p className="text-2xl font-bold text-white">
                {stats.active_devices} <span className="text-sm font-normal text-gray-500">/ {stats.total_devices}</span>
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-gray-800 p-5 shadow-lg border border-gray-700/50">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-blue-900/50 p-3 text-blue-400">
              <TrendingUp size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-400">Events (24h)</p>
              <p className="text-2xl font-bold text-white">{stats.total_events_24h}</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-gray-800 p-5 shadow-lg border border-red-900/50 relative overflow-hidden">
          <div className="absolute top-0 right-0 h-16 w-16 -mr-8 -mt-8 rounded-full bg-red-500/10 blur-xl"></div>
          <div className="flex items-center gap-4 relative z-10">
            <div className="rounded-lg bg-red-900/50 p-3 text-red-400">
              <ShieldAlert size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-400">Critical Alerts</p>
              <p className="text-2xl font-bold text-white">{stats.critical_alerts}</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-gray-800 p-5 shadow-lg border border-amber-900/50 relative overflow-hidden">
          <div className="absolute top-0 right-0 h-16 w-16 -mr-8 -mt-8 rounded-full bg-amber-500/10 blur-xl"></div>
          <div className="flex items-center gap-4 relative z-10">
            <div className="rounded-lg bg-amber-900/50 p-3 text-amber-400">
              <CheckCircle2 size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-400">Pending Approvals</p>
              <p className="text-2xl font-bold text-white">{stats.pending_approvals}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Event Trend Chart */}
        <div className="rounded-xl bg-gray-800 p-5 shadow-lg border border-gray-700/50 lg:col-span-2">
          <h3 className="mb-4 text-lg font-semibold text-white">Event Volume (24h)</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis 
                  dataKey="time" 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(val) => (val === 0 ? '' : val)}
                />
                <Tooltip
                  cursor={{ fill: '#1f2937' }}
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem' }}
                  itemStyle={{ color: '#22d3ee' }}
                />
                <Bar dataKey="events" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Violators */}
        <div className="rounded-xl bg-gray-800 p-5 shadow-lg border border-gray-700/50">
          <h3 className="mb-4 text-lg font-semibold text-white">Top Devices by Event Volume</h3>
          <div className="space-y-4">
            {stats.top_violators.length === 0 ? (
              <div className="flex h-[200px] items-center justify-center text-sm text-gray-500">
                No events recorded.
              </div>
            ) : (
              stats.top_violators.map((v, i) => (
                <div key={v.device_id} className="flex items-center justify-between border-b border-gray-700/50 pb-3 last:border-0 last:pb-0">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-700 text-xs font-bold text-gray-300">
                      #{i + 1}
                    </div>
                    <div className="truncate">
                      <p className="truncate text-sm font-medium text-gray-200" title={v.device_name}>
                        {v.device_name}
                      </p>
                      <p className="truncate text-xs text-gray-500" title={v.device_id}>
                        {v.device_id.substring(0, 8)}...
                      </p>
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <span className="inline-flex items-center rounded-md bg-gray-700 px-2.5 py-0.5 text-sm font-medium text-cyan-400">
                      {v.event_count}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
