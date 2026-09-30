import React, { useEffect, useState } from 'react';
import { TrendingUp, Activity, Shield, AlertTriangle, ShieldCheck, Clock, ShieldAlert } from 'lucide-react';
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts';
import { dashboardApi } from '../services/api';
import type { RiskDistribution, SensitivityDistribution, EnforcementStats } from '../types';

const COLORS = {
  // Risk
  low: '#10b981',    // emerald-500
  medium: '#f59e0b', // amber-500
  high: '#ef4444',   // red-500
  
  // Sensitivity
  public: '#94a3b8',              // slate-400
  internal: '#3b82f6',            // blue-500
  confidential: '#8b5cf6',        // violet-500
  highly_confidential: '#ec4899', // pink-500
  unknown: '#4b5563',             // gray-600
  
  // Enforcement
  allowed: '#10b981', // emerald-500
  held: '#f59e0b',    // amber-500
  blocked: '#ef4444', // red-500
  approved: '#0ea5e9',// sky-500
  denied: '#f43f5e',  // rose-500
};

const Analytics: React.FC = () => {
  const [riskData, setRiskData] = useState<RiskDistribution | null>(null);
  const [sensitivityData, setSensitivityData] = useState<SensitivityDistribution | null>(null);
  const [enforcementData, setEnforcementData] = useState<EnforcementStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        const [risk, sensitivity, enforcement] = await Promise.all([
          dashboardApi.riskDistribution(timeRange),
          dashboardApi.sensitivityDistribution(),
          dashboardApi.enforcementStats(),
        ]);
        setRiskData(risk);
        setSensitivityData(sensitivity);
        setEnforcementData(enforcement);
      } catch (err) {
        console.error('Failed to fetch analytics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [timeRange]);

  // Format data for Recharts Pie
  const riskPieData = riskData ? [
    { name: 'Low', value: riskData.low, fill: COLORS.low },
    { name: 'Medium', value: riskData.medium, fill: COLORS.medium },
    { name: 'High', value: riskData.high, fill: COLORS.high },
  ].filter(d => d.value > 0) : [];

  const sensitivityPieData = sensitivityData ? [
    { name: 'Public', value: sensitivityData.public, fill: COLORS.public },
    { name: 'Internal', value: sensitivityData.internal, fill: COLORS.internal },
    { name: 'Confidential', value: sensitivityData.confidential, fill: COLORS.confidential },
    { name: 'Highly Confidential', value: sensitivityData.highly_confidential, fill: COLORS.highly_confidential },
    { name: 'Unknown', value: sensitivityData.unknown, fill: COLORS.unknown },
  ].filter(d => d.value > 0) : [];

  const enforcementBarData = enforcementData ? [
    { name: 'Allowed', count: enforcementData.allowed, fill: COLORS.allowed },
    { name: 'Blocked', count: enforcementData.blocked, fill: COLORS.blocked },
    { name: 'Held', count: enforcementData.held, fill: COLORS.held },
    { name: 'Approved', count: enforcementData.approved, fill: COLORS.approved },
    { name: 'Denied', count: enforcementData.denied, fill: COLORS.denied },
  ].filter(d => d.count > 0) : [];

  return (
    <div className="space-y-6 flex flex-col min-h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <TrendingUp className="text-cyan-400" />
          Security Analytics
        </h2>
        
        <div className="flex items-center gap-4">
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="rounded-md border border-gray-600 bg-gray-800 py-1.5 pl-3 pr-8 text-sm font-medium text-white shadow-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex-1 flex justify-center items-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Risk Distribution */}
          <div className="rounded-xl bg-gray-800 p-6 shadow-lg border border-gray-700/50 flex flex-col h-[400px]">
            <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
              <AlertTriangle size={18} className="text-amber-400" />
              Risk Distribution
            </h3>
            <p className="text-sm text-gray-400 mb-6">Distribution of events by assessed risk level.</p>
            
            {riskPieData.length > 0 ? (
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={riskPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {riskPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} stroke="transparent" />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#f3f4f6' }}
                      itemStyle={{ color: '#fff' }}
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                No risk data available for this period.
              </div>
            )}
          </div>

          {/* Sensitivity Classification */}
          <div className="rounded-xl bg-gray-800 p-6 shadow-lg border border-gray-700/50 flex flex-col h-[400px]">
            <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
              <Shield size={18} className="text-violet-400" />
              Data Sensitivity Classification
            </h3>
            <p className="text-sm text-gray-400 mb-6">Breakdown of content by highest sensitivity level detected.</p>
            
            {sensitivityPieData.length > 0 ? (
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={sensitivityPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {sensitivityPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} stroke="transparent" />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#f3f4f6' }}
                      itemStyle={{ color: '#fff' }}
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                No classification data available.
              </div>
            )}
          </div>

          {/* Enforcement Outcomes */}
          <div className="rounded-xl bg-gray-800 p-6 shadow-lg border border-gray-700/50 lg:col-span-2 flex flex-col h-[400px]">
            <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
              <Activity size={18} className="text-cyan-400" />
              Enforcement Outcomes
            </h3>
            <p className="text-sm text-gray-400 mb-6">Results of policy evaluation and subsequent actions taken.</p>
            
            {enforcementBarData.length > 0 ? (
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={enforcementBarData}
                    margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
                    layout="vertical"
                  >
                    <XAxis type="number" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} width={100} />
                    <Tooltip 
                      cursor={{ fill: '#1f2937' }}
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#f3f4f6' }}
                      itemStyle={{ color: '#fff' }}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {enforcementBarData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                No enforcement data available.
              </div>
            )}
            
            {/* Quick Stats Row below bar chart */}
            {enforcementData && (
              <div className="mt-6 grid grid-cols-3 gap-4 border-t border-gray-700 pt-6">
                <div className="text-center">
                  <div className="flex justify-center mb-1"><ShieldCheck size={20} className="text-emerald-400" /></div>
                  <p className="text-xl font-bold text-emerald-400">{enforcementData.allowed}</p>
                  <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Allowed</p>
                </div>
                <div className="text-center">
                  <div className="flex justify-center mb-1"><Clock size={20} className="text-amber-400" /></div>
                  <p className="text-xl font-bold text-amber-400">{enforcementData.held}</p>
                  <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Held for Review</p>
                </div>
                <div className="text-center">
                  <div className="flex justify-center mb-1"><ShieldAlert size={20} className="text-red-400" /></div>
                  <p className="text-xl font-bold text-red-400">{enforcementData.blocked}</p>
                  <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Blocked</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
