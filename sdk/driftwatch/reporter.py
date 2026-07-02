"""
Compliance report generator.
Usage: driftwatch.report(org_id, api_key, "soc2")
"""
import asyncio
import os
import time
from typing import Literal

import httpx


ReportType = Literal["soc2", "gdpr", "iso27001"]


async def _poll_report(
    client: httpx.AsyncClient,
    report_url: str,
    headers: dict,
    max_wait: float = 30.0,
    poll_interval: float = 2.0,
) -> dict:
    """Poll a report URL until status is 'ready' or timeout."""
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        resp = await client.get(report_url, headers=headers, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "ready" or "content" in data:
            return data
        await asyncio.sleep(poll_interval)
    raise TimeoutError(f"Report did not complete within {max_wait}s")


async def _fetch_latest_report(
    org_id: str,
    api_key: str,
    base_url: str,
    report_type: ReportType,
) -> dict:
    """Fetch the latest report for org_id, triggering generation if none exists."""
    headers = {"x-driftwatch-api-key": api_key}
    async with httpx.AsyncClient() as client:
        # Try fetching existing reports
        resp = await client.get(
            f"{base_url}/api/v2/reports/{org_id}",
            headers=headers,
            timeout=10.0,
        )
        resp.raise_for_status()
        reports = resp.json()

        # Find a ready report of the requested type
        for r in reports if isinstance(reports, list) else reports.get("reports", []):
            if r.get("type", "").lower() == report_type.lower() and r.get("status") == "ready":
                return r

        # No ready report — trigger generation
        gen_resp = await client.post(
            f"{base_url}/api/v2/reports/{org_id}/generate",
            json={"type": report_type},
            headers=headers,
            timeout=10.0,
        )
        gen_resp.raise_for_status()
        gen_data = gen_resp.json()

        report_url = gen_data.get("url") or f"{base_url}/api/v2/reports/{org_id}/{gen_data.get('id', '')}"
        return await _poll_report(client, report_url, headers)


def report(
    org_id: str,
    api_key: str | None = None,
    report_type: ReportType = "soc2",
    base_url: str = "https://api.driftwatch.io",
    timeout: float = 30.0,
) -> str:
    """
    Generate a compliance report and return its content as a string.

    Args:
        org_id: Your Driftwatch organization ID.
        api_key: Your Driftwatch API key. Falls back to DRIFTWATCH_API_KEY env var.
        report_type: One of "soc2", "gdpr", "iso27001". Defaults to "soc2".
        base_url: Driftwatch API base URL.
        timeout: Max time to wait for report generation. Default 30s.

    Returns:
        The report content as a string (HTML, Markdown, or JSON).

    Raises:
        ValueError: Missing API key.
        TimeoutError: Report did not complete within timeout.
        httpx.HTTPStatusError: API request failed.
    """
    key = api_key or os.getenv("DRIFTWATCH_API_KEY")
    if not key:
        raise ValueError(
            "Driftwatch API key required. Set DRIFTWATCH_API_KEY env var or pass api_key."
        )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop — create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                _fetch_latest_report(org_id, key, base_url, report_type)
            ).get("content", "")
        finally:
            loop.close()

    # Running loop exists — schedule the coroutine via threadsafe API
    future = asyncio.run_coroutine_threadsafe(
        _fetch_latest_report(org_id, key, base_url, report_type),
        loop,
    )
    result = future.result(timeout=timeout)
    return result.get("content", "")


async def _generate_report_async(
    org_id: str,
    api_key: str,
    report_type: ReportType,
    base_url: str,
) -> dict:
    """Async version — returns full dict for use with DriftwatchClient."""
    headers = {"x-driftwatch-api-key": api_key}
    async with httpx.AsyncClient() as client:
        # Check for existing ready report
        resp = await client.get(f"{base_url}/api/v2/reports/{org_id}", headers=headers, timeout=10.0)
        resp.raise_for_status()
        reports = resp.json()
        for r in reports if isinstance(reports, list) else reports.get("reports", []):
            if r.get("type", "").lower() == report_type.lower() and r.get("status") == "ready":
                return r

        # Trigger generation
        gen_resp = await client.post(
            f"{base_url}/api/v2/reports/{org_id}/generate",
            json={"type": report_type},
            headers=headers,
            timeout=10.0,
        )
        gen_resp.raise_for_status()
        gen_data = gen_resp.json()

        report_url = gen_data.get("url") or (
            f"{base_url}/api/v2/reports/{org_id}/{gen_data.get('id', '')}"
        )
        return await _poll_report(client, report_url, headers)


__all__ = ["report"]
