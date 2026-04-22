"""
Webhooks — GitHub (credential leak detection), Slack (notification), generic.
"""
from fastapi import APIRouter, Request, HTTPException
from app.core.database import get_supabase
from app.core.auth import verify_github_webhook
from app.core.config import settings
import json

router = APIRouter()

# ─── Credential patterns to detect ───────────────────────────────────────────
SUSPICIOUS_PATTERNS = [
    "api_key=", "apikey=", "secret=", "password=",
    "token=", "bearer ", "Authorization:",
    "aws_access_key", "sk_live_", "sk_test_",
    "ghp_", "gho_", "github_pat_",
    "AKIA",  # AWS access key ID prefix
    "xoxb-", "xoxp-",  # Slack tokens
]

# ─── GitHub webhook ────────────────────────────────────────────────────────────
@router.post("/github")
async def github_webhook(request: Request):
    """
    Listen for GitHub push/PR events to detect credential leaks.
    Verifies HMAC-SHA256 signature if GITHUB_WEBHOOK_SECRET is set.
    """
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")

    # Verify signature
    if not verify_github_webhook(body, signature, settings.GITHUB_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Resolve org_id from repository → org mapping
    repo_full_name = payload.get("repository", {}).get("full_name", "")
    org_id = _resolve_org_from_repo(repo_full_name)
    if not org_id:
        # Webhook received for untracked repo — could be noise, log and skip
        return {"status": "skipped", "reason": "unregistered_repository"}

    # Extract commits
    commits = payload.get("commits", [])
    if not commits:
        return {"status": "ok", "leaks_found": 0}

    findings = []
    for commit in commits:
        # Check message, diff, and added files
        text_to_scan = " ".join([
            commit.get("message", ""),
            commit.get("diff", ""),
            # GitHub doesn't send 'files' in push event by default,
            # but we scan the message + diff
        ]).lower()

        for pattern in SUSPICIOUS_PATTERNS:
            if pattern.lower() in text_to_scan:
                findings.append({
                    "commit": commit.get("id"),
                    "author": commit.get("author", {}).get("name"),
                    "email": commit.get("author", {}).get("email"),
                    "pattern": pattern,
                    "message": commit.get("message", "")[:200],
                })

    # Create alert for any findings
    if findings:
        sb = get_supabase()
        sb.table("alerts").insert({
            "org_id": org_id,
            "severity": "critical",
            "type": "credential",
            "title": "Potential credential leak in GitHub commit",
            "description": json.dumps(findings[:10]),  # cap at 10
            "remediation": (
                "1. Force-push a commit that removes the secret. "
                "2. Use 'git filter-branch' or 'BFG Repo-Cleaner' to rewrite history. "
                "3. Rotate the exposed credential immediately. "
                "4. Review CI/CD pipelines for exposed secrets."
            ),
        }).execute()

        return {"status": "alert_created", "leaks_found": len(findings)}

    return {"status": "ok", "leaks_found": 0}


# ─── Slack webhook ─────────────────────────────────────────────────────────────
@router.post("/slack")
async def slack_webhook(request: Request):
    """
    Slack sends events here — mostly URL verification and interactive payloads.
    For alert forwarding (Driftwatch → Slack), configure the Slack webhook URL
    in the dashboard settings and use it as a notification channel, not here.
    """
    body = await request.json()

    # Slack URL verification challenge
    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge")}

    # Event callback
    if body.get("type") == "event_callback":
        event = body.get("event", {})
        # Handle Slack app_mention or direct message if needed
        return {"status": "ok"}

    return {"status": "ok"}


# ─── Generic webhook (generic alert forwarding) ──────────────────────────────
@router.post("/generic")
async def generic_webhook(request: Request, org_id: str | None = None):
    """
    Generic webhook for external integrations (Grafana, PagerDuty, etc.).
    Accepts: { "alert": "...", "severity": "...", "meta": {...} }
    """
    body = await request.json()
    alert_text = body.get("alert", "")
    severity = body.get("severity", "medium")
    meta = body.get("meta", {})

    target_org = org_id or body.get("org_id")
    if not target_org:
        raise HTTPException(status_code=400, detail="org_id required")

    sb = get_supabase()
    sb.table("alerts").insert({
        "org_id": target_org,
        "severity": severity,
        "type": "webhook",
        "title": alert_text[:200] if alert_text else "External webhook alert",
        "description": json.dumps(meta),
        "remediation": "Review the external system's alert details.",
    }).execute()

    return {"status": "received"}


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _resolve_org_from_repo(repo_full_name: str) -> str | None:
    """
    Map a GitHub repo (e.g. 'acme/my-api') to an org_id in our system.
    For prototype: hardcoded mapping stored in a webhook_configs table.
    Production: use the webhook_configs table to store repo → org mappings.
    """
    if not repo_full_name:
        return None

    sb = get_supabase()
    result = sb.table("webhook_configs").select("org_id").eq(
        "config", {"repo": repo_full_name}
    ).eq("type", "github").eq("active", True).execute()

    if result.data:
        return result.data[0]["org_id"]

    # Fallback: check if org has a default GitHub integration
    # (prototype: first org is default for testing)
    return None