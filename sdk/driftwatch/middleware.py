"""
ASGI/WSGI middleware for FastAPI, Flask, Django.
Usage: driftwatch.watch(app)
"""
import asyncio
import os
import time
import uuid
from collections import deque
from typing import Callable

import httpx


# ─── Anomaly scoring helpers ────────────────────────────────────────────────

def _compute_anomaly_score(method: str, path: str, status_code: int, latency_ms: float) -> float:
    """Compute anomaly score 0.0–5.0 based on heuristics."""
    score = 0.0

    # High latency
    if latency_ms > 3000:
        score += 1.0
    elif latency_ms > 1000:
        score += 0.5

    # Server errors
    if status_code >= 500:
        score += 2.0
    elif status_code >= 400:
        score += 0.5

    # Rate limiting
    if status_code == 429:
        score += 1.5

    # Unusual HTTP methods
    unusual = {"TRACE", "CONNECT", "OPTIONS"}
    if method.upper() in unusual:
        score += 1.0

    # Paths that smell like probing
    probing_paths = {
        "/.env", "/.git/config", "/admin", "/wp-admin",
        "/wp-login", "/xmlrpc.php", "/phpmyadmin", "/console",
        "/api/.git", "/.aws", "/config", "/backup", "/.htaccess",
    }
    if path.lower() in probing_paths:
        score += 2.0
    elif any(p in path.lower() for p in probing_paths):
        score += 0.5

    return min(score, 5.0)


def _build_event(scope: dict, status_code: int, latency_ms: float, org_id: str | None = None) -> dict:
    """Extract request metadata from an ASGI scope dict."""
    headers = {}
    for k, v in scope.get("headers", []):
        headers[k.decode()] = v.decode()

    # Extract client IP
    client = scope.get("client")
    ip = "unknown"
    if client:
        ip = client[0] if isinstance(client, (list, tuple)) else str(client)

    # Extract org_id from auth header if not provided
    auth_header = headers.get("authorization", headers.get("authorization", ""))
    if not org_id:
        if auth_header.startswith("Bearer "):
            # Try to decode JWT payload (unverified, just for org_id extraction)
            import base64, json
            try:
                parts = auth_header[7:].split(".")
                if len(parts) >= 2:
                    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
                    org_id = payload.get("org_id") or payload.get("organization_id")
            except Exception:
                pass
        # Fallback: use x-sentinel-org-id header
        org_id = headers.get("x-sentinel-org-id")

    return {
        "org_id": org_id or "unknown",
        "method": scope.get("method", "GET"),
        "path": scope.get("path", "/"),
        "status_code": status_code,
        "latency_ms": int(latency_ms),
        "ip": ip,
        "user_agent": headers.get("user-agent", "unknown"),
        "anomaly_score": _compute_anomaly_score(
            scope.get("method", "GET"),
            scope.get("path", "/"),
            status_code,
            latency_ms,
        ),
    }


# ─── Event queue & background flush ────────────────────────────────────────

class _EventQueue:
    """Thread-safe async queue that batches events and flushes to SentinelAPI."""

    def __init__(self, api_key: str, base_url: str, flush_interval: float = 5.0):
        self.api_key = api_key
        self.base_url = base_url
        self.flush_interval = flush_interval
        self._queue: deque[dict] = deque()
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task[None] | None = None
        self._started = False

    def enqueue(self, event: dict) -> None:
        """Add an event to the batch queue (thread-safe)."""
        import threading
        # Called from async middleware, but enqueue is safe
        self._queue.append(event)
        # Trigger flush if batch reaches 100 events
        if len(self._queue) >= 100:
            asyncio.create_task(self._flush())

    async def start(self) -> None:
        """Start the background flush loop."""
        if self._started:
            return
        self._started = True
        self._flush_task = asyncio.create_task(self._flush_loop())

    async def _flush_loop(self) -> None:
        """Flush queued events every flush_interval seconds."""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush()

    async def _flush(self) -> None:
        """Flush all queued events to Driftwatch."""
        async with self._lock:
            if not self._queue:
                return
            events = list(self._queue)
            self._queue.clear()

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/api/v2/events/batch",
                    json={"events": events},
                    headers={"x-driftwatch-api-key": self.api_key},
                    timeout=10.0,
                )
        except Exception:
            # Silently re-queue on failure to avoid flooding
            async with self._lock:
                self._queue.extendleft(reversed(events))

    async def stop(self) -> None:
        """Flush remaining events and stop the flush loop."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                self._flush_task.cancelled()
            except asyncio.CancelledError:
                pass
        await self._flush()


# ─── Driftwatch Middleware ───────────────────────────────────────────────────

class DriftwatchMiddleware:
    """ASGI middleware that instruments all HTTP requests and sends to Driftwatch."""

    def __init__(
        self,
        app,
        api_key: str | None = None,
        org_id: str | None = None,
        base_url: str = "https://api.driftwatch.io",
        flush_interval: float = 5.0,
    ):
        self.app = app
        self.api_key = api_key or os.getenv("DRIFTWATCH_API_KEY")
        self.org_id = org_id or os.getenv("DRIFTWATCH_ORG_ID")
        self.base_url = base_url
        self._queue = _EventQueue(self.api_key, self.base_url, flush_interval)

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Process an HTTP request, compute metrics, and enqueue an event."""
        if scope["type"] not in ("http", "https"):
            await self.app(scope, receive, send)
            return

        # Start queue flush loop on first request
        await self._queue.start()

        start_time = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        await self.app(scope, receive, send_wrapper)

        latency_ms = (time.perf_counter() - start_time) * 1000

        event = _build_event(scope, status_code, latency_ms, self.org_id)
        self._queue.enqueue(event)


def watch(
    app,
    api_key: str | None = None,
    org_id: str | None = None,
    base_url: str = "https://api.driftwatch.io",
    flush_interval: float = 5.0,
) -> None:
    """
    Driftwatch monitoring middleware.

    Wraps a FastAPI/Starlette app and intercepts all requests, sending
    request metadata + anomaly scoring to the Driftwatch cloud in batches.

    Args:
        app: FastAPI, Starlette, or any ASGI-compatible app.
        api_key: Your Driftwatch API key. Falls back to DRIFTWATCH_API_KEY env var.
        org_id: Organization ID for this deployment. Falls back to DRIFTWATCH_ORG_ID env var.
        base_url: API base URL. Defaults to https://api.driftwatch.io.
        flush_interval: Seconds between batch flushes. Default 5.

    Usage:
        from fastapi import FastAPI
        import driftwatch

        app = FastAPI()
        driftwatch.watch(app, api_key="dw_live_...")

        # Django (in settings.py MIDDLEWARE)
        driftwatch.watch(app, api_key="dw_live_...")

        # Flask via Werkzeug
        driftwatch.watch(app, api_key="dw_live_...")
    """
    key = api_key or os.getenv("DRIFTWATCH_API_KEY")
    if not key:
        raise ValueError(
            "Driftwatch API key required. Set DRIFTWATCH_API_KEY env var or pass api_key."
        )

    from starlette.applications import Starlette
    if isinstance(app, Starlette):
        app.add_middleware(
            DriftwatchMiddleware,
            api_key=key,
            org_id=org_id,
            base_url=base_url,
            flush_interval=flush_interval,
        )
    else:
        # Generic ASGI app — apply middleware directly
        if hasattr(app, "add_middleware"):
            app.add_middleware(DriftwatchMiddleware, api_key=key, org_id=org_id, base_url=base_url, flush_interval=flush_interval)
