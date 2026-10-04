import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { policiesApi } from '../services/api';
import type { Policy } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import { ArrowLeft, ShieldCheck, Tag, Target, Clock, ShieldX } from 'lucide-react';

export default function PolicyDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPolicyData = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const policyData = await policiesApi.get(parseInt(id, 10));
        setPolicy(policyData);
      } catch (err) {
        console.error('Failed to fetch policy', err);
        setError('Failed to load policy details.');
      } finally {
        setLoading(false);
      }
    };
    fetchPolicyData();
  }, [id]);

  if (loading) return <LoadingSpinner message="Loading policy details..." />;
  if (error || !policy) return <div className="p-8 text-center text-red-500">{error || 'Policy not found'}</div>;

  return (
    <div className="flex h-full flex-col p-8 overflow-y-auto space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/policies')}
          className="rounded-full p-2 text-gray-400 hover:bg-gray-800 hover:text-white"
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            Policy Details
          </h2>
          <p className="text-sm text-gray-400 mt-1">{policy.name} (v{policy.version})</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl lg:col-span-1 space-y-6 h-fit">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">General Info</h3>
            <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border ${
              policy.is_active 
                ? 'bg-emerald-900/30 text-emerald-400 border-emerald-500/30'
                : 'bg-red-900/30 text-red-400 border-red-500/30'
            }`}>
              {policy.is_active ? <><ShieldCheck size={12} /> Active</> : <><ShieldX size={12} /> Inactive</>}
            </span>
          </div>

          <p className="text-sm text-gray-300 italic">{policy.description || 'No description provided.'}</p>

          <div className="space-y-3 text-sm border-t border-gray-800 pt-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-500 flex items-center gap-2"><Target size={16} /> Action</span>
              <span className="font-mono text-amber-400">{policy.action}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500 flex items-center gap-2"><Tag size={16} /> Priority</span>
              <span>{policy.priority}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500 flex items-center gap-2"><Clock size={16} /> Updated At</span>
              <span>{new Date(policy.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl lg:col-span-2 space-y-6">
          <h3 className="text-lg font-semibold text-white">Policy Criteria</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Risk Threshold</h4>
              <div className="text-2xl font-bold text-white">
                {policy.risk_min !== null ? policy.risk_min : '0'} 
                <span className="text-gray-500 font-normal mx-2">-</span> 
                {policy.risk_max !== null ? policy.risk_max : '100'}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Target Sensitivities</h4>
              <div className="flex flex-wrap gap-2">
                {policy.sensitivity_levels && policy.sensitivity_levels.length > 0 ? (
                  policy.sensitivity_levels.map(level => (
                    <span key={level} className="bg-purple-900/30 text-purple-400 border border-purple-500/30 px-2 py-0.5 rounded text-xs">
                      {level}
                    </span>
                  ))
                ) : (
                  <span className="text-gray-500 text-sm">Any</span>
                )}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Target Actions</h4>
              <div className="flex flex-wrap gap-2">
                {policy.allowed_actions && policy.allowed_actions.length > 0 ? (
                  policy.allowed_actions.map(action => (
                    <span key={action} className="bg-blue-900/30 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded text-xs font-mono">
                      {action}
                    </span>
                  ))
                ) : (
                  <span className="text-gray-500 text-sm">Any</span>
                )}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Allowed Destinations</h4>
              <div className="flex flex-wrap gap-2">
                {policy.allowed_destinations && policy.allowed_destinations.length > 0 ? (
                  policy.allowed_destinations.map(dest => (
                    <span key={dest} className="bg-gray-700 text-gray-300 border border-gray-600 px-2 py-0.5 rounded text-xs font-mono">
                      {dest}
                    </span>
                  ))
                ) : (
                  <span className="text-gray-500 text-sm">Any</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="mt-4">
            <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Advanced Conditions (JSON)</h4>
            <div className="bg-black/50 p-4 rounded-lg border border-gray-800 overflow-x-auto">
              <pre className="text-xs text-gray-400 font-mono">
                {policy.conditions_json 
                  ? JSON.stringify(JSON.parse(policy.conditions_json), null, 2) 
                  : '{}'}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
