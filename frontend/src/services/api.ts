/** API service functions for all SentinelX endpoints. */

import apiClient from './apiClient';
import type {
  Alert,
  Approval,
  AuditLog,
  DashboardSummary,
  Device,
  EnforcementResult,
  EnforcementStats,
  HealthResponse,
  LoginRequest,
  OverviewStats,
  PaginatedResponse,
  Policy,
  RiskAssessment,
  RiskAssessmentListItem,
  RiskDistribution,
  SecurityEvent,
  SensitivityDistribution,
  TokenResponse,
  UserMe,
} from '../types';

// ── Auth ────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<TokenResponse>('/api/v1/auth/login', data).then((r) => r.data),

  me: () => apiClient.get<UserMe>('/api/v1/auth/me').then((r) => r.data),
};

// ── Dashboard ───────────────────────────────────────────────────────────────

export const dashboardApi = {
  summary: () =>
    apiClient.get<DashboardSummary>('/api/v1/dashboard/summary').then((r) => r.data),

  overview: () =>
    apiClient.get<OverviewStats>('/api/v1/dashboard/overview').then((r) => r.data),

  riskDistribution: (period = '24h') =>
    apiClient
      .get<RiskDistribution>('/api/v1/dashboard/risk-distribution', { params: { period } })
      .then((r) => r.data),

  sensitivityDistribution: () =>
    apiClient
      .get<SensitivityDistribution>('/api/v1/dashboard/sensitivity-distribution')
      .then((r) => r.data),

  enforcementStats: () =>
    apiClient.get<EnforcementStats>('/api/v1/dashboard/enforcement-stats').then((r) => r.data),
};

// ── Events ──────────────────────────────────────────────────────────────────

export const eventsApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiClient
      .get<PaginatedResponse<SecurityEvent>>('/api/v1/events', { params })
      .then((r) => r.data),

  get: (eventId: string) =>
    apiClient.get<SecurityEvent>(`/api/v1/events/${eventId}`).then((r) => r.data),
};

// ── Devices ─────────────────────────────────────────────────────────────────

export const devicesApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiClient
      .get<PaginatedResponse<Device>>('/api/v1/devices', { params })
      .then((r) => r.data),

  get: (deviceId: string) =>
    apiClient.get<Device>(`/api/v1/devices/${deviceId}`).then((r) => r.data),
};

// ── Approvals ───────────────────────────────────────────────────────────────

export const approvalsApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiClient
      .get<PaginatedResponse<Approval>>('/api/v1/approvals', { params })
      .then((r) => r.data),

  get: (id: number) =>
    apiClient.get<Approval>(`/api/v1/approvals/${id}`).then((r) => r.data),

  approve: (id: number, comment?: string) =>
    apiClient
      .post<Approval>(`/api/v1/approvals/${id}/approve`, { comment })
      .then((r) => r.data),

  reject: (id: number, comment?: string) =>
    apiClient
      .post<Approval>(`/api/v1/approvals/${id}/reject`, { comment })
      .then((r) => r.data),
};

// ── Alerts ──────────────────────────────────────────────────────────────────

export const alertsApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiClient
      .get<PaginatedResponse<Alert>>('/api/v1/alerts', { params })
      .then((r) => r.data),

  get: (id: number) =>
    apiClient.get<Alert>(`/api/v1/alerts/${id}`).then((r) => r.data),

  acknowledge: (id: number, comment?: string) =>
    apiClient
      .post<Alert>(`/api/v1/alerts/${id}/acknowledge`, { comment })
      .then((r) => r.data),

  resolve: (id: number, comment?: string) =>
    apiClient
      .post<Alert>(`/api/v1/alerts/${id}/resolve`, { comment })
      .then((r) => r.data),
};

// ── Risk ────────────────────────────────────────────────────────────────────

export const riskApi = {
  listAssessments: (params: Record<string, unknown> = {}) =>
    apiClient
      .get<PaginatedResponse<RiskAssessmentListItem>>('/api/v1/risk/assessments', { params })
      .then((r) => r.data),

  getAssessment: (id: number) =>
    apiClient.get<RiskAssessment>(`/api/v1/risk/assessments/${id}`).then((r) => r.data),
};

// ── Enforcement ─────────────────────────────────────────────────────────────

export const enforcementApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiClient
      .get<EnforcementResult[]>('/api/v1/enforcement/results', { params })
      .then((r) => r.data),
};

// ── Policies ────────────────────────────────────────────────────────────────

export const policiesApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiClient
      .get<PaginatedResponse<Policy>>('/api/v1/policies', { params })
      .then((r) => r.data),

  get: (id: number) =>
    apiClient.get<Policy>(`/api/v1/policies/${id}`).then((r) => r.data),

  enable: (id: number) =>
    apiClient.post<Policy>(`/api/v1/policies/${id}/enable`).then((r) => r.data),

  disable: (id: number) =>
    apiClient.post<Policy>(`/api/v1/policies/${id}/disable`).then((r) => r.data),
};

// ── Audit ───────────────────────────────────────────────────────────────────

export const auditApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiClient
      .get<PaginatedResponse<AuditLog>>('/api/v1/audit', { params })
      .then((r) => r.data),
};

// ── Health ───────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => apiClient.get<HealthResponse>('/api/v1/health').then((r) => r.data),
};
