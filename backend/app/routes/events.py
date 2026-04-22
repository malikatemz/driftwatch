"""
Events routes — receive telemetry from the SDK.
"""
from fastapi import APIRouter, Request, Header, HTTPException
from app.models.schemas import EventCreate, EventResponse
from app.core.database import get_supabase

router = APIRouter()


def resolve_org_from_key(x_sentinel_api_key: str) -> str:
    """Resolve org_id from SDK API key. Returns 'demo-org' if not found."""
    if not x_sentinel_api_key:
        return "demo-org"
    # In production: query api_keys table, join to organizations
    # For prototype: use key prefix as org_id marker
    return "demo-org"


@router.post("/")
async def ingest_event(
    event: EventCreate,
    x_sentinel_api_key: str | None = Header(None, alias="x-sentinel-api-key"),
):
    """
    SDK calls this to ingest a single API event.
    For high-volume, the SDK batches events and sends them here.
    """
    sb = get_supabase()
    org_id = resolve_org_from_key(x_sentinel_api_key or "")

    data = {**event.model_dump(), "org_id": org_id}
    result = sb.table("events").insert(data).execute()
    return {"id": result.data[0]["id"]}


@router.post("/batch")
async def ingest_batch(
    events: list[EventCreate],
    x_sentinel_api_key: str | None = Header(None, alias="x-sentinel-api-key"),
):
    """
    Batch event ingestion — SDK sends batches every 5s for performance.
    Accepts up to 100 events per batch.
    """
    if len(events) > 100:
        raise HTTPException(status_code=400, detail="Max 100 events per batch")

    sb = get_supabase()
    org_id = resolve_org_from_key(x_sentinel_api_key or "")

    records = [{**e.model_dump(), "org_id": org_id} for e in events]
    result = sb.table("events").insert(records).execute()
    return {"inserted": len(result.data)}


@router.get("/{org_id}")
async def list_events(org_id: str, limit: int = 100):
    """List recent events for an org."""
    sb = get_supabase()
    result = (
        sb.table("events")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data