"""
Port scanner service — integrates with existing cyber_audit logic.
"""
import socket
import asyncio
from app.core.database import get_supabase
from concurrent.futures import ThreadPoolExecutor

# Common ports to scan
COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
    993, 995, 1723, 3306, 3389, 5900, 8080, 8443, 9200, 27017,
]

# Port risk labels
RISK_PORTS = {
    21: "FTP — unencrypted file transfer",
    22: "SSH — usually OK if authenticated",
    23: "Telnet — unencrypted, disable immediately",
    25: "SMTP — verify it's intentional mail relay",
    3306: "MySQL — should not be internet-facing",
    3389: "RDP — high risk if exposed",
    5900: "VNC — unencrypted remote access",
    8080: "HTTP proxy — verify it's intentional",
    9200: "Elasticsearch — often unauthenticated by default",
    27017: "MongoDB — should not be internet-facing",
}


def scan_port(target: str, port: int, timeout: float = 1.0) -> dict | None:
    """Scan a single port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target, port))
        sock.close()
        if result == 0:
            return {"port": port, "status": "open", "risk": RISK_PORTS.get(port, "standard service")}
    except Exception:
        pass
    return None


def scan_target(target: str) -> tuple[list, list]:
    """
    Scan all common ports on a target.
    Returns (open_ports, risks).
    """
    open_ports = []
    risks = []

    # Parse host from URL if needed
    host = target.replace("https://", "").replace("http://", "").split("/")[0]

    with ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(lambda p: scan_port(host, p), COMMON_PORTS)

    for result in results:
        if result:
            open_ports.append(result)
            if result["port"] in RISK_PORTS:
                risks.append({
                    "port": result["port"],
                    "issue": RISK_PORTS[result["port"]],
                    "recommendation": f"Close port {result['port']} or restrict access via firewall",
                })

    return open_ports, risks


def run_scan(org_id: str, scan_id: str, target: str):
    """Run a scan and update the database."""
    open_ports, risks = scan_target(target)

    sb = get_supabase()
    sb.table("scans").update({
        "open_ports": open_ports,
        "risks": risks,
    }).eq("id", scan_id).execute()

    # Create alerts for high-risk findings
    if risks:
        for risk in risks:
            sb.table("alerts").insert({
                "org_id": org_id,
                "severity": "high",
                "type": "port",
                "title": f"High-risk port exposed: {risk['port']}",
                "description": risk["issue"],
                "remediation": risk["recommendation"],
                "resolved": False,
            }).execute()
