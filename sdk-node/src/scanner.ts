import { createSocket } from 'net';
import { DWClient, ScanResult, PortResult } from './client';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ScannerOptions {
  apiKey: string;
  orgId: string;
  baseUrl?: string;
}

// ─── Defaults ────────────────────────────────────────────────────────────────

const DEFAULT_PORTS = [
  21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
  993, 995, 1723, 3306, 3389, 5900, 8080, 8443, 9200, 27017,
];

const PORT_SERVICE: Record<number, string> = {
  21: 'FTP',
  22: 'SSH',
  23: 'Telnet',
  25: 'SMTP',
  53: 'DNS',
  80: 'HTTP',
  110: 'POP3',
  111: 'RPCbind',
  135: 'MSRPC',
  139: 'NetBIOS',
  143: 'IMAP',
  443: 'HTTPS',
  445: 'SMB',
  993: 'IMAPS',
  995: 'POP3S',
  1723: 'PPTP',
  3306: 'MySQL',
  3389: 'RDP',
  5900: 'VNC',
  8080: 'HTTP-alt',
  8443: 'HTTPS-alt',
  9200: 'Elasticsearch',
  27017: 'MongoDB',
};

const HIGH_RISK = new Set([21, 23, 135, 139, 445, 3306, 3389, 5900, 9200, 27017]);
const MEDIUM_RISK = new Set([25, 110, 111, 143, 993, 995, 1723, 8080]);

function classifyRisk(port: number): PortResult['risk'] {
  if (HIGH_RISK.has(port)) return 'HIGH';
  if (MEDIUM_RISK.has(port)) return 'MEDIUM';
  return 'LOW';
}

// ─── Scan single port ─────────────────────────────────────────────────────────

function scanPort(host: string, port: number, timeout = 2000): Promise<PortResult> {
  return new Promise((resolve) => {
    const socket = createSocket();
    socket.setTimeout(timeout);

    socket.on('connect', () => {
      socket.destroy();
      resolve({
        port,
        open: true,
        risk: classifyRisk(port),
        service: PORT_SERVICE[port],
      });
    });

    socket.on('timeout', () => {
      socket.destroy();
      resolve({ port, open: false, risk: 'LOW' });
    });

    socket.on('error', () => {
      socket.destroy();
      resolve({ port, open: false, risk: 'LOW' });
    });

    socket.connect(port, host);
  });
}

// ─── Main scan ───────────────────────────────────────────────────────────────

export async function scan(
  target: string,
  ports: number[] = DEFAULT_PORTS,
  options?: ScannerOptions
): Promise<ScanResult> {
  const results = await Promise.all(
    ports.map((port) => scanPort(target, port))
  );

  const scanResult: ScanResult = {
    target,
    ports: results,
    scanned_at: Date.now(),
  };

  // Report to Driftwatch in background
  if (options?.apiKey && options?.orgId) {
    const client = new DWClient({
      apiKey: options.apiKey,
      orgId: options.orgId,
      baseUrl: options.baseUrl,
    });

    // Fire and forget — don't block the return
    client
      .sendBatch(
        results
          .filter((r) => r.open)
          .map((r) => ({
            event_type: 'scan_result',
            target,
            port: r.port,
            service: r.service,
            risk: r.risk,
            scanned_at: scanResult.scanned_at,
            org_id: options.orgId,
          })) as unknown as import('./client').SecurityEvent[]
      )
      .catch(() => {});
  }

  return scanResult;
}

// ─── Convenience wrapper ──────────────────────────────────────────────────────

export function createScanner(options: ScannerOptions) {
  return (target: string, ports?: number[]) => scan(target, ports, options);
}