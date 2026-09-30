/** Core TypeScript types for the SentinelX Dashboard. */

// ── Auth ────────────────────────────────────────────────────────────────────

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserMe {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: 'ADMIN' | 'SECURITY_ANALYST' | 'VIEWER';
}

// ── Paginated ───────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ── Dashboard ───────────────────────────────────────────────────────────────

export interface DashboardSummary {
  connected_devices: number;
  events_today: number;
  high_risk_events: number;
  blocked_operations: number;
  pending_approvals: number;
  active_alerts: number;
}

export interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
}

export interface SensitivityDistribution {
  public: number;
  internal: number;
  confidential: number;
  highly_confidential: number;
  unknown: number;
}

export interface EnforcementStats {
  allowed: number;
  held: number;
  blocked: number;
  approved: number;
  denied: number;
  expired: number;
  failed: number;
}

export interface EventTrend {
  timestamp: string;
  count: number;
}

export interface OverviewStats {
  total_devices: number;
  active_devices: number;
  total_events_24h: number;
  critical_alerts: number;
  pending_approvals: number;
  events_trend: EventTrend[];
  top_violators: Array<{ device_id: string; device_name: string; event_count: number }>;
}

// ── Events ──────────────────────────────────────────────────────────────────

export interface ClassificationResponse {
  id: number;
  event_id: string;
  sensitivity_level: string;
  confidence: number;
  categories: string[];
  evidence: Array<Record<string, unknown>>;
  content_inspected: boolean;
  inspection_complete: boolean;
  classifier_version: string;
  model_name: string | null;
  model_version: string | null;
  classified_at: string | null;
}

export interface SecurityEvent {
  id: number;
  event_id: string;
  device_id: string;
  timestamp: string;
  event_type: string;
  action: string | null;
  source: string | null;
  destination: string | null;
  file_name: string | null;
  file_path: string | null;
  file_size: number | null;
  file_hash: string | null;
  sensitivity_level: string | null;
  risk_score: number | null;
  decision: string | null;
  status: string | null;
  user_context: string | null;
  process_name: string | null;
  process_id: number | null;
  metadata_json: unknown;
  created_at: string;
  classification: ClassificationResponse | null;
}

// ── Devices ─────────────────────────────────────────────────────────────────

export interface Device {
  id: number;
  device_id: string;
  device_name: string;
  hostname: string | null;
  operating_system: string | null;
  os_version: string | null;
  agent_version: string | null;
  ip_address: string | null;
  status: 'ONLINE' | 'OFFLINE' | 'UNKNOWN' | 'DISABLED';
  last_seen_at: string | null;
  registered_at: string;
  updated_at: string;
  is_active: boolean;
}

// ── Approvals ───────────────────────────────────────────────────────────────

export interface Approval {
  id: number;
  request_id: string;
  event_id: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'CANCELLED';
  reason: string | null;
  reviewer_comment: string | null;
  created_at: string;
  reviewed_at: string | null;
  risk_assessment_id: number | null;
  requested_action: string | null;
  expires_at: string | null;
  policy_id: number | null;
  policy_version: number | null;
  requester: UserResponse | null;
  reviewer: UserResponse | null;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: string;
}

// ── Alerts ──────────────────────────────────────────────────────────────────

export interface Alert {
  id: number;
  alert_id: string;
  event_id: number | null;
  device_id: string | null;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  message: string | null;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  acknowledger: UserResponse | null;
  resolver: UserResponse | null;
}

// ── Risk ────────────────────────────────────────────────────────────────────

export interface RiskFactor {
  name: string;
  score: number;
  weight: number;
  contribution: number;
  reason: string;
}

export interface RiskAssessment {
  id: number;
  risk_assessment_id: number;
  event_id: string;
  risk_score: number;
  risk_level: string;
  decision: string;
  policy_id: number | null;
  policy_name: string | null;
  factors: RiskFactor[];
  explanation: string;
  risk_engine_version: string;
  policy_engine_version: string;
  risk_config_version: string;
  created_at: string;
}

export interface RiskAssessmentListItem {
  id: number;
  event_id: string;
  risk_score: number;
  risk_level: string;
  decision: string;
  policy_name: string | null;
  created_at: string;
}

// ── Enforcement ─────────────────────────────────────────────────────────────

export interface EnforcementResult {
  id: number;
  operation_id: string;
  status: string;
  decision: string;
  started_at: string | null;
  completed_at: string;
  source_hash: string | null;
  destination_hash: string | null;
  bytes_transferred: number;
  reason_code: string | null;
  error_code: string | null;
  message: string | null;
}

// ── Policies ────────────────────────────────────────────────────────────────

export interface Policy {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  priority: number;
  action: string;
  version: number;
  conditions_json: string | null;
  risk_min: number | null;
  risk_max: number | null;
  sensitivity_levels: string[] | null;
  allowed_actions: string[] | null;
  allowed_destinations: string[] | null;
  created_at: string;
  updated_at: string;
  created_by: number | null;
  updated_by: number | null;
}

// ── Audit ───────────────────────────────────────────────────────────────────

export interface AuditLog {
  id: number;
  action: string;
  actor_user_id: number | null;
  actor_device_id: string | null;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  metadata_json: string | null;
  created_at: string;
}

// ── WebSocket ───────────────────────────────────────────────────────────────

export interface WSMessage {
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

// ── Health ───────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: 'ok' | 'degraded';
  service: string;
  version: string;
  database: 'healthy' | 'unhealthy';
  timestamp: string;
}
