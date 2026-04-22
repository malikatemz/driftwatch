import axios from 'axios';

export type ReportType = 'soc2' | 'gdpr' | 'iso27001';

interface ReportResponse {
  id: string;
  org_id: string;
  type: ReportType;
  status: 'pending' | 'generating' | 'ready' | 'failed';
  content?: string;
  created_at: string;
  ready_at?: string;
}

export async function report(
  orgId: string,
  apiKey: string,
  type: ReportType,
  baseUrl = 'https://api.driftwatch.io'
): Promise<string> {
  const client = axios.create({
    baseURL: baseUrl,
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
  });

  // Try to fetch existing report
  try {
    const existing = await client.get<ReportResponse>(`/api/v1/reports/${orgId}`);
    const ready = existing.data.find(
      (r) => r.type === type && r.status === 'ready' && r.content
    );
    if (ready?.content) {
      return ready.content;
    }
  } catch {
    // No existing report — fall through to generate
  }

  // Trigger generation
  const gen = await client.post<ReportResponse>(`/api/v1/reports/${orgId}/generate`, { type });
  const reportId = gen.data.id;

  // Poll until ready
  const maxAttempts = 15; // 30s at 2s intervals
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((resolve) => setTimeout(resolve, 2000));

    const statusResp = await client.get<ReportResponse>(`/api/v1/reports/${orgId}`);
    const latest = statusResp.data.find((r) => r.id === reportId);

    if (!latest) continue;

    if (latest.status === 'ready' && latest.content) {
      return latest.content;
    }

    if (latest.status === 'failed') {
      throw new Error(`Report generation failed for type: ${type}`);
    }
  }

  throw new Error(`Report generation timed out after 30s for type: ${type}`);
}