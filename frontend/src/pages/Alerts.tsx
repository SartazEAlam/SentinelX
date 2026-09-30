import React, { useEffect, useState } from 'react';
import { Bell, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { alertsApi } from '../services/api';
import type { Alert, PaginatedResponse } from '../types';

const getSeverityStyles = (severity: string) => {
  switch (severity) {
    case 'CRITICAL':
      return 'bg-red-900/30 text-red-400 border border-red-500/30';
    case 'HIGH':
      return 'bg-orange-900/30 text-orange-400 border border-orange-500/30';
    case 'MEDIUM':
      return 'bg-amber-900/30 text-amber-400 border border-amber-500/30';
    case 'LOW':
      return 'bg-blue-900/30 text-blue-400 border border-blue-500/30';
    default:
      return 'bg-gray-800 text-gray-400 border border-gray-600';
  }
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'OPEN':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-red-900/30 px-2 py-0.5 text-xs font-medium text-red-400"><AlertTriangle size={12} /> Open</span>;
    case 'ACKNOWLEDGED':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-900/30 px-2 py-0.5 text-xs font-medium text-amber-400"><Info size={12} /> Acknowledged</span>;
    case 'RESOLVED':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-900/30 px-2 py-0.5 text-xs font-medium text-emerald-400"><CheckCircle size={12} /> Resolved</span>;
    default:
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-700 px-2 py-0.5 text-xs font-medium text-gray-300">{status}</span>;
  }
};

const Alerts: React.FC = () => {
  const [data, setData] = useState<PaginatedResponse<Alert> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState<'OPEN' | 'ALL'>('OPEN');
  const size = 20;

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, size };
      if (activeTab === 'OPEN') {
        params.status = 'OPEN';
      }
      const response = await alertsApi.list(params);
      setData(response);
    } catch (err) {
      console.error('Failed to fetch alerts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [page, activeTab]);

  const handleAction = async (id: number, action: 'acknowledge' | 'resolve') => {
    try {
      if (action === 'acknowledge') {
        await alertsApi.acknowledge(id);
      } else {
        await alertsApi.resolve(id);
      }
      fetchAlerts();
    } catch (err) {
      console.error(`Failed to ${action} alert`, err);
    }
  };

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Bell className="text-cyan-400" />
          Security Alerts
        </h2>
        
        <div className="flex items-center gap-4">
          <div className="flex rounded-lg bg-gray-800 p-1 border border-gray-700">
            <button
              onClick={() => { setActiveTab('OPEN'); setPage(1); }}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                activeTab === 'OPEN'
                  ? 'bg-gray-700 text-white shadow-sm'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Open
            </button>
            <button
              onClick={() => { setActiveTab('ALL'); setPage(1); }}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                activeTab === 'ALL'
                  ? 'bg-gray-700 text-white shadow-sm'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              All Alerts
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-xl border border-gray-700 bg-gray-800 shadow-xl flex flex-col">
        {loading && !data ? (
          <div className="flex-1 flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent"></div>
          </div>
        ) : data?.items.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center py-12 text-center">
            <div className="rounded-full bg-gray-700/50 p-4 mb-4 text-gray-500">
              <Bell size={32} />
            </div>
            <p className="text-lg font-medium text-gray-300">No {activeTab.toLowerCase()} alerts.</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1 p-4 space-y-3">
            {data?.items.map((alert) => (
              <div key={alert.id} className="rounded-lg border border-gray-700 bg-gray-900/50 p-4 transition-colors hover:border-gray-600 flex flex-col sm:flex-row gap-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${getSeverityStyles(alert.severity)}`}>
                      {alert.severity}
                    </span>
                    <h3 className="font-semibold text-white">{alert.title}</h3>
                    <div className="ml-auto flex items-center gap-3">
                      {getStatusBadge(alert.status)}
                      <span className="text-xs text-gray-500">
                        {new Date(alert.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400">{alert.message || 'No description provided.'}</p>
                </div>
                
                {alert.status !== 'RESOLVED' && (
                  <div className="flex sm:flex-col gap-2 shrink-0 border-t sm:border-t-0 sm:border-l border-gray-700 pt-3 sm:pt-0 sm:pl-4 justify-center">
                    {alert.status === 'OPEN' && (
                      <button
                        onClick={() => handleAction(alert.id, 'acknowledge')}
                        className="rounded bg-gray-800 px-3 py-1 text-sm font-medium text-gray-300 hover:bg-gray-700 transition-colors"
                      >
                        Acknowledge
                      </button>
                    )}
                    <button
                      onClick={() => handleAction(alert.id, 'resolve')}
                      className="rounded bg-emerald-600/20 px-3 py-1 text-sm font-medium text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30 transition-colors"
                    >
                      Resolve
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Alerts;
