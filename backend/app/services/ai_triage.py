"""
AI Triage service — uses Claude to reduce false positives and provide remediation.
"""
import logging

logger = logging.getLogger(__name__)

async def triage_alert(alert_data: dict) -> dict:
    """
    Use AI to triage an alert.
    Returns enriched alert with risk scoring and suggested remediation.
    """
    # Stub for Claude-powered triage
    return {
        "risk_score": 0.5,
        "suggested_remediation": "No remediation needed.",
        "ai_summary": "This alert seems to be a false positive."
    }
