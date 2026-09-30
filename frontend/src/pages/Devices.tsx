import React, { useEffect, useState } from 'react';
import { Laptop, Search, Monitor, Terminal, ShieldX, Server, CheckCircle2, ChevronLeft, ChevronRight } from 'lucide-react';
import { devicesApi } from '../services/api';
import type { Device, PaginatedResponse } from '../types';

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'ONLINE':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-900/30 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/30"><CheckCircle2 size={12} /> Online</span>;
    case 'OFFLINE':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-800 px-2.5 py-0.5 text-xs font-medium text-gray-400 border border-gray-600"><Monitor size={12} /> Offline</span>;
    case 'DISABLED':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-red-900/30 px-2.5 py-0.5 text-xs font-medium text-red-400 border border-red-500/30"><ShieldX size={12} /> Disabled</span>;
    default:
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-700 px-2.5 py-0.5 text-xs font-medium text-gray-300">Unknown</span>;
  }
};

const Devices: React.FC = () => {
  const [data, setData] = useState<PaginatedResponse<Device> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const size = 20;

  useEffect(() => {
    const fetchDevices = async () => {
      setLoading(true);
      try {
        const response = await devicesApi.list({ page, size });
        setData(response);
      } catch (err) {
        console.error('Failed to fetch devices', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDevices();
  }, [page]);

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Laptop className="text-cyan-400" />
          Managed Devices
        </h2>
        
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input 
              type="text" 
              placeholder="Search devices..." 
              className="w-full sm:w-64 rounded-md border border-gray-600 bg-gray-700/50 py-1.5 pl-9 pr-3 text-sm text-white placeholder-gray-400 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-colors"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {loading && !data ? (
          <div className="col-span-full py-12 flex justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent"></div>
          </div>
        ) : data?.items.length === 0 ? (
          <div className="col-span-full py-12 text-center text-gray-500 bg-gray-800 rounded-xl border border-gray-700">
            No devices registered.
          </div>
        ) : (
          data?.items.map((device) => (
            <div key={device.id} className="rounded-xl border border-gray-700 bg-gray-800 p-5 shadow-lg flex flex-col hover:border-cyan-900/50 transition-colors">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-gray-700 p-2 text-cyan-400">
                    <Server size={20} />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white truncate w-32" title={device.device_name}>
                      {device.device_name}
                    </h3>
                    <p className="text-xs text-gray-500 font-mono truncate w-32" title={device.device_id}>
                      {device.device_id.substring(0, 12)}...
                    </p>
                  </div>
                </div>
                <div>{getStatusBadge(device.status)}</div>
              </div>
              
              <div className="space-y-3 flex-1">
                <div className="flex items-center gap-2 text-sm">
                  <Terminal size={14} className="text-gray-500 shrink-0" />
                  <span className="text-gray-300 truncate" title={device.operating_system || 'Unknown OS'}>
                    {device.operating_system || 'Unknown OS'} {device.os_version && `(${device.os_version})`}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Monitor size={14} className="text-gray-500 shrink-0" />
                  <span className="text-gray-300 truncate" title={device.hostname || 'Unknown Host'}>
                    {device.hostname || 'Unknown Host'}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mt-4 pt-4 border-t border-gray-700/50">
                  Last seen: {device.last_seen_at ? new Date(device.last_seen_at).toLocaleString() : 'Never'}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between border border-gray-700 rounded-xl bg-gray-800 px-4 py-3 shadow-lg">
          <span className="text-sm text-gray-400">
            Showing <span className="font-semibold text-white">{(data.page - 1) * data.size + 1}</span> to{' '}
            <span className="font-semibold text-white">
              {Math.min(data.page * data.size, data.total)}
            </span>{' '}
            of <span className="font-semibold text-white">{data.total}</span> devices
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="flex items-center justify-center rounded-md border border-gray-600 bg-gray-900 p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page === data.pages}
              className="flex items-center justify-center rounded-md border border-gray-600 bg-gray-900 p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Devices;
