import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Search, Filter, ShieldAlert, Shield, ShieldCheck, Clock, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import { eventsApi } from '../services/api';
import type { SecurityEvent, PaginatedResponse } from '../types';

const getRiskColor = (score: number | null) => {
  if (score === null) return 'text-gray-400 bg-gray-800';
  if (score >= 70) return 'text-red-400 bg-red-900/30 border border-red-500/30';
  if (score >= 30) return 'text-amber-400 bg-amber-900/30 border border-amber-500/30';
  return 'text-emerald-400 bg-emerald-900/30 border border-emerald-500/30';
};

const getDecisionBadge = (decision: string | null) => {
  if (!decision) return <span className="text-gray-500">-</span>;
  
  switch (decision) {
    case 'BLOCK':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-red-900/30 px-2 py-0.5 text-xs font-medium text-red-400 border border-red-500/30"><ShieldAlert size={12} /> Blocked</span>;
    case 'HOLD':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-900/30 px-2 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/30"><Clock size={12} /> Held</span>;
    case 'ALLOW':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-900/30 px-2 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/30"><ShieldCheck size={12} /> Allowed</span>;
    default:
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-700 px-2 py-0.5 text-xs font-medium text-gray-300"><Shield size={12} /> {decision}</span>;
  }
};

const Events: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<PaginatedResponse<SecurityEvent> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const size = 20;

  useEffect(() => {
    const fetchEvents = async () => {
      setLoading(true);
      try {
        const response = await eventsApi.list({ page, size });
        setData(response);
      } catch (err) {
        console.error('Failed to fetch events', err);
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, [page]);

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Activity className="text-cyan-400" />
          Security Events
        </h2>
        
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input 
              type="text" 
              placeholder="Search events..." 
              className="w-full sm:w-64 rounded-md border border-gray-600 bg-gray-700/50 py-1.5 pl-9 pr-3 text-sm text-white placeholder-gray-400 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-colors"
            />
          </div>
          <button className="flex items-center gap-2 rounded-md border border-gray-600 bg-gray-800 px-3 py-1.5 text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition-colors">
            <Filter size={16} />
            Filters
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-xl border border-gray-700 bg-gray-800 shadow-xl flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm text-gray-400">
            <thead className="sticky top-0 bg-gray-900/95 text-xs uppercase text-gray-300 backdrop-blur border-b border-gray-700">
              <tr>
                <th scope="col" className="px-4 py-3">Timestamp</th>
                <th scope="col" className="px-4 py-3">Event Type</th>
                <th scope="col" className="px-4 py-3">File / Asset</th>
                <th scope="col" className="px-4 py-3">User</th>
                <th scope="col" className="px-4 py-3">Risk</th>
                <th scope="col" className="px-4 py-3">Decision</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading && !data ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <div className="flex justify-center">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent"></div>
                    </div>
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-500">
                    No events found.
                  </td>
                </tr>
              ) : (
                data?.items.map((event) => (
                  <tr 
                    key={event.id} 
                    className="hover:bg-gray-700/50 transition-colors cursor-pointer"
                    onClick={() => navigate(`/events/${event.event_id}`)}
                  >
                    <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-300">
                      {new Date(event.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded bg-gray-700 px-2 py-0.5 text-xs font-medium text-gray-300">
                        {event.event_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 max-w-[200px] truncate">
                      <div className="flex items-center gap-2" title={event.file_path || event.file_name || 'N/A'}>
                        <FileText size={14} className="shrink-0 text-gray-500" />
                        <span className="truncate text-gray-200">{event.file_name || 'N/A'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-300">
                      {event.user_context || 'Unknown'}
                    </td>
                    <td className="px-4 py-3">
                      {event.risk_score !== null ? (
                        <span className={`inline-flex items-center justify-center rounded px-2 py-0.5 text-xs font-bold ${getRiskColor(event.risk_score)}`}>
                          {event.risk_score.toFixed(0)}
                        </span>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {getDecisionBadge(event.decision)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between border-t border-gray-700 bg-gray-900/50 px-4 py-3">
            <span className="text-sm text-gray-400">
              Showing <span className="font-semibold text-white">{(data.page - 1) * data.size + 1}</span> to{' '}
              <span className="font-semibold text-white">
                {Math.min(data.page * data.size, data.total)}
              </span>{' '}
              of <span className="font-semibold text-white">{data.total}</span> events
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center justify-center rounded-md border border-gray-600 bg-gray-800 p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="flex items-center justify-center rounded-md border border-gray-600 bg-gray-800 p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Events;
