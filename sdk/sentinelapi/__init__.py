"""
SentinelAPI SDK — One line to monitor your API.
"""
from .client import SentinelClient
from .middleware import watch
from .scanner import scan
from .reporter import report as _report

# Alias so users do sentinelapi.report()
report = _report

__version__ = "0.1.0"

__all__ = ["watch", "scan", "report", "SentinelClient"]