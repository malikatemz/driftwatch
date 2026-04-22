"""
Port scanner — detects exposed ports on infrastructure.
Usage: sentinelapi.scan("api.yoursite.com")
"""
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional

import httpx
import os


COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
    993, 995, 1723, 3306, 3389, 5900, 8080, 8443, 9200, 27017,
]

RISK_CLASSIFICATION = {
    21: ("HIGH", "FTP — unencrypted file transfer, credentials in clear text"),
    22: ("LOW", "SSH — usually safe if key-based auth; verify exposure intent"),
    23: ("HIGH", "Telnet — unencrypted remote access, disable immediately"),
    25: ("MEDIUM", "SMTP — verify it's intentional; open relay risk"),
    53: ("LOW", "DNS — normal for nameservers; restrict zone transfers"),
    80: ("LOW", "HTTP — normal for web services"),
    110: ("MEDIUM", "POP3 — unencrypted email retrieval"),
    111: ("HIGH", "RPCbind — can leak NFS mounts and service info"),
    135: ("HIGH", "MSRPC — Windows RPC endpoint mapper; restrict to LAN"),
    139: ("HIGH", "NetBIOS — legacy SMB; disable if not required"),
    143: ("MEDIUM", "IMAP — unencrypted email access"),
    443: ("LOW", "HTTPS — normal encrypted web"),
    445: ("HIGH", "SMB — can leak file shares; restrict to LAN"),
    993: ("LOW", "IMAPS — encrypted email"),
    995: ("LOW", "POP3S — encrypted email"),
    1723: ("MEDIUM", "PPTP — weak VPN protocol, consider IKEv2/WireGuard"),
    3306: ("HIGH", "MySQL — should never be internet-facing without a tunnel"),
    3389: ("HIGH", "RDP — high-value attack target; restrict via firewall"),
    5900: ("HIGH", "VNC — unencrypted remote desktop, often unauthenticated"),
    8080: ("MEDIUM", "HTTP alt — often dev servers; verify it's intentional"),
    8443: ("LOW", "HTTPS alt — often admin panels; verify exposure intent"),
    9200: ("HIGH", "Elasticsearch — often unauthenticated by default, data leak risk"),
    27017: ("HIGH", "MongoDB — often unauthenticated, complete database access risk"),
}


def _classify_port(port: int) -> tuple[str, str]:
    """Return (risk_level, description) for a port."""
    return RISK_CLASSIFICATION.get(port, ("LOW", "standard service"))


def _scan_port(host: str, port: int, timeout: float = 1.5) -> Optional[dict]:
    """Attempt to connect to a single port. Returns port info if open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            risk_level, description = _classify_port(port)
            return {
                "port": port,
                "status": "open",
                "risk_level": risk_level,
                "description": description,
            }
    except Exception:
        pass
    return None


async def _report_scan_results(
    target: str,
    open_ports: list[dict],
    risks: list[dict],
    api_key: str,
    base_url: str,
) -> None:
    """Send scan results to SentinelAPI as a security event."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{base_url}/api/v1/events/",
                json={
                    "event_type": "scan_completed",
                    "target": target,
                    "open_ports": [p["port"] for p in open_ports],
                    "risks": risks,
                    "scanned_at": datetime.now(timezone.utc).isoformat(),
                },
                headers={"x-sentinel-api-key": api_key},
                timeout=10.0,
            )
    except Exception:
        pass  # Don't fail the scan if reporting fails


def scan(
    target: str,
    ports: list[int] | None = None,
    timeout: float = 1.5,
    api_key: str | None = None,
    base_url: str = "https://api.sentinelapi.io",
    report: bool = True,
) -> dict:
    """
    Scan a target host for open ports and security risks.

    Args:
        target: Hostname or IP address to scan.
        ports: List of ports to scan. Defaults to COMMON_PORTS.
        timeout: Per-port connection timeout in seconds. Default 1.5.
        api_key: SentinelAPI key. Falls back to SENTINEL_API_KEY env var.
        base_url: SentinelAPI base URL.
        report: Whether to POST scan results to SentinelAPI. Default True.

    Returns:
        dict with keys:
            - target: the host that was scanned
            - open_ports: list of open ports with risk info
            - risks: list of HIGH/MEDIUM risk ports with descriptions
            - summary: human-readable summary string
            - scanned_at: ISO timestamp
    """
    host = target.replace("https://", "").replace("http://", "").rstrip("/").split(":")[0].split("/")[0]
    port_list = ports or COMMON_PORTS

    open_ports: list[dict] = []
    risks: list[dict] = []

    with ThreadPoolExecutor(max_workers=min(50, len(port_list))) as executor:
        futures = {executor.submit(_scan_port, host, p, timeout): p for p in port_list}
        for future in as_completed(futures):
            result = future.result()
            if result:
                open_ports.append(result)
                if result["risk_level"] in ("HIGH", "MEDIUM"):
                    risks.append({
                        "port": result["port"],
                        "risk_level": result["risk_level"],
                        "issue": result["description"],
                        "recommendation": f"Close port {result['port']} or restrict via firewall",
                    })

    scanned_at = datetime.now(timezone.utc).isoformat()
    response: dict = {
        "target": host,
        "open_ports": open_ports,
        "risks": risks,
        "summary": f"{len(open_ports)} open, {len(risks)} risks identified",
        "scanned_at": scanned_at,
    }

    # Report results to SentinelAPI in background
    key = api_key or os.getenv("SENTINEL_API_KEY")
    if key and report:
        import asyncio
        try:
            asyncio.create_task(_report_scan_results(host, open_ports, risks, key, base_url))
        except RuntimeError:
            # No event loop running — run it synchronously
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_report_scan_results(host, open_ports, risks, key, base_url))
            except Exception:
                pass
            finally:
                loop.close()

    return response


__all__ = ["scan", "COMMON_PORTS"]
