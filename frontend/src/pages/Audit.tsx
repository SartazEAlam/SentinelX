import { useEffect, useState } from 'react';
import { History, Search, User, Monitor, ChevronLeft, ChevronRight } from 'lucide-react';
import { auditApi } from '../services/api';
import type { AuditLog, PaginatedResponse } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Audit() {
  const [data, setData] = useState<PaginatedResponse<AuditLog> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const size = 20;

  useEffect(() => {
    const fetchAuditLogs = async () => {
      try {
        setLoading(true);
        const response = await auditApi.list({ page, size });
        setData(response);
      } catch (err) {
        console.error('Failed to fetch audit logs', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAuditLogs();
  }, [page]);

  return (
    <div className="space-y-6 flex flex-col h-full p-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <History className="text-cyan-400" />
          Audit Logs
        </h2>
        
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input 
              type="text" 
              placeholder="Search audit trail..." 
              className="w-full sm:w-64 rounded-md border border-gray-600 bg-gray-700/50 py-1.5 pl-9 pr-3 text-sm text-white placeholder-gray-400 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-colors"
            />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-xl border border-gray-700 bg-gray-800 shadow-xl flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm text-gray-400">
            <thead className="sticky top-0 bg-gray-900/95 text-xs uppercase text-gray-300 backdrop-blur border-b border-gray-700">
              <tr>
                <th scope="col" className="px-4 py-3">Timestamp</th>
                <th scope="col" className="px-4 py-3">Action</th>
                <th scope="col" className="px-4 py-3">Actor</th>
                <th scope="col" className="px-4 py-3">Resource</th>
                <th scope="col" className="px-4 py-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading && !data ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center">
                    <LoadingSpinner />
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-gray-500">
                    No audit logs found.
                  </td>
                </tr>
              ) : (
                data?.items.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-700/50 transition-colors">
                    <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-300">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : (log.created_at ? new Date(log.created_at).toLocaleString() : '-')}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded bg-blue-900/30 border border-blue-500/30 px-2 py-0.5 text-xs font-medium text-blue-400">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        {log.actor_user_id && (
                          <span className="flex items-center gap-1 text-gray-300"><User size={12}/> User {log.actor_user_id}</span>
                        )}
                        {log.actor_device_id && (
                          <span className="flex items-center gap-1 text-gray-400 text-xs"><Monitor size={10}/> {log.actor_device_id}</span>
                        )}
                        {!log.actor_user_id && !log.actor_device_id && 'System'}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-gray-300">{log.resource_type || '-'}</div>
                      <div className="text-xs text-gray-500 font-mono">{log.resource_id || ''}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-gray-500 break-words line-clamp-2" title={log.metadata_json || ''}>
                        {log.metadata_json || '-'}
                      </span>
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
              of <span className="font-semibold text-white">{data.total}</span> entries
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
}
