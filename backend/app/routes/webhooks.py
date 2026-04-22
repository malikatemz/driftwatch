"""
Webhooks — receive events from external services (GitHub, CI/CD pipelines).
"""
from fastapi import APIRouter, Request, HTTPException
from app.core.database import get_supabase
import hmac
import hashlib
import json

router = APIRouter()


@router.post("/github")
async def github_webhook(request: Request):
    """
    Listen for git commits to detect credential leaks.
    GitHub sends: push events, pull request events
    """
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")

    # TODO: Verify GitHub webhook signature
    # secret = settings.GITHUB_WEBHOOK_SECRET
    # expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    # if not hmac.compare_digest(signature, expected):
    #     raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)

    # Detect credential patterns in commits
    suspicious_patterns = [
        "api_key=", "apikey=", "secret=", "password=",
        "token=", "bearer ", "Authorization:",
        "aws_access_key", "sk_live_", "sk_test_",
    ]

    findings = []
    if "commits" in payload:
        for commit in payload.get("commits", []):
            message = commit.get("message", "")
            diff = commit.get("diff", "")
            for pattern in suspicious_patterns:
                if pattern.lower() in (message + diff).lower():
                    findings.append({
                        "commit": commit.get("id"),
                        "author": commit.get("author", {}).get("name"),
                        "pattern": pattern,
                    })

    if findings:
        sb = get_supabase()
        # TODO: determine org_id from repo -> org mapping
        sb.table("alerts").insert({
            "org_id": "unknown",  # TODO: map repo to org
            "severity": "critical",
            "type": "credential",
            "title": "Potential credential leak detected in GitHub commit",
            "description": json.dumps(findings),
            "remediation": "Remove secrets from git history using BFG Repo-Cleaner",
        }).execute()

    return {"status": "ok"}


@router.post("/slack")
async def slack_webhook(request: Request):
    """Receive Slack webhook events for alert notifications."""
    body = await request.json()
    # Slack verification challenge
    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge")}
    return {"status": "ok"}
