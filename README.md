# Driftwatch

**Continuous API Security for Modern Engineering Teams**

Driftwatch continuously monitors your APIs for attacks, exposed infrastructure, leaked credentials, and compliance risks—all through a single SDK and developer-friendly dashboard.

## Features

### Real-time API Monitoring
* Request logging
* Behavioral anomaly detection
* Attack pattern detection
* Rate anomaly detection
* Live dashboard
* Historical analytics

### Credential Scanner
* GitHub scanning
* GitLab scanning
* Bitbucket support
* CI/CD secret detection
* Environment variable auditing

### Compliance
* SOC 2 evidence generation
* ISO 27001 control mapping
* GDPR security summaries
* Downloadable PDF reports

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

driftwatch.watch(
    app,
    api_key="dw_live_xxx",
)
```

### Supported Frameworks
✓ FastAPI
✓ Django
✓ Flask
✓ Starlette
✓ Quart
✓ Falcon
✓ Sanic

**Coming Soon:** Node.js, Express, NestJS, Go, Rust, Java, .NET

## Detection Capabilities
Detects:
* SQL Injection
* XSS
* SSRF
* RCE attempts
* JWT abuse
* API key abuse
* Credential stuffing
* Rate-limit bypass
* Prompt injection
* Token replay
* Bot traffic
* OWASP API Top 10

## AI Alert Triage
* Root cause analysis
* Attack explanation
* Risk scoring
* False-positive reduction
* Suggested remediation
* Auto-generated incident summaries

## Architecture

```
driftwatch/
├── backend/           FastAPI — events, alerts, scans, reports, billing
│   └── app/
│       ├── routes/    API endpoints
│       ├── models/    Pydantic schemas
│       ├── services/
│       │   ├── anomaly_engine.py
│       │   ├── port_scanner.py
│       │   ├── secrets_scanner.py
│       │   ├── ai_triage.py
│       │   └── compliance.py
│       └── core/      config, auth, database
├── frontend/          Next.js 15 — dashboard, alerts, scanner, reports
├── sdk/               Python SDK — middleware, scanner, reporter, CLI
└── supabase/          Postgres schema, RLS policies, Edge Functions
```

## Security & Privacy
* TLS 1.3 everywhere
* Row-Level Security
* Signed SDK events
* API key rotation
* Audit logging
* Optional end-to-end encryption
* Regional data residency

## API Reference

```
POST /api/v2/events       - Ingest event
POST /api/v2/events/batch - Batch ingestion
GET  /api/v2/alerts       - List alerts
POST /api/v2/scans        - Trigger scan
GET  /api/v2/reports      - Fetch reports
```

## CLI

```bash
# Scan a target
driftwatch scan api.yoursite.com

# Generate a report
driftwatch report my-org-id soc2

# Check credentials
driftwatch init dw_live_...
```

## Comparison

| Driftwatch         | Typical API Gateway |
| ------------------ | ------------------- |
| Threat detection   | Basic logging       |
| AI alert triage    | None                |
| Compliance reports | Manual              |
| Secret scanning    | No                  |
| Port scanning      | No                  |
| SDK integration    | Limited             |

## Pricing

| Plan       |  Price |
| ---------- | -----: |
| Starter    |    $49 |
| Growth     |   $149 |
| Business   |   $499 |
| Enterprise | Custom |

## Setup

### 1. Supabase
Create a project at [supabase.com](https://supabase.com), then run the schema:
```bash
# Apply the full schema (tables, RLS, triggers)
supabase db push --project-ref YOUR_PROJECT_REF
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
- **Backend** → Railway or Render
- **Frontend** → Vercel

## Roadmap
✓ Python SDK
✓ Dashboard
✓ Port Scanner
✓ Compliance
✓ Secret Scanner
• Node SDK
• Kubernetes Agent
• AWS Integration
• Azure Integration
• GCP Integration
• Terraform Provider
• OpenAPI Scanner
• Runtime AI Copilot

## License
Proprietary — All rights reserved.
