"""
Alert Engine — evaluates events and creates alerts.
Anomaly detection uses Z-score on request rate, IP clusters, response codes.
"""
from app.core.database import get_supabase
from app.models.schemas import AlertCreate
import numpy as np


class AlertEngine:
    def __init__(self):
        self.baseline_window_hours = 24

    def evaluate_event(self, org_id: str, event: dict) -> list[AlertCreate]:
        """
        Evaluate a single event against the org's baseline.
        Returns list of alerts if anomalies detected.
        """
        alerts = []

        # Z-score anomaly detection
        if event.get("anomaly_score", 0) > 2.5:
            alerts.append(AlertCreate(
                severity="high",
                type="anomaly",
                title="Anomalous API request detected",
                description=f"Unusual request pattern: {event.get('method')} {event.get('path')} from {event.get('ip')}",
                remediation="Review the request source. If malicious, block the IP.",
            ))

        # Rate limit detection (429 responses)
        if event.get("status_code") == 429:
            alerts.append(AlertCreate(
                severity="medium",
                type="rate_limit",
                title="Rate limit triggered",
                description=f"Your API is rejecting requests due to rate limiting at {event.get('path')}",
                remediation="Consider increasing rate limits or implementing caching.",
            ))

        # High error rate (5xx responses)
        if event.get("status_code", 0) >= 500:
            alerts.append(AlertCreate(
                severity="medium",
                type="anomaly",
                title="API server error",
                description=f"Backend returned {event.get('status_code')} at {event.get('path')}",
                remediation="Check your server logs. This may indicate a security issue or outage.",
            ))

        # Suspicious user agent
        suspicious_agents = ["sqlmap", "nikto", "nmap", "masscan", "hydra", "burp"]
        ua = event.get("user_agent", "").lower()
        if any(bot in ua for bot in suspicious_agents):
            alerts.append(AlertCreate(
                severity="critical",
                type="anomaly",
                title="Security scanner detected",
                description=f"Automated security tool detected: {event.get('user_agent')}",
                remediation="Block this IP immediately. You're being scanned.",
            ))

        return alerts

    def save_alerts(self, org_id: str, alerts: list[AlertCreate]):
        """Persist alerts to Supabase and send notifications."""
        if not alerts:
            return

        sb = get_supabase()
        for alert in alerts:
            sb.table("alerts").insert({
                **alert.model_dump(),
                "org_id": org_id,
                "resolved": False,
            }).execute()

        # TODO: Send Slack/email notifications
        self._notify(alerts)

    def _notify(self, alerts: list[AlertCreate]):
        """Send notifications via Slack/email."""
        critical = [a for a in alerts if a.severity == "critical"]
        if critical:
            # TODO: Send immediate Slack DM to org admin
            pass
