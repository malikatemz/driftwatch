"""
SentinelAPI client for manual event ingestion.
"""
import asyncio
import httpx
import os


class SentinelClient:
    """Manual event ingestion client for SentinelAPI.

    Args:
        api_key: Your SentinelAPI key. Falls back to SENTINEL_API_KEY env var.
        base_url: API base URL. Defaults to https://api.sentinelapi.io.
    """

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.sentinelapi.io"):
        self.api_key = api_key or os.getenv("SENTINEL_API_KEY")
        self.base_url = base_url
        if not self.api_key:
            raise ValueError("SentinelAPI API key required. Set SENTINEL_API_KEY env var or pass api_key.")
        self._client = httpx.AsyncClient(
            headers={"x-sentinel-api-key": self.api_key},
            timeout=30.0,
        )

    async def send_event(self, event: dict) -> dict:
        """Send a single security event.

        Args:
            event: Event dict with keys like method, path, status_code, latency_ms, ip, user_agent, anomaly_score.
        Returns:
            Response JSON dict.
        """
        resp = await self._client.post(f"{self.base_url}/api/v1/events/", json=event)
        resp.raise_for_status()
        return resp.json()

    async def send_batch(self, events: list[dict]) -> dict:
        """Send a batch of security events.

        Args:
            events: List of event dicts.
        Returns:
            Response JSON dict.
        """
        resp = await self._client.post(f"{self.base_url}/api/v1/events/batch", json={"events": events})
        resp.raise_for_status()
        return resp.json()

    async def get_alerts(self, org_id: str, resolved: bool | None = None) -> dict:
        """Fetch alerts for an organization.

        Args:
            org_id: Organization ID.
            resolved: Filter by resolved status.
        Returns:
            Response JSON dict.
        """
        params = {}
        if resolved is not None:
            params["resolved"] = str(resolved).lower()
        resp = await self._client.get(f"{self.base_url}/api/v1/alerts/{org_id}", params=params)
        resp.raise_for_status()
        return resp.json()

    async def trigger_scan(self, org_id: str, target: str) -> dict:
        """Trigger a remote scan for a target.

        Args:
            org_id: Organization ID.
            target: Target URL or hostname to scan.
        Returns:
            Response JSON dict with scan status.
        """
        resp = await self._client.post(
            f"{self.base_url}/api/v1/scans/{org_id}/run",
            json={"target": target},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_reports(self, org_id: str) -> dict:
        """Fetch compliance reports for an organization.

        Args:
            org_id: Organization ID.
        Returns:
            Response JSON dict with reports list.
        """
        resp = await self._client.get(f"{self.base_url}/api/v1/reports/{org_id}")
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "SentinelClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    def __enter__(self) -> "SentinelClient":
        return self

    def __exit__(self, *args) -> None:
        # For sync context manager, schedule async close
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(self.close())
        else:
            try:
                asyncio.run(self.close())
            except RuntimeError:
                pass
