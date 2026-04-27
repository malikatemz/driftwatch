"""
Clerk webhook — handles user.created, user.updated, organization events.
Verifies Svix signature and auto-provisions orgs on first sign-up.
"""
from fastapi import APIRouter, Request, HTTPException
from app.core.database import get_supabase
from app.core.config import settings
import json, logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Svix verification (pip install svix)
try:
    from svix import Webhooks
    SVIX_AVAILABLE = True
except ImportError:
    SVIX_AVAILABLE = False
    logger.warning("svix not installed — Clerk webhook signature verification disabled")


async def verify_clerk_signature(request: Request) -> dict:
    """
    Verify Clerk webhook signature using Svix.
    Clerk sends: svix-id, svix-timestamp, svix-signature headers.
    """
    if not SVIX_AVAILABLE:
        logger.warning("Clerk webhook: svix not installed, skipping signature verification")
        return await request.json()

    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp")
    svix_signature = request.headers.get("svix-signature")

    if not all([svix_id, svix_timestamp, svix_signature]):
        raise HTTPException(status_code=401, detail="Missing Clerk Svix headers")

    if not settings.CLERK_WEBHOOK_SECRET:
        logger.warning("CLERK_WEBHOOK_SECRET not set — skipping Clerk verification")
        return await request.json()

    try:
        wh = Webhooks(settings.CLERK_WEBHOOK_SECRET)
        payload = await request.body()
        payload_dict = wh.verify(payload, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        })
        return payload_dict
    except Exception as e:
        logger.error(f"Clerk webhook signature verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Clerk webhook signature")


@router.post("/clerk")
async def clerk_webhook(request: Request):
    """
    Receive Clerk webhook events.
    Events: user.created, user.updated, organization.created, organizationMembership.created
    """
    payload = await verify_clerk_signature(request)
    event_type = payload.get("type", "")

    sb = get_supabase()

    # ── user.created — first sign-up ───────────────────────────────────────
    if event_type == "user.created":
        data = payload.get("data", {})
        user_id = data.get("id")
        email = data.get("email_addresses", [{}])[0].get("email_address", "")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

        # Check if user already exists
        existing = sb.table("users").select("id").eq("id", user_id).execute()
        if existing.data:
            logger.info(f"Clerk user.created: user {user_id} already exists, skipping")
            return {"status": "skipped", "reason": "user_exists"}

        # Create user record (org_id will be assigned below or via organizationMembership)
        sb.table("users").insert({
            "id": user_id,
            "email": email,
            "name": f"{first_name} {last_name}".strip(),
        }).execute()

        logger.info(f"Clerk: created user record for {email}")
        return {"status": "ok", "user_id": user_id}

    # ── user.updated ───────────────────────────────────────────────────────
    if event_type == "user.updated":
        data = payload.get("data", {})
        user_id = data.get("id")
        email = data.get("email_addresses", [{}])[0].get("email_address", "")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

        sb.table("users").update({
            "email": email,
            "name": f"{first_name} {last_name}".strip(),
        }).eq("id", user_id).execute()

        logger.info(f"Clerk: updated user {user_id}")
        return {"status": "ok"}

    # ── organization.created — org created in Clerk dashboard ──────────────
    if event_type == "organization.created":
        data = payload.get("data", {})
        org_id = data.get("id")  # Clerk org ID
        name = data.get("name", "My Organization")

        # Create org in our DB with a mapping
        sb.table("organizations").insert({
            "id": org_id,
            "name": name,
            "plan": "starter",  # default plan
        }).execute()

        logger.info(f"Clerk: created org {org_id} ('{name}')")
        return {"status": "ok", "org_id": org_id}

    # ── organizationMembership.created — user joins an org ───────────────
    if event_type == "organizationMembership.created":
        data = payload.get("data", {})
        user_id = data.get("user_id", {}).get("id")
        org_id = data.get("organization_id")

        if not user_id or not org_id:
            return {"status": "skipped", "reason": "missing_user_id_or_org_id"}

        # Ensure org exists
        org_check = sb.table("organizations").select("id").eq("id", org_id).execute()
        if not org_check.data:
            sb.table("organizations").insert({
                "id": org_id,
                "name": "Organization",
                "plan": "starter",
            }).execute()

        # Link user to org
        sb.table("users").update({"org_id": org_id}).eq("id", user_id).execute()

        # Ensure user has an API key
        key_check = sb.table("api_keys").select("id").eq("org_id", org_id).limit(1).execute()
        if not key_check.data:
            import secrets
            api_key = f"dw_{secrets.token_urlsafe(32)}"
            # In production: hash the key before storing
            sb.table("api_keys").insert({
                "org_id": org_id,
                "key_hash": api_key,  # TODO: hash in production
                "prefix": api_key[:12],
                "name": "Default API Key",
            }).execute()
            logger.info(f"Created default API key for org {org_id}")

        logger.info(f"Clerk: linked user {user_id} to org {org_id}")
        return {"status": "ok"}

    return {"status": "ok", "event": event_type}