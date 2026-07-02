"""
Compliance report generator — uses Claude API.
"""
import anthropic
from app.core.config import settings
from app.core.database import get_supabase

REPORT_TEMPLATES = {
    "soc2": {
        "title": "SOC 2 Compliance Report",
        "sections": [
            "Access Controls",
            "Change Management",
            "Monitoring and Logging",
            "Incident Response",
            "Data Protection",
            "Vendor Management",
        ],
    },
    "gdpr": {
        "title": "GDPR Compliance Report",
        "sections": [
            "Data Processing Lawfulness",
            "Data Subject Rights",
            "Data Breach Notification",
            "Privacy by Design",
            "International Data Transfers",
        ],
    },
    "iso27001": {
        "title": "ISO 27001 Compliance Report",
        "sections": [
            "Information Security Policies",
            "Asset Management",
            "Access Control",
            "Cryptography",
            "Physical Security",
            "Operations Security",
            "Communications Security",
        ],
    },
}


async def generate_compliance_report(org_id: str, report_type: str) -> str:
    """
    Generate a compliance report using Claude.
    Pulls org data (alerts, scans, events) to build the report.
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    sb = get_supabase()

    # Gather org data
    alerts = sb.table("alerts").select("*").eq("org_id", org_id).execute().data
    scans = sb.table("scans").select("*").eq("org_id", org_id).execute().data
    endpoints = sb.table("endpoints").select("*").eq("org_id", org_id).execute().data

    # Build context summary
    open_alerts = [a for a in alerts if not a["resolved"]]
    critical_alerts = [a for a in open_alerts if a["severity"] in ("high", "critical")]
    total_findings = len(scans)
    high_risk_ports = []
    for scan in scans:
        for risk in scan.get("risks", []):
            high_risk_ports.append(risk)

    template = REPORT_TEMPLATES.get(report_type, REPORT_TEMPLATES["soc2"])

    prompt = f"""
Generate a {template['title']} for an organization with the following security posture:

MONITORED ENDPOINTS: {len(endpoints)}
OPEN ALERTS: {len(open_alerts)}
CRITICAL ALERTS: {len(critical_alerts)}
RECENT SCAN RESULTS: {total_findings} scans completed

RECENT HIGH-RISK FINDINGS:
{chr(10).join([f"- {a['title']}: {a['description']}" for a in critical_alerts[:5]]) or 'No critical alerts'}

PORT SCAN FINDINGS:
{chr(10).join([f"- Port {r['port']}: {r['issue']}" for r in high_risk_ports[:5]]) or 'No high-risk ports detected'}

Generate a comprehensive {template['title']} with the following sections:
{chr(10).join([f"- {s}" for s in template['sections']])}

Format as a professional audit report with:
1. Executive summary (2-3 paragraphs)
2. Each section with findings, evidence, and recommendations
3. Overall compliance posture summary
4. Remediation roadmap (prioritized by risk)

Be specific and actionable. This report will be reviewed by security auditors.
"""

    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
