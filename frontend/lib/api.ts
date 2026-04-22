import { createClient as createSupabaseClient } from "./supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthHeaders(): Promise<Record<string, string>> {
  const supabase = createSupabaseClient();
  const { data: { session } } = await supabase.auth.getSession();
  return {
    "Content-Type": "application/json",
    ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
  };
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await getAuthHeaders();
  const url = endpoint.startsWith("http") ? endpoint : `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message || `API Error: ${response.status}`);
  }

  return response.json();
}

// Alert types
export interface Alert {
  id: string;
  org_id: string;
  severity: "critical" | "high" | "medium" | "low";
  type: string;
  title: string;
  description: string;
  status: "open" | "resolved";
  remediation_hint?: string;
  created_at: string;
  resolved_at?: string;
}

// Scan types
export interface ScanResult {
  id: string;
  org_id: string;
  target: string;
  status: "pending" | "running" | "completed" | "failed";
  started_at: string;
  completed_at?: string;
}

export interface PortResult {
  port: number;
  status: "open" | "closed" | "filtered";
  risk_level: "high" | "medium" | "low";
  service?: string;
  description: string;
}

// API functions
export const api = {
  // Alerts
  getAlerts: (orgId: string) =>
    apiFetch<Alert[]>(`/api/v1/alerts?org_id=${orgId}`),
  getAlert: (id: string) =>
    apiFetch<Alert>(`/api/v1/alerts/${id}`),
  resolveAlert: (id: string) =>
    apiFetch<Alert>(`/api/v1/alerts/${id}/resolve`, { method: "PATCH" }),

  // Scans
  getScans: (orgId: string) =>
    apiFetch<ScanResult[]>(`/api/v1/scans?org_id=${orgId}`),
  startScan: (orgId: string, target: string) =>
    apiFetch<ScanResult>(`/api/v1/scans/${orgId}/run`, {
      method: "POST",
      body: JSON.stringify({ target }),
    }),
  getScanResults: (scanId: string) =>
    apiFetch<PortResult[]>(`/api/v1/scans/${scanId}/results`),

  // Reports
  getReports: (orgId: string) =>
    apiFetch<Report[]>(`/api/v1/reports?org_id=${orgId}`),
  generateReport: (orgId: string, type: "SOC2" | "GDPR" | "ISO27001") =>
    apiFetch<Report>(`/api/v1/reports/${orgId}/generate`, {
      method: "POST",
      body: JSON.stringify({ type }),
    }),
  getReport: (id: string) =>
    apiFetch<Report>(`/api/v1/reports/${id}`),

  // Settings
  getOrg: (orgId: string) =>
    apiFetch<Org>(`/api/v1/orgs/${orgId}`),
  updateOrg: (orgId: string, data: Partial<Org>) =>
    apiFetch<Org>(`/api/v1/orgs/${orgId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};

export interface Report {
  id: string;
  org_id: string;
  type: "SOC2" | "GDPR" | "ISO27001";
  status: "pending" | "generating" | "completed" | "failed";
  created_at: string;
  completed_at?: string;
  content?: ReportContent;
}

export interface ReportContent {
  summary: string;
  sections: { title: string; content: string }[];
  generated_at: string;
}

export interface Org {
  id: string;
  name: string;
  plan: "starter" | "pro" | "enterprise";
  api_key?: string;
  endpoints: Endpoint[];
  notification_channels: NotificationChannel[];
}

export interface Endpoint {
  id: string;
  url: string;
  name: string;
  status: "connected" | "disconnected";
  last_seen: string;
}

export interface NotificationChannel {
  id: string;
  type: "email" | "slack";
  value: string;
  enabled: boolean;
}