"""
Events routes — receive telemetry from Python and Node.js SDKs.
Supports both x-driftwatch-api-key (v2) and x-sentinel-api-key (legacy) headers.
"""
from fastapi import APIRouter, Request, Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import EventCreate
from app.core.database import get_supabase
from app.core.auth import verify_sdk_key
from app.core.ratelimit import limiter

router = APIRouter()


def resolve_org(key: str | None) -> str:
    """
    Resolve org_id from an SDK key.
    Uses the verify_sdk_key helper which validates against the api_keys table.
    Returns 'demo-org' if no key provided (for local dev without credentials).
    """
    if not key:
        return "demo-org"
    org_id = verify_sdk_key(key)
    return org_id or "demo-org"


@router.post("/")
@limiter.limit("200/minute")
async def ingest_event(
    request: Request,
    event: EventCreate,
    x_driftwatch_api_key: str | None = Header(None, alias="x-driftwatch-api-key"),
    x_sentinel_api_key: str | None = Header(None, alias="x-sentinel-api-key"),
    x_api_key: str | None = Header(None, alias="x-api-key"),
):
    """
    SDK calls this to ingest a single API event.
    Accepts any of: x-driftwatch-api-key, x-sentinel-api-key, x-api-key
    """
    # Support all SDK key header variants
    key = x_driftwatch_api_key or x_sentinel_api_key or x_api_key
    org_id = resolve_org(key)

    sb = get_supabase()
    data = {**event.model_dump(), "org_id": org_id}
    result = sb.table("events").insert(data).execute()
    return {"id": result.data[0]["id"]}


@router.post("/batch")
@limiter.limit("100/minute")
async def ingest_batch(
    request: Request,
    x_driftwatch_api_key: str | None = Header(None, alias="x-driftwatch-api-key"),
    x_sentinel_api_key: str | None = Header(None, alias="x-sentinel-api-key"),
    x_api_key: str | None = Header(None, alias="x-api-key"),
):
    """
    Batch event ingestion — SDK sends batches every 5s for performance.
    Accepts up to 100 events per batch.
    Body: { "events": [...] }
    """
    body = await request.json()
    events = body.get("events", [])
    if not events:
        raise HTTPException(status_code=400, detail="No events provided")
    if len(events) > 100:
        raise HTTPException(status_code=400, detail="Max 100 events per batch")

    key = x_driftwatch_api_key or x_sentinel_api_key or x_api_key
    org_id = resolve_org(key)

    sb = get_supabase()
    records = [{**e, "org_id": org_id} for e in events]
    result = sb.table("events").insert(records).execute()
    return {"inserted": len(result.data)}


@router.get("/{org_id}")
async def list_events(org_id: str, limit: int = 100, offset: int = 0):
    """List recent events for an org. Supports pagination."""
    sb = get_supabase()
    result = (
        sb.table("events")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
        .execute()
    )
    return {
        "events": result.data,
        "count": len(result.data),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{org_id}/summary")
async def event_summary(org_id: str):
    """
    Aggregate event stats for an org — used by the dashboard.
    Returns hourly breakdowns for the last 24h.
    """
    from datetime import datetime, timezone, timedelta

    sb = get_supabase()
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    result = sb.table("events").select(
        "status_code, latency_ms, anomaly_score, created_at"
    ).eq("org_id", org_id).gte("created_at", since.isoformat()).execute()

    events = result.data or []
    total = len(events)
    errors = sum(1 for e in events if (e.get("status_code") or 0) >= 500)
    anomaly_high = sum(1 for e in events if (e.get("anomaly_score") or 0) > 2.0)
    avg_latency = sum((e.get("latency_ms") or 0) for e in events) / max(total, 1)

    return {
        "total_requests": total,
        "errors": errors,
        "high_anomaly_events": anomaly_high,
        "avg_latency_ms": round(avg_latency, 1),
        "error_rate": round(errors / max(total, 1) * 100, 2),
        "period": "24h",
    }