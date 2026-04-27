"""
SentinelAPI Configuration
All environment variables for the backend.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SentinelAPI"
    DEBUG: bool = Field(default=False)
    API_VERSION: str = "v1"

    # Supabase
    SUPABASE_URL: str = Field(default="")
    SUPABASE_ANON_KEY: str = Field(default="")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")

    # Clerk Auth
    CLERK_PUBLISHABLE_KEY: str = Field(default="")
    CLERK_SECRET_KEY: str = Field(default="")
    CLERK_WEBHOOK_SECRET: str = Field(default="")  # Svix signing secret from Clerk dashboard

    # Stripe
    STRIPE_PUBLISHABLE_KEY: str = Field(default="")
    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")

    # Stripe Price IDs (create these in Stripe dashboard)
    STRIPE_PRICE_STARTER: str = Field(default="price_starter")
    STRIPE_PRICE_PRO: str = Field(default="price_pro")
    STRIPE_PRICE_ENTERPRISE: str = Field(default="price_enterprise")

    # SendGrid
    SENDGRID_API_KEY: str = Field(default="")
    SENDGRID_FROM_EMAIL: str = "alerts@sentinelapi.io"

    # Claude API
    ANTHROPIC_API_KEY: str = Field(default="")
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Redis / Queue (for async event ingestion)
    REDIS_URL: str = Field(default="redis://localhost:6379")

    # SentinelAPI SDK endpoints
    SDK_SECRET_KEY: str = Field(default="")  # For SDK auth

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
