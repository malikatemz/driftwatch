"""
Scans routes.
"""
from fastapi import APIRouter, BackgroundTasks
from app.models.schemas import ScanCreate, ScanResponse
from app.core.database import get_supabase
from app.services.port_scanner import run_scan

router = APIRouter()


@router.get("/{org_id}")
async def list_scans(org_id: str, limit: int = 20):
    sb = get_supabase()
    result = (
        sb.table("scans")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


@router.post("/{org_id}/run", include_in_schema=False)
async def trigger_scan(org_id: str, scan: ScanCreate, background_tasks: BackgroundTasks):
    """
    Trigger a port scan in the background.
    Returns immediately — scan runs async.
    """
    sb = get_supabase()

    # Create pending scan record
    result = sb.table("scans").insert({
        "org_id": org_id,
        "target": scan.target,
        "open_ports": [],
        "risks": [],
    }).execute()
    scan_id = result.data[0]["id"]

    # Run scan in background
    background_tasks.add_task(run_scan, org_id, scan_id, scan.target)

    return {"scan_id": scan_id, "status": "running"}
