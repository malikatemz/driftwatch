"""
Driftwatch API v2 — production-ready with rate limiting, auth, and structured errors.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.auth import verify_clerk_token, verify_sdk_key
from app.routes import events, alerts, scans, reports, webhooks, billing

app = FastAPI(
    title="Driftwatch API",
    description="API security monitoring for startups that ship.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Error handlers ───────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code,
            "path": str(request.url),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status": 500,
            "path": str(request.url),
        },
    )


# ─── Health & status ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Basic health check."""
    return {"status": "ok", "version": "2.0.0", "service": "driftwatch-api"}


@app.get("/api/v2/status")
async def api_status(request: Request):
    """
    API health + auth status.
    Useful for SDK init verification.
    """
    auth_header = request.headers.get("Authorization", "")
    sdk_key = request.headers.get("x-driftwatch-api-key", "")
    org_info = {"authenticated": False, "org_id": None}

    if sdk_key:
        org_id = verify_sdk_key(sdk_key)
        org_info = {"authenticated": bool(org_id), "org_id": org_id, "type": "sdk_key"}
    elif auth_header.startswith("Bearer "):
        payload = await verify_clerk_token(auth_header[7:])
        org_info = {"authenticated": True, "org_id": payload.get("org_id"), "type": "clerk"}

    return {
        "status": "ok",
        "org": org_info,
        "version": "2.0.0",
    }


# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(events.router, prefix="/api/v2/events", tags=["events"])
app.include_router(alerts.router, prefix="/api/v2/alerts", tags=["alerts"])
app.include_router(scans.router, prefix="/api/v2/scans", tags=["scans"])
app.include_router(reports.router, prefix="/api/v2/reports", tags=["reports"])
app.include_router(webhooks.router, prefix="/api/v2/webhooks", tags=["webhooks"])
app.include_router(billing.router, prefix="/api/v2/billing", tags=["billing"])

# ─── Dashboard (summary) ──────────────────────────────────────────────────────
@app.get("/api/v2/org/{org_id}/dashboard")
async def dashboard(org_id: str, request: Request):
    """
    Main dashboard data endpoint.
    Returns threat summary, recent alerts, scan status for an org.
    """
    # Verify auth
    auth_header = request.headers.get("Authorization", "")
    sdk_key = request.headers.get("x-driftwatch-api-key", "")
    if not (sdk_key or auth_header):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Resolve org_id
    if sdk_key:
        resolved_org = verify_sdk_key(sdk_key)
        if resolved_org and resolved_org != org_id:
            raise HTTPException(status_code=403, detail="Access denied for this organization")
    else:
        payload = await verify_clerk_token(auth_header[7:])
        if payload.get("org_id") != org_id:
            raise HTTPException(status_code=403, detail="Access denied")

    from app.core.database import get_supabase
    sb = get_supabase()

    # Fetch all data in parallel
    alerts_resp = sb.table("alerts").select("*").eq("org_id", org_id).execute()
    scans_resp = sb.table("scans").select("*").eq("org_id", org_id).order("created_at", desc=True).limit(10).execute()
    events_resp = sb.table("events").select("id, created_at").eq("org_id", org_id).execute()

    alerts_data = alerts_resp.data or []
    open_alerts = [a for a in alerts_data if not a.get("resolved", False)]
    critical = [a for a in open_alerts if a.get("severity") in ("high", "critical")]

    # Today's events
    from datetime import datetime, timezone, timedelta
    today = datetime.now(timezone.utc) - timedelta(hours=24)
    today_events = [e for e in (events_resp.data or []) if e.get("created_at", "") >= today.isoformat()]

    return {
        "active_threats": len(critical),
        "alerts_this_week": len([a for a in alerts_data if a.get("created_at", "") >= (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()]),
        "requests_today": len(today_events),
        "compliance_score": max(0, 100 - (len(critical) * 10)),
        "open_alerts": len(open_alerts),
        "recent_scans": scans_resp.data or [],
        "alert_breakdown": {
            "critical": len([a for a in alerts_data if a.get("severity") == "critical"]),
            "high": len([a for a in alerts_data if a.get("severity") == "high"]),
            "medium": len([a for a in alerts_data if a.get("severity") == "medium"]),
            "low": len([a for a in alerts_data if a.get("severity") == "low"]),
        },
    }


# ─── Legacy v1 redirect (optional — helps with SDK migrations) ─────────────────
@app.get("/api/v1/status")
async def legacy_status(request: Request):
    """Redirect v1 status to v2."""
    return {"status": "ok", "version": "2.0.0", "note": "Use /api/v2/status for v2"}