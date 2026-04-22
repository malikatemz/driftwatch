"""
Clerk authentication helpers.
"""
from clerk_backend_api import Clerk
from fastapi import HTTPException, Request
from app.core.config import settings

clerk = Clerk(temporary_public_api_key=settings.CLERK_PUBLISHABLE_KEY)


async def get_authenticated_org(request: Request) -> str:
    """
    Extract and verify the org_id from Clerk JWT in request headers.
    The frontend sends: Authorization: Bearer <jwt>
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid auth header")

    token = auth_header[7:]  # Strip "Bearer "

    try:
        claims = clerk.jwtClaims(token)
        org_id = claims["org_id"]
        return org_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
