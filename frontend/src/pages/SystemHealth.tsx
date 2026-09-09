import { useEffect, useState } from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';
import { getHealth, type HealthResponse } from '../services/apiClient';
import StatusIndicator from '../components/StatusIndicator';
import LoadingSpinner from '../components/LoadingSpinner';

/**
 * System Health page — calls the real backend health endpoint
 * and displays live system status.
 */
export default function SystemHealth() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<string>('');

  const executeHealthCheck = async (showLoading = false) => {
    if (showLoading) {
      setLoading(true);
    }
    setError(null);
    try {
      const data = await getHealth();
      setHealth(data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to connect to backend';
      setError(message);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;

    const loadInitialHealth = async () => {
      try {
        const data = await getHealth();
        if (isMounted) {
          setHealth(data);
          setError(null);
          setLastChecked(new Date().toLocaleTimeString());
        }
      } catch (err: unknown) {
        if (isMounted) {
          const message = err instanceof Error ? err.message : 'Failed to connect to backend';
          setError(message);
          setHealth(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    void loadInitialHealth();
    const interval = setInterval(() => {
      void executeHealthCheck(false);
    }, 30000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="system-health-page">
      <div className="page-header">
        <h2>System Health</h2>
        <button
          onClick={() => void executeHealthCheck(true)}
          className="btn-primary"
          id="refresh-health-btn"
          disabled={loading}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={15} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {loading && !health && <LoadingSpinner message="Checking backend health..." />}

      {error && (
        <div className="health-card health-card-error">
          <div className="health-card-icon">
            <AlertOctagon size={40} className="text-red-400" />
          </div>
          <h3>Backend Unreachable</h3>
          <p>{error}</p>
          <p className="health-hint">
            Make sure the backend is running: <code>uvicorn app.main:app --reload</code>
          </p>
        </div>
      )}

      {health && (
        <div className="health-grid">
          <div className="health-card">
            <div className="health-card-header">
              <span className="health-card-title">Service Status</span>
              <StatusIndicator status={health.status} label={health.status.toUpperCase()} />
            </div>
            <div className="health-card-body">
              <div className="health-detail">
                <span className="health-label">Service</span>
                <span className="health-value">{health.service}</span>
              </div>
              <div className="health-detail">
                <span className="health-label">Version</span>
                <span className="health-value">{health.version}</span>
              </div>
              <div className="health-detail">
                <span className="health-label">Timestamp</span>
                <span className="health-value">{new Date(health.timestamp).toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="health-card">
            <div className="health-card-header">
              <span className="health-card-title">Database</span>
              <StatusIndicator
                status={health.database === 'healthy' ? 'ok' : 'degraded'}
                label={health.database.toUpperCase()}
              />
            </div>
            <div className="health-card-body">
              <div className="health-detail">
                <span className="health-label">Status</span>
                <span className="health-value">{health.database}</span>
              </div>
            </div>
          </div>

          <div className="health-card">
            <div className="health-card-header">
              <span className="health-card-title">Connection</span>
              <StatusIndicator status="ok" label="CONNECTED" />
            </div>
            <div className="health-card-body">
              <div className="health-detail">
                <span className="health-label">API Base</span>
                <span className="health-value">{import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}</span>
              </div>
              <div className="health-detail">
                <span className="health-label">Last Checked</span>
                <span className="health-value">{lastChecked}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
