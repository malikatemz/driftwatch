"""
Rate limiting configuration for Driftwatch API.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Per-IP rate limiter for public endpoints
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# Per-org rate limiter (used for authenticated endpoints)
# Usage: add @limiter.limit("100/minute", key_func=lambda: org_id)
