"""
Driftwatch SDK — One line to monitor your API.
"""
from .client import DriftwatchClient
from .middleware import watch
from .scanner import scan
from .reporter import report as _report
import os
import asyncio

# Alias so users do driftwatch.report()
report = _report

def health(api_key: str | None = None, base_url: str = "https://api.driftwatch.io") -> dict:
    """Check API health and auth status."""
    async def _check():
        async with DriftwatchClient(api_key=api_key, base_url=base_url) as client:
            return await client.health()

    try:
        loop = asyncio.get_running_loop()
        # If we are already in an event loop, we can't use run_until_complete
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
        return loop.run_until_complete(_check())
    except RuntimeError:
        # No event loop — create a new one
        return asyncio.run(_check())

def shutdown():
    """No-op for compatibility with other SDKs; middleware handles its own cleanup."""
    pass

__version__ = "0.1.0"

__all__ = ["watch", "scan", "report", "health", "shutdown", "DriftwatchClient"]