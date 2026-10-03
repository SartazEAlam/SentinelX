import { useEffect, useState } from 'react';
import { Shield, ShieldAlert, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';
import { enforcementApi } from '../services/api';
import type { EnforcementResult } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';

const getDecisionIcon = (decision: string) => {
  switch (decision) {
    case 'BLOCK': return <ShieldAlert size={16} className="text-red-400" />;
    case 'ALLOW': return <CheckCircle2 size={16} className="text-emerald-400" />;
    case 'HOLD': return <Clock size={16} className="text-amber-400" />;
    default: return <AlertTriangle size={16} className="text-gray-400" />;
  }
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'COMPLETED':
      return <span className="bg-emerald-900/30 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-xs">Completed</span>;
    case 'FAILED':
      return <span className="bg-red-900/30 text-red-400 border border-red-500/30 px-2 py-0.5 rounded text-xs">Failed</span>;
    case 'PENDING':
      return <span className="bg-amber-900/30 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded text-xs">Pending</span>;
    default:
      return <span className="bg-gray-800 text-gray-400 border border-gray-600 px-2 py-0.5 rounded text-xs">{status}</span>;
  }
};

export default function Enforcement() {
  const [results, setResults] = useState<EnforcementResult[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        const data = await enforcementApi.list({ limit: 100 });
        setResults(data);
      } catch (err) {
        console.error('Failed to fetch enforcement results', err);
        setError('Failed to load enforcement timeline.');
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, []);

  if (loading) return <LoadingSpinner message="Loading enforcement history..." />;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="flex h-full flex-col p-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Shield className="text-cyan-400" />
            Enforcement History
          </h2>
          <p className="text-sm text-gray-400 mt-1">Timeline of endpoint enforcement actions</p>
        </div>
      </div>

      <div className="flex-1 overflow-auto rounded-xl border border-gray-700 bg-gray-900 shadow-xl p-4">
        {results?.length === 0 ? (
          <div className="py-12 text-center text-gray-500">No enforcement actions recorded.</div>
        ) : (
          <div className="space-y-4">
            {results?.map((result) => (
              <div key={result.id} className="relative pl-6 pb-6 border-l border-gray-800 last:border-0 last:pb-0">
                <div className="absolute left-[-9px] top-1 h-4 w-4 rounded-full bg-gray-900 border border-gray-700 flex items-center justify-center">
                  <div className={`h-2 w-2 rounded-full ${
                    result.decision === 'BLOCK' ? 'bg-red-500' :
                    result.decision === 'ALLOW' ? 'bg-emerald-500' :
                    result.decision === 'HOLD' ? 'bg-amber-500' : 'bg-gray-500'
                  }`} />
                </div>
                
                <div className="rounded-lg border border-gray-700/50 bg-gray-800/50 p-4 hover:bg-gray-800 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-3">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1.5 font-bold text-gray-200">
                        {getDecisionIcon(result.decision)}
                        {result.decision}
                      </div>
                      <span className="text-gray-500 text-sm">
                        {new Date(result.completed_at).toLocaleString()}
                      </span>
                    </div>
                    <div>
                      {getStatusBadge(result.status)}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-300">
                    <div className="space-y-2">
                      <div className="flex justify-between border-b border-gray-700/50 pb-1">
                        <span className="text-gray-500">Operation ID</span>
                        <span className="font-mono text-cyan-400">{result.operation_id.split('-')[0]}...</span>
                      </div>
                      <div className="flex justify-between border-b border-gray-700/50 pb-1">
                        <span className="text-gray-500">Bytes</span>
                        <span>{result.bytes_transferred} B</span>
                      </div>
                      {result.reason_code && (
                        <div className="flex justify-between border-b border-gray-700/50 pb-1">
                          <span className="text-gray-500">Reason Code</span>
                          <span className="font-mono">{result.reason_code}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      {result.message && (
                        <div className="bg-black/30 p-2 rounded text-xs font-mono text-gray-400 border border-gray-800">
                          {result.message}
                        </div>
                      )}
                      {result.error_code && (
                        <div className="flex justify-between text-red-400">
                          <span>Error Code</span>
                          <span className="font-mono">{result.error_code}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
