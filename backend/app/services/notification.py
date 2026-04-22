"""
Alert notification dispatcher — sends alerts via email (SendGrid) and Slack webhook.
"""
import logging
from typing import Optional

import httpx
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


def _get_notification_channels(org_id: str) -> list[dict]:
    """Fetch active email + Slack webhook channels for an org."""
    sb = get_supabase()
    result = (
        sb.table("webhook_configs")
        .select("*")
        .eq("org_id", org_id)
        .eq("active", True)
        .execute()
    )
    return result.data or []


def _build_email_html(alert: dict) -> str:
    """Build a professional HTML email for an alert."""
    severity = alert.get("severity", "unknown").lower()

    # Severity color mapping
    severity_colors = {
        "critical": "#DC2626",  # red
        "high": "#EA580C",  # orange
        "medium": "#D97706",  # amber
        "low": "#2563EB",  # blue
    }
    color = severity_colors.get(severity, "#6B7280")

    severity_emojis = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
    }
    emoji = severity_emojis.get(severity, "⚠️")
    severity_label = severity.upper()

    title = alert.get("title", "Alert")
    description = alert.get("description", "No description provided.")
    remediation = alert.get("remediation", "N/A")
    alert_type = alert.get("type", "unknown")
    timestamp = alert.get("created_at", "")
    if timestamp:
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            timestamp = dt.strftime("%b %d, %Y at %H:%M UTC")
        except Exception:
            pass
    else:
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).strftime("%b %d, %Y at %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Driftwatch Alert</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F3F4F6;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F3F4F6; padding: 32px 16px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 600px; width: 100%;">

          <!-- Header -->
          <tr>
            <td style="background-color: {color}; padding: 28px 32px; text-align: center;">
              <p style="margin: 0; font-size: 32px;">{emoji}</p>
              <p style="margin: 8px 0 0 0; color: #FFFFFF; font-size: 13px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; opacity: 0.9;">
                DRIFTWATCH ALERT
              </p>
            </td>
          </tr>

          <!-- Severity badge -->
          <tr>
            <td style="padding: 24px 32px 0 32px; text-align: center;">
              <span style="display: inline-block; background-color: {color}; color: #FFFFFF; font-size: 12px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; padding: 6px 16px; border-radius: 20px;">
                {severity_label} SEVERITY
              </span>
            </td>
          </tr>

          <!-- Title -->
          <tr>
            <td style="padding: 20px 32px 0 32px;">
              <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #111827; line-height: 1.3;">
                {title}
              </h1>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding: 16px 32px 0 32px;">
              <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 0;" />
            </td>
          </tr>

          <!-- Details -->
          <tr>
            <td style="padding: 20px 32px 0 32px;">
              <p style="margin: 0; font-size: 14px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                Description
              </p>
              <p style="margin: 8px 0 0 0; font-size: 15px; color: #374151; line-height: 1.6;">
                {description}
              </p>
            </td>
          </tr>

          <!-- Metadata grid -->
          <tr>
            <td style="padding: 20px 32px 0 32px;">
              <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB;">
                <tr>
                  <td style="padding: 14px 16px; border-bottom: 1px solid #E5E7EB;">
                    <p style="margin: 0; font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Type</p>
                    <p style="margin: 4px 0 0 0; font-size: 14px; color: #111827; font-weight: 500; text-transform: capitalize;">{alert_type}</p>
                  </td>
                  <td style="padding: 14px 16px; border-bottom: 1px solid #E5E7EB; border-left: 1px solid #E5E7EB;">
                    <p style="margin: 0; font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Severity</p>
                    <p style="margin: 4px 0 0 0; font-size: 14px; color: {color}; font-weight: 700; text-transform: uppercase;">{severity_label}</p>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 14px 16px;" colspan="2">
                    <p style="margin: 0; font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Timestamp</p>
                    <p style="margin: 4px 0 0 0; font-size: 14px; color: #111827; font-weight: 500;">{timestamp}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Remediation -->
          <tr>
            <td style="padding: 20px 32px 0 32px;">
              <p style="margin: 0; font-size: 14px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                Recommended Action
              </p>
              <p style="margin: 8px 0 0 0; font-size: 15px; color: #374151; line-height: 1.6; background-color: #ECFDF5; border-left: 4px solid #10B981; padding: 12px 16px; border-radius: 0 8px 8px 0;">
                {remediation}
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 28px 32px; text-align: center; border-top: 1px solid #E5E7EB;">
              <p style="margin: 0; font-size: 12px; color: #9CA3AF;">
                This alert was generated automatically by <strong>Driftwatch</strong> — your API security monitoring platform.
              </p>
              <p style="margin: 8px 0 0 0; font-size: 12px; color: #9CA3AF;">
                You're receiving this because you have alert notifications enabled.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_alert_email(org_id: str, alert: dict, to_email: str) -> bool:
    """Send a single alert email. Returns True if sent successfully."""
    if not to_email or not settings.SENDGRID_API_KEY:
        return False

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        html = _build_email_html(alert)
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=to_email,
            subject=f"[{alert['severity'].upper()}] Driftwatch Alert: {alert['title']}",
            html_content=html,
        )
        sg.send(message)
        logger.info(f"Alert email sent to {to_email} for alert '{alert['title']}'")
        return True
    except Exception as e:
        logger.warning(f"Failed to send alert email to {to_email}: {e}")
        return False


def send_slack_alert(org_id: str, alert: dict, webhook_url: str) -> bool:
    """POST a Slack-formatted alert to a webhook URL."""
    if not webhook_url:
        return False

    severity_emojis = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
    emoji = severity_emojis.get(alert["severity"], "⚠️")
    payload = {
        "text": f"{emoji} *{alert['title']}*",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} {alert['title']}"},
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{alert['severity'].upper()}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{alert.get('type', 'unknown')}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{alert.get('description', '')}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Remediation:*\n{alert.get('remediation', 'N/A')}",
                },
            },
        ],
    }
    try:
        import asyncio

        asyncio.run(httpx.AsyncClient().post(webhook_url, json=payload, timeout=5.0))
        logger.info(f"Slack alert sent for '{alert['title']}'")
        return True
    except Exception as e:
        logger.warning(f"Failed to send Slack alert: {e}")
        return False


def dispatch_alert(org_id: str, alert: dict) -> None:
    """
    Send an alert to all configured notification channels for the org.
    Only sends for high/critical severity. Skips medium/low silently.
    """
    severity = alert.get("severity", "").lower()
    if severity not in ("critical", "high"):
        return

    channels = _get_notification_channels(org_id)
    if not channels:
        logger.debug(f"No notification channels configured for org {org_id}")
        return

    for channel in channels:
        channel_type = channel.get("type")
        config = channel.get("config") or {}

        if channel_type == "email":
            send_alert_email(org_id, alert, config.get("email"))
        elif channel_type == "slack":
            send_slack_alert(org_id, alert, config.get("webhook_url"))
