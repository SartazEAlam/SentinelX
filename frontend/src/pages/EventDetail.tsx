import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { eventsApi, riskApi } from '../services/api';
import type { SecurityEvent, RiskAssessment } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import { ArrowLeft, FileText, Server, Activity, ArrowRight, ShieldCheck, ShieldAlert } from 'lucide-react';

export default function EventDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [event, setEvent] = useState<SecurityEvent | null>(null);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchEventData = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const eventData = await eventsApi.get(id);
        setEvent(eventData);

        // Try to fetch associated risk assessment
        try {
          const riskList = await riskApi.listAssessments({ event_id: id });
          if (riskList.items && riskList.items.length > 0) {
            const fullAssessment = await riskApi.getAssessment(riskList.items[0].id);
            setRiskAssessment(fullAssessment);
          }
        } catch (rErr) {
          console.warn('No risk assessment found or failed to fetch', rErr);
        }

      } catch (err) {
        console.error('Failed to fetch event', err);
        setError('Failed to load event details.');
      } finally {
        setLoading(false);
      }
    };
    fetchEventData();
  }, [id]);

  if (loading) return <LoadingSpinner message="Loading event details..." />;
  if (error || !event) return <div className="p-8 text-center text-red-500">{error || 'Event not found'}</div>;

  return (
    <div className="flex h-full flex-col p-8 overflow-y-auto space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/events')}
          className="rounded-full p-2 text-gray-400 hover:bg-gray-800 hover:text-white"
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            Event Investigation
          </h2>
          <p className="text-sm text-gray-400 font-mono mt-1">ID: {event.event_id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Information */}
        <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl">
          <h3 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
            <Server size={18} className="text-blue-400" />
            Basic Information
          </h3>
          <div className="space-y-4 text-sm text-gray-300">
            <div className="flex justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">Timestamp</span>
              <span>{new Date(event.timestamp).toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">Device</span>
              <span className="font-mono text-blue-400">{event.device_id}</span>
            </div>
            <div className="flex justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">User Context</span>
              <span>{event.user_context || 'Unknown'}</span>
            </div>
            <div className="flex justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">Operation</span>
              <span className="font-mono text-amber-400">{event.action || event.event_type}</span>
            </div>
            <div className="flex justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">Source</span>
              <span className="font-mono text-xs break-all text-right ml-4">{event.source || 'N/A'}</span>
            </div>
            <div className="flex justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">Destination</span>
              <span className="font-mono text-xs break-all text-right ml-4">{event.destination || 'N/A'}</span>
            </div>
            <div className="flex justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">File Type</span>
              <span>{event.file_name ? event.file_name.split('.').pop()?.toUpperCase() : 'N/A'}</span>
            </div>
            <div className="flex justify-between border-b border-gray-800 pb-2">
              <span className="text-gray-500">File Size</span>
              <span>{event.file_size ? `${(event.file_size / 1024).toFixed(2)} KB` : 'N/A'}</span>
            </div>
            {event.file_hash && (
              <div className="flex justify-between pb-2">
                <span className="text-gray-500">File Hash</span>
                <span className="font-mono text-xs text-gray-500">{event.file_hash}</span>
              </div>
            )}
          </div>
        </div>

        {/* Classification */}
        <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl">
          <h3 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
            <FileText size={18} className="text-purple-400" />
            Classification
          </h3>
          {event.classification ? (
            <div className="space-y-4 text-sm text-gray-300">
              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-500">Sensitivity</span>
                <span className={`font-semibold ${
                  event.classification.sensitivity_level === 'CRITICAL' ? 'text-red-500' :
                  event.classification.sensitivity_level === 'HIGH' ? 'text-amber-500' :
                  event.classification.sensitivity_level === 'MEDIUM' ? 'text-yellow-500' :
                  'text-emerald-500'
                }`}>
                  {event.classification.sensitivity_level}
                </span>
              </div>
              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-500">Detected Categories</span>
                <div className="flex gap-1 flex-wrap justify-end">
                  {event.classification.categories.map((cat, i) => (
                    <span key={i} className="bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded text-xs">
                      {cat}
                    </span>
                  ))}
                  {event.classification.categories.length === 0 && 'None'}
                </div>
              </div>
              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-500">Confidence</span>
                <span>{(event.classification.confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between pb-2">
                <span className="text-gray-500">Classifier Info</span>
                <span className="text-gray-500 text-xs">
                  {event.classification.classifier_version} ({event.classification.model_name || 'Rules'})
                </span>
              </div>
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center text-gray-500">
              No classification data available for this event.
            </div>
          )}
        </div>

        {/* Risk & Policy */}
        <div className="rounded-xl border border-gray-700 bg-gray-900/50 p-6 shadow-xl lg:col-span-2">
          <h3 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
            <Activity size={18} className="text-amber-400" />
            Risk & Policy Explainability
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <div className="mb-4 flex items-end gap-3">
                <div className="text-4xl font-bold text-white">{event.risk_score?.toFixed(1) || '0.0'}</div>
                <div className="text-sm text-gray-500 mb-1">Total Risk Score</div>
              </div>
              
              {riskAssessment ? (
                <div className="space-y-3 mt-6">
                  <h4 className="text-sm font-medium text-gray-400">Contributing Factors</h4>
                  {riskAssessment.factors.map((factor, idx) => (
                    <div key={idx} className="flex justify-between text-sm items-center border-b border-gray-800 pb-2">
                      <span className="text-gray-300">{factor.name}</span>
                      <span className="text-amber-400 font-mono">+{factor.contribution.toFixed(1)}</span>
                    </div>
                  ))}
                  <div className="mt-4 pt-4 text-sm text-gray-400 italic">
                    {riskAssessment.explanation}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500 mt-6">
                  Detailed risk factors are not available.
                </div>
              )}
            </div>

            <div className="border-l border-gray-700 pl-8">
              <h4 className="text-sm font-medium text-gray-400 mb-4">Policy Enforcement</h4>
              
              <div className="space-y-4 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Requested Operation</span>
                  <span className="font-mono text-gray-300">{event.action}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Policy Triggered</span>
                  <span className="text-cyan-400">{riskAssessment?.policy_name || 'Default Strategy'}</span>
                </div>
                
                <div className="mt-8 flex items-center justify-center gap-4 bg-gray-800/50 p-6 rounded-lg border border-gray-700">
                  <div className="text-center">
                    <div className="text-gray-500 text-xs mb-2">Intent</div>
                    <div className="font-mono text-gray-300">{event.action}</div>
                  </div>
                  <ArrowRight className="text-gray-600" />
                  <div className="text-center">
                    <div className="text-gray-500 text-xs mb-2">Decision</div>
                    <div className={`font-bold px-3 py-1 rounded flex items-center gap-2 ${
                      event.decision === 'BLOCK' ? 'bg-red-500/20 text-red-500' :
                      event.decision === 'HOLD' ? 'bg-amber-500/20 text-amber-500' :
                      'bg-emerald-500/20 text-emerald-500'
                    }`}>
                      {event.decision === 'BLOCK' ? <ShieldAlert size={16} /> : <ShieldCheck size={16} />}
                      {event.decision}
                    </div>
                  </div>
                </div>

                <div className="mt-4 text-xs text-gray-500 text-center">
                  Final State: {event.status || 'PROCESSED'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
