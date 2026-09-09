import axios from 'axios';

/**
 * Configured Axios instance for SentinelX backend API.
 * Base URL is set via VITE_API_BASE_URL environment variable.
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/** Health check response from the backend. */
export interface HealthResponse {
  status: 'ok' | 'degraded';
  service: string;
  version: string;
  database: 'healthy' | 'unhealthy';
  timestamp: string;
}

/**
 * Fetch the backend health status.
 */
export async function getHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/api/v1/health');
  return response.data;
}

export default apiClient;
