# Driftwatch

**API security monitoring for startups that ship.**

Real-time threat detection, port & credential scanning, and auto-generated compliance reports — via a one-line SDK integration.

## Features

- **Real-time API monitoring** — captures all requests, detects anomalies via Z-score analysis
- **Port scanner** — detects exposed ports, services, and infrastructure risks
- **Credential leak detector** — monitors git commits and CI/CD pipelines for secrets
- **AI alert triage** — Claude-powered analysis reduces false positives
- **Compliance reporter** — one-click SOC2 / GDPR / ISO 27001 audit reports

## Quick Start

### Install the SDK

```bash
pip install driftwatch
```

### FastAPI integration (one line)

```python
from fastapi import FastAPI
import driftwatch

app = FastAPI()
driftwatch.watch(app, api_key="sk_live_...", org_id="your-org-id")
```

### Django, Flask, Starlette — same pattern

```python
import driftwatch
driftwatch.watch(app, api_key="sk_live_...", org_id="your-org-id")
```

### Run a port scan

```python
import driftwatch
result = driftwatch.scan("api.yoursite.com")
# Returns: open ports, risk classification, recommendations
```

### Generate a compliance report

```python
import driftwatch
report = driftwatch.report(org_id="your-org-id", api_key="sk_live_...", report_type="soc2")
print(report)
```

### CLI

```bash
# Scan a target
sentinel scan api.yoursite.com

# Generate a report
sentinel report my-org-id soc2

# Check credentials
sentinel init sk_live_...
```

## Architecture

```
driftwatch/
├── backend/           FastAPI — events, alerts, scans, reports, billing
│   └── app/
│       ├── routes/    API endpoints
│       ├── models/    Pydantic schemas
│       ├── services/  alert engine, scanner, reporter
│       └── core/      config, auth, database
├── frontend/          Next.js 15 — dashboard, alerts, scanner, reports
├── sdk/               Python SDK — middleware, scanner, reporter, CLI
└── supabase/          Postgres schema, RLS policies, Edge Functions
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python |
| Database | Supabase (Postgres + Realtime) |
| Auth | Clerk |
| Frontend | Next.js 15 + Tailwind CSS |
| Payments | Stripe |
| AI | Claude API (Anthropic) |
| Emails | SendGrid |
| Deployment | Vercel + Railway |

## Setup

### 1. Supabase

Create a project at [supabase.com](https://supabase.com), then run the schema:

```bash
# Apply the full schema (tables, RLS, triggers)
supabase db push --project-ref YOUR_PROJECT_REF

# Or paste schema.sql directly in the Supabase SQL Editor
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Fill in your keys (Supabase, Clerk, Stripe, Anthropic)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY
npm install
npm run dev
```

### 4. Deploy

- **Backend** → Railway or Render (connect GitHub, set env vars)
- **Frontend** → Vercel (connect GitHub, auto-deploys on push)
- **SDK** → publish to PyPI (`python -m build && twine upload`)

## Pricing

| Tier | Price | Limits |
|------|-------|--------|
| Starter | $49/mo | 3 endpoints, 100K req/mo |
| Pro | $149/mo | 20 endpoints, 5M req/mo |
| Enterprise | $299/mo | Unlimited, SLA, custom reports |

## License

Proprietary — All rights reserved.