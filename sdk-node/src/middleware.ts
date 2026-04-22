import { Request, Response, NextFunction } from 'express';
import { DWClient, SecurityEvent } from './client';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface MiddlewareOptions {
  apiKey: string;
  orgId: string;
  baseUrl?: string;
}

// ─── Scoring ─────────────────────────────────────────────────────────────────

function scoreAnomaly(req: Request, res: Response, latencyMs: number): number {
  let score = 0;

  // Latency scoring
  if (latencyMs > 3000) {
    score += 1.0;
  } else if (latencyMs > 1000) {
    score += 0.5;
  }

  // Status code scoring
  const status = res.statusCode;
  if (status >= 500) {
    score += 2.0;
  } else if (status === 429) {
    score += 1.5;
  }

  // Unusual HTTP methods
  const dangerous = ['TRACE', 'CONNECT', 'OPTIONS'];
  if (dangerous.includes(req.method)) {
    score += 1.0;
  }

  // Probing paths
  const probing = ['/admin', '/.env', '/wp-login', '/phpmyadmin', '/config', '/backup', '/.git'];
  const path = req.path.toLowerCase();
  for (const p of probing) {
    if (path.includes(p)) {
      score += 2.0;
      break;
    }
  }

  return Math.round(score * 10) / 10;
}

// ─── Batching ─────────────────────────────────────────────────────────────────

interface PendingEvent {
  event: SecurityEvent;
  timer: NodeJS.Timeout;
}

function createBatcher(
  client: DWClient,
  intervalMs = 5000,
  maxBatch = 100
): (event: SecurityEvent) => void {
  const pending: SecurityEvent[] = [];
  let timer: NodeJS.Timeout | null = null;

  const flush = async () => {
    if (pending.length === 0) return;
    const batch = pending.splice(0, pending.length);
    try {
      await client.sendBatch(batch);
    } catch {
      // silent — don't crash the server
    }
  };

  return (event: SecurityEvent) => {
    pending.push(event);

    if (!timer) {
      timer = setTimeout(async () => {
        timer = null;
        await flush();
      }, intervalMs);
    }

    if (pending.length >= maxBatch) {
      if (timer) clearTimeout(timer);
      timer = null;
      flush().catch(() => {});
    }
  };
}

// ─── Middleware Factory ───────────────────────────────────────────────────────

export function init(options: MiddlewareOptions) {
  const client = new DWClient(options);
  const batch = createBatcher(client);

  return (req: Request, res: Response, next: NextFunction): void => {
    const start = Date.now();

    // Capture original end
    const originalEnd = res.end;
    const originalJson = res.json;

    // Hook into finish so we have status code
    res.end = function (this: Response, ...args: Parameters<Response['end']>): Response {
      const latencyMs = Date.now() - start;
      const ip =
        (req.headers['x-forwarded-for'] as string)?.split(',')[0]?.trim() ??
        req.socket.remoteAddress ??
        'unknown';
      const userAgent = req.headers['user-agent'] ?? 'unknown';

      const event: SecurityEvent = {
        method: req.method,
        path: req.path,
        status_code: res.statusCode,
        latency_ms: latencyMs,
        ip,
        user_agent: userAgent,
        anomaly_score: scoreAnomaly(req, res, latencyMs),
        org_id: options.orgId,
        timestamp: Date.now(),
      };

      batch(event);
      return originalEnd.apply(this, args);
    } as typeof res.end;

    next();
  };
}

// ─── Fastify adaptation note ──────────────────────────────────────────────────
// Fastify users can wrap this middleware manually or use the fastify-adapted
// variant below. For explicit Fastify support a separate adapter is recommended.

export function fastifyInit(options: MiddlewareOptions) {
  const client = new DWClient(options);
  const batch = createBatcher(client);

  return async function dwHook(
    req: { method: string; url: string; headers: Record<string, string | string[] | undefined>; socket: { remoteAddress?: string } },
    reply: { statusCode: number; end: () => void }
  ): Promise<void> {
    const start = Date.now();

    await reply;

    const latencyMs = Date.now() - start;
    const ip =
      (req.headers['x-forwarded-for'] as string)?.split(',')[0]?.trim() ??
      req.socket.remoteAddress ??
      'unknown';

    const event: SecurityEvent = {
      method: req.method,
      path: req.url,
      status_code: reply.statusCode,
      latency_ms: latencyMs,
      ip,
      user_agent: (req.headers['user-agent'] as string) ?? 'unknown',
      anomaly_score: 0, // scoring done via pre-hook if needed
      org_id: options.orgId,
      timestamp: Date.now(),
    };

    batch(event);
  };
}