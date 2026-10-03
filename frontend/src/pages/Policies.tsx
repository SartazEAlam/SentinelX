import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ScrollText, Plus, Shield, ShieldAlert, Clock, ShieldCheck, Settings } from 'lucide-react';
import { policiesApi } from '../services/api';
import type { Policy, PaginatedResponse } from '../types';

const Policies: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<PaginatedResponse<Policy> | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchPolicies = async () => {
    setLoading(true);
    try {
      const response = await policiesApi.list({ size: 100 });
      setData(response);
    } catch (err) {
      console.error('Failed to fetch policies', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleToggle = async (id: number, currentStatus: boolean) => {
    try {
      if (currentStatus) {
        await policiesApi.disable(id);
      } else {
        await policiesApi.enable(id);
      }
      fetchPolicies();
    } catch (err) {
      console.error('Failed to toggle policy', err);
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'BLOCK': return <ShieldAlert size={16} className="text-red-400" />;
      case 'ALLOW': return <ShieldCheck size={16} className="text-emerald-400" />;
      case 'HOLD': return <Clock size={16} className="text-amber-400" />;
      default: return <Shield size={16} className="text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <ScrollText className="text-cyan-400" />
          Security Policies
        </h2>
        
        <button className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-900/20">
          <Plus size={18} />
          Create Policy
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 xl:grid-cols-3">
        {loading && !data ? (
          <div className="col-span-full py-12 flex justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent"></div>
          </div>
        ) : data?.items.length === 0 ? (
          <div className="col-span-full py-12 text-center text-gray-500 bg-gray-800 rounded-xl border border-gray-700">
            No policies defined.
          </div>
        ) : (
          data?.items.map((policy) => (
            <div 
              key={policy.id} 
              className={`rounded-xl border ${policy.is_active ? 'border-cyan-900/50 shadow-cyan-900/10' : 'border-gray-700'} bg-gray-800 p-5 shadow-lg flex flex-col transition-all cursor-pointer hover:border-cyan-700`}
              onClick={() => navigate(`/policies/${policy.id}`)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`rounded-lg p-2 ${policy.is_active ? 'bg-cyan-900/30 text-cyan-400' : 'bg-gray-700 text-gray-400'}`}>
                    <Shield size={20} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{policy.name}</h3>
                    <p className="text-xs text-gray-500">v{policy.version} • Priority: {policy.priority}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleToggle(policy.id, policy.is_active)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${
                    policy.is_active ? 'bg-cyan-500' : 'bg-gray-600'
                  }`}
                  role="switch"
                  aria-checked={policy.is_active}
                >
                  <span
                    aria-hidden="true"
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      policy.is_active ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
              
              <p className="text-sm text-gray-400 mb-6 flex-1 line-clamp-3">
                {policy.description || 'No description provided.'}
              </p>
              
              <div className="space-y-3 pt-4 border-t border-gray-700/50">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Action</span>
                  <div className="flex items-center gap-1.5 font-medium text-gray-200">
                    {getActionIcon(policy.action)}
                    {policy.action}
                  </div>
                </div>
                
                {(policy.risk_min !== null || policy.risk_max !== null) && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Risk Threshold</span>
                    <span className="font-medium text-gray-200">
                      {policy.risk_min ?? 0} - {policy.risk_max ?? 100}
                    </span>
                  </div>
                )}
                
                {policy.sensitivity_levels && policy.sensitivity_levels.length > 0 && (
                  <div className="flex items-start justify-between text-sm">
                    <span className="text-gray-500 mt-0.5">Sensitivity</span>
                    <div className="flex flex-wrap justify-end gap-1 max-w-[60%]">
                      {policy.sensitivity_levels.map(level => (
                        <span key={level} className="rounded bg-gray-700 px-1.5 py-0.5 text-[10px] uppercase font-semibold text-gray-300 tracking-wider">
                          {level.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-6 flex justify-end">
                <button 
                  className="flex items-center gap-1.5 text-xs font-medium text-gray-400 hover:text-white transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/policies/${policy.id}`);
                  }}
                >
                  <Settings size={14} />
                  Configure
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Policies;
