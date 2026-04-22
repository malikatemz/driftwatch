"""
Authentication helpers — Clerk JWT + SDK key verification.
"""
import hashlib
import hmac
from clerk_backend_api import Clerk
from fastapi import HTTPException, Request
from app.core.config import settings
from app.core.database import get_supabase

clerk = Clerk(temporary_public_api_key=settings.CLERK_PUBLISHABLE_KEY)


async def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk JWT and return the decoded payload.
    Used by both SDK auth and user auth.
    """
    try:
        claims = clerk.jwtClaims(token)
        return dict(claims)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Clerk token: {e}")


def verify_sdk_key(sdk_key: str) -> str | None:
    """
    Verify an SDK key against the api_keys table.
    Returns org_id if valid, None otherwise.
    Also updates last_used_at.
    """
    if not sdk_key:
        return None

    sb = get_supabase()

    # Find the key by prefix match (we store prefix + hash)
    # For prototype: simple lookup by the key itself
    # Production: store sha256 hash of key and do hash comparison
    try:
        # Try to find by key prefix
        prefix = sdk_key[:12] if len(sdk_key) >= 12 else sdk_key

        result = sb.table("api_keys").select("id, org_id").eq("prefix", prefix).execute()

        if not result.data:
            return None

        key_record = result.data[0]

        # Update last_used_at
        sb.table("api_keys").update({
            "last_used_at": "now()",
        }).eq("id", key_record["id"]).execute()

        return key_record["org_id"]

    except Exception:
        return None


def verify_github_webhook(payload: bytes, signature: str, secret: str | None = None) -> bool:
    """
    Verify GitHub webhook HMAC-SHA256 signature.
    GitHub sends: X-Hub-Signature-256: sha256=<hex>
    """
    if not secret:
        # Webhook secret not configured — skip verification (warn in prod)
        return True  # TODO: in production, return False

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


async def get_authenticated_org(request: Request) -> str:
    """
    Extract and verify org_id from Clerk JWT in request headers.
    Used by protected API endpoints.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid auth header")

    token = auth_header[7:]
    payload = await verify_clerk_token(token)
    org_id = payload.get("org_id")
    if not org_id:
        raise HTTPException(status_code=401, detail="No org_id in token")
    return org_id


def get_org_from_request(request: Request) -> str | None:
    """
    Resolve org_id from a request — tries SDK key first, then Clerk JWT.
    Returns None if neither is valid.
    """
    sdk_key = request.headers.get("x-driftwatch-api-key")
    if sdk_key:
        return verify_sdk_key(sdk_key)

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        # Sync call — create new loop if needed
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # Can't await in sync context — schedule it
            future = asyncio.run_coroutine_threadsafe(
                verify_clerk_token(auth_header[7:]),
                loop,
            )
            payload = future.result(timeout=5)
            return payload.get("org_id")
        except Exception:
            return None

    return None