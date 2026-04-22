"""
Alerts routes.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import AlertCreate, AlertResponse
from app.core.database import get_supabase
from app.services.alert_engine import AlertEngine

router = APIRouter()
alert_engine = AlertEngine()


@router.get("/{org_id}")
async def list_alerts(org_id: str, resolved: bool | None = None):
    sb = get_supabase()
    query = sb.table("alerts").select("*").eq("org_id", org_id)
    if resolved is not None:
        query = query.eq("resolved", resolved)
    result = query.order("created_at", desc=True).execute()
    return result.data


@router.get("/{org_id}/{alert_id}")
async def get_alert(org_id: str, alert_id: str):
    sb = get_supabase()
    result = (
        sb.table("alerts")
        .select("*")
        .eq("org_id", org_id)
        .eq("id", alert_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result.data[0]


@router.post("/{org_id}/{alert_id}/resolve")
async def resolve_alert(org_id: str, alert_id: str):
    sb = get_supabase()
    sb.table("alerts").update({"resolved": True}).eq("id", alert_id).execute()
    return {"status": "resolved"}


@router.post("/create")
async def create_alert(alert: AlertCreate, org_id: str):
    """Used internally by alert engine or tests."""
    sb = get_supabase()
    data = {**alert.model_dump(), "org_id": org_id, "resolved": False}
    result = sb.table("alerts").insert(data).execute()
    return {"id": result.data[0]["id"]}
