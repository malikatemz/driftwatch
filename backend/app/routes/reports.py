"""
Reports routes — AI-generated compliance reports.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import ReportGenerate, ReportResponse
from app.core.database import get_supabase
from app.services.compliance import generate_compliance_report

router = APIRouter()


@router.get("/{org_id}")
async def list_reports(org_id: str, limit: int = 20):
    sb = get_supabase()
    result = (
        sb.table("reports")
        .select("*")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


@router.post("/{org_id}/generate", include_in_schema=False)
async def create_report(org_id: str, report_type: ReportGenerate):
    """
    Generate a compliance report using Claude.
    This is an async job — returns immediately with a pending status.
    """
    sb = get_supabase()

    # Create pending report record
    result = sb.table("reports").insert({
        "org_id": org_id,
        "type": report_type.type,
        "content": "Generating...",
    }).execute()
    report_id = result.data[0]["id"]

    # Generate asynchronously
    try:
        content = await generate_compliance_report(org_id, report_type.type)
        sb.table("reports").update({"content": content}).eq("id", report_id).execute()
    except Exception as e:
        sb.table("reports").update({"content": f"Error generating report: {e}"}).eq("id", report_id).execute()

    return {"report_id": report_id, "status": "ready"}
