import axios, { AxiosInstance } from 'axios';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface SecurityEvent {
  timestamp?: number;
  method: string;
  path: string;
  status_code: number;
  latency_ms: number;
  ip: string;
  user_agent: string;
  anomaly_score?: number;
  org_id?: string;
}

export interface Alert {
  id: string;
  org_id: string;
  event: SecurityEvent;
  score: number;
  resolved: boolean;
  created_at: string;
}

export interface PortResult {
  port: number;
  open: boolean;
  risk: 'HIGH' | 'MEDIUM' | 'LOW';
  service?: string;
}

export interface ScanResult {
  target: string;
  ports: PortResult[];
  scanned_at: number;
  org_id?: string;
}

export interface Report {
  id: string;
  org_id: string;
  type: 'soc2' | 'gdpr' | 'iso27001';
  status: 'pending' | 'generating' | 'ready' | 'failed';
  content?: string;
  created_at: string;
  ready_at?: string;
}

// ─── DWClient ────────────────────────────────────────────────────────────────

export class DWClient {
  private client: AxiosInstance;
  private orgId: string;

  constructor(options: { apiKey: string; orgId: string; baseUrl?: string }) {
    this.orgId = options.orgId;
    this.client = axios.create({
      baseURL: options.baseUrl ?? 'https://api.driftwatch.io',
      headers: {
        Authorization: `Bearer ${options.apiKey}`,
        'Content-Type': 'application/json',
      },
    });
  }

  async sendEvent(event: SecurityEvent): Promise<void> {
    const payload: SecurityEvent = {
      ...event,
      org_id: event.org_id ?? this.orgId,
      timestamp: event.timestamp ?? Date.now(),
    };
    await this.client.post('/api/v1/events/', payload);
  }

  async sendBatch(events: SecurityEvent[]): Promise<void> {
    const payload = events.map((e) => ({
      ...e,
      org_id: e.org_id ?? this.orgId,
      timestamp: e.timestamp ?? Date.now(),
    }));
    await this.client.post('/api/v1/events/batch', payload);
  }

  async getAlerts(resolved?: boolean): Promise<Alert[]> {
    const params: Record<string, string> = {};
    if (resolved !== undefined) {
      params.resolved = String(resolved);
    }
    const res = await this.client.get<Alert[]>('/api/v1/alerts', { params });
    return res.data;
  }

  async triggerScan(target: string): Promise<ScanResult> {
    const res = await this.client.post<ScanResult>('/api/v1/scan', { target, org_id: this.orgId });
    return res.data;
  }

  async getReports(): Promise<Report[]> {
    const res = await this.client.get<Report[]>(`/api/v1/reports/${this.orgId}`);
    return res.data;
  }
}