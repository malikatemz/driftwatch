"""
SentinelAPI Backend - FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routes import events, alerts, scans, reports, webhooks, billing

app = FastAPI(
    title="SentinelAPI",
    description="Security monitoring for developer APIs",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://sentinelapi.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(scans.router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/v1/org/{org_id}/dashboard")
async def dashboard(org_id: str):
    """Main dashboard data endpoint."""
    return {
        "active_threats": 0,
        "alerts_this_week": 0,
        "requests_today": 0,
        "compliance_score": 100,
    }
