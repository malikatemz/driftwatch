# SentinelAPI

**Security monitoring for developer APIs — one line of code to get started.**

SentinelAPI monitors your APIs and infrastructure for security threats in real time, detects exposed ports, credential leaks, and anomalies, and auto-generates compliance reports — all via a one-line SDK integration.

## Quick Start

```bash
pip install sentinelapi
```

```python
import sentinelapi

# One line to start monitoring
sentinelapi.watch(app)

# Or scan manually
results = sentinelapi.scan(target="https://api.yoursite.com")
report = sentinelapi.report(type="soc2")
```

## Features

- **Real-time API monitoring** — captures all requests, detects anomalies
- **Port scanner** — continuous infrastructure scanning for exposed services
- **Credential leak detector** — watches git commits and CI/CD for secrets
- **AI alert triage** — Claude-powered analysis reduces false positives
- **Compliance reporter** — one-click SOC2/GDPR/ISO27001 audit reports

## Architecture

```
sentinelapi/
├── frontend/          # Next.js 15 dashboard
├── backend/           # FastAPI
│   └── app/
│       ├── routes/    # API endpoints
│       ├── models/    # DB models
│       ├── services/  # Business logic
│       └── core/      # Config, auth, etc.
├── sdk/               # Python SDK
└── supabase/          # DB schema
```

## Tech Stack

- **Backend:** FastAPI + Python
- **Database:** Supabase (Postgres + Realtime)
- **Auth:** Clerk
- **Frontend:** Next.js 15 + Tailwind
- **Payments:** Stripe
- **AI:** Claude API
- **Emails:** SendGrid
- **Deployment:** Vercel + Railway

## Pricing

| Tier | Price | Limits |
|------|-------|--------|
| Starter | $49/mo | 3 endpoints, 100K req/mo |
| Pro | $149/mo | 20 endpoints, 5M req/mo |
| Enterprise | $299/mo | Unlimited, SLA, custom reports |

## License

Proprietary — All rights reserved.
