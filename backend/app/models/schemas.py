"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Events ---


class EventCreate(BaseModel):
    endpoint_id: str
    method: str
    path: str
    status_code: int
    latency_ms: int
    ip: str
    user_agent: str
    anomaly_score: float = 0.0


class EventResponse(BaseModel):
    id: str
    org_id: str
    endpoint_id: str
    method: str
    path: str
    status_code: int
    latency_ms: int
    ip: str
    user_agent: str
    anomaly_score: float
    created_at: datetime


# --- Alerts ---


class AlertCreate(BaseModel):
    severity: str  # low, medium, high, critical
    type: str  # anomaly, port, credential, rate_limit
    title: str
    description: Optional[str] = None
    remediation: Optional[str] = None


class AlertResponse(BaseModel):
    id: str
    org_id: str
    severity: str
    type: str
    title: str
    description: Optional[str]
    remediation: Optional[str]
    resolved: bool
    created_at: datetime


# --- Scans ---


class ScanCreate(BaseModel):
    target: str


class ScanResponse(BaseModel):
    id: str
    org_id: str
    target: str
    open_ports: list[dict]
    risks: list[dict]
    created_at: datetime


# --- Endpoints (monitored APIs) ---


class EndpointCreate(BaseModel):
    name: str
    url: str


class EndpointResponse(BaseModel):
    id: str
    org_id: str
    name: str
    url: str
    active: bool
    created_at: datetime


# --- Reports ---


class ReportGenerate(BaseModel):
    type: str  # soc2, gdpr, iso27001


class ReportResponse(BaseModel):
    id: str
    org_id: str
    type: str
    content: str
    created_at: datetime


# --- Billing ---


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_end: datetime
