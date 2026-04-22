# SentinelAPI SDK

One line of code to monitor your API for security threats.

## Install

```bash
pip install sentinelapi
```

Or with extras:

```bash
pip install sentinelapi[dev]
```

## Quick Start

### FastAPI

```python
from fastapi import FastAPI
import sentinelapi

app = FastAPI()

sentinelapi.watch(
    app,
    api_key="sk_live_...",   # or set SENTINEL_API_KEY env var
    org_id="org_...",        # or set SENTINEL_ORG_ID env var
)
```

All requests are instrumented automatically. Events are batched and sent to SentinelAPI every 5 seconds so there's minimal overhead.

### Django

In `settings.py`:

```python
MIDDLEWARE = [
    # ...
    "sentinelapi.middleware.SentinelAPIMiddleware",
]
```

Then add to your app config:

```python
# somewhere in startup — e.g. AppConfig.ready()
import sentinelapi, os
os.environ["SENTINEL_API_KEY"] = "sk_live_..."
os.environ["SENTINEL_ORG_ID"] = "org_..."
```

Or apply directly:

```python
import sentinelapi
sentinelapi.watch(app, api_key="sk_live_...", org_id="org_...")
```

### Flask

```python
from flask import Flask
import sentinelapi

app = Flask(__name__)
sentinelapi.watch(app, api_key="sk_live_...", org_id="org_...")
```

### Manual Scan

Scan any host for exposed ports and security risks:

```python
import sentinelapi

result = sentinelapi.scan("api.yoursite.com")
# {'target': 'api.yoursite.com', 'open_ports': [...], 'risks': [...], 'summary': '...', 'scanned_at': '...'}

for risk in result["risks"]:
    print(f"Port {risk['port']}: {risk['issue']}")
```

CLI:

```bash
sentinel scan api.yoursite.com
sentinel scan api.yoursite.com --ports 22,80,443,3306
```

### Compliance Report

Generate a compliance report for your organization:

```python
import sentinelapi

content = sentinelapi.report(
    org_id="org_...",
    api_key="sk_live_...",
    report_type="soc2",     # or "gdpr", "iso27001"
)
print(content)
```

CLI:

```bash
sentinel report org_... soc2
sentinel report org_... gdpr --api-key sk_live_...
```

### SentinelClient (Manual Event Ingestion)

For custom integrations:

```python
import asyncio
from sentinelapi import SentinelClient

async def main():
    async with SentinelClient(api_key="sk_live_...") as client:
        # Send a single event
        await client.send_event({
            "method": "GET",
            "path": "/api/users",
            "status_code": 200,
            "latency_ms": 45,
            "ip": "1.2.3.4",
            "user_agent": "my-client/1.0",
            "anomaly_score": 0.0,
        })

        # Send a batch
        await client.send_batch([{...}, {...}])

        # Fetch alerts
        alerts = await client.get_alerts("org_...", resolved=False)

        # Trigger a remote scan
        scan_result = await client.trigger_scan("org_...", target="https://api.yoursite.com")

        # Fetch reports
        reports = await client.get_reports("org_...")

asyncio.run(main())
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SENTINEL_API_KEY` | Your SentinelAPI API key | — |
| `SENTINEL_ORG_ID` | Organization ID for middleware | — |
| `SENTINEL_BASE_URL` | API base URL | `https://api.sentinelapi.io` |

## CLI

After installing, the `sentinel` command is available:

```bash
sentinel --version
sentinel init --api-key sk_live_...
sentinel scan example.com
sentinel scan example.com --ports 22,80,443,3306
sentinel report org_... soc2
sentinel report org_... gdpr --api-key sk_live_...
```

## Anomaly Scoring

The middleware computes an anomaly score (0.0–5.0) per request using these heuristics:

- **High latency** (>3s): +1.0, (>1s): +0.5
- **Server errors** (5xx): +2.0, (4xx): +0.5
- **Rate limiting** (429): +1.5
- **Unusual methods** (TRACE, CONNECT, OPTIONS): +1.0
- **Probing paths** (/.env, /wp-admin, /phpmyadmin, etc.): +2.0; partial matches: +0.5

## Architecture

```
sentinelapi.watch(app)
    └── SentinelAPIMiddleware  (ASGI)
            ├── _EventQueue    (batches events every 5s)
            │       └── httpx.AsyncClient POST /api/v1/events/batch
            └── asyncio background task
```

## License

MIT
