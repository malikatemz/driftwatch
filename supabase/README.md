# SentinelAPI - Supabase Setup

## Overview

This directory contains the Supabase schema and Edge Functions for SentinelAPI's multi-tenant API security monitoring platform.

## Quick Start

### 1. Create a Supabase Project

```bash
# Install Supabase CLI if you haven't
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
cd supabase
supabase link --project-ref your-project-ref
```

### 2. Push the Schema

**Option A: Using Supabase CLI (recommended)**
```bash
supabase db push
```

**Option B: Using SQL Editor**
1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of `schema.sql`
4. Paste and run

### 3. Enable Row Level Security

RLS is enabled in the schema.sql, but verify in the Supabase dashboard:

1. Go to **Table Editor** in your Supabase project
2. Select any table → **Policies**
3. Verify RLS is enabled (green toggle)

### 4. Configure Environment Variables

```bash
cp .env.example .env.local
```

Fill in your actual values:
- `SUPABASE_URL` - Found in Supabase dashboard → Settings → API
- `SUPABASE_ANON_KEY` - Found in Supabase dashboard → Settings → API
- `SUPABASE_SERVICE_ROLE_KEY` - Found in Supabase dashboard → Settings → API (keep secret!)
- `STRIPE_SECRET_KEY` - From Stripe Dashboard → Developers → API Keys
- `STRIPE_WEBHOOK_SECRET` - From Stripe Dashboard → Developers → Webhooks
- `CLERK_SECRET_KEY` - From Clerk Dashboard → API Keys
- `ANTHROPIC_API_KEY` - From Anthropic Console

### 5. Deploy Edge Functions

```bash
# Deploy all functions
supabase functions deploy create-org
supabase functions deploy verify-sdk-key

# Or deploy all at once (if using a supabase/functions directory structure)
supabase functions deploy
```

### 6. Set up Clerk Webhook

1. In Clerk Dashboard → Webhooks
2. Add Endpoint: `https://your-project.supabase.co/functions/v1/create-org`
3. Subscribe to: `user.created`
4. Copy the signing secret to `CLERK_WEBHOOK_SECRET` in `.env`

### 7. Create Stripe Products/Prices

In Stripe Dashboard:

1. Create products for each plan:
   - **Starter** - $49/mo
   - **Pro** - $149/mo
   - **Enterprise** - $299/mo

2. Note the Price IDs and configure in your app's billing flow

### 8. Configure Stripe Webhooks

1. In Stripe Dashboard → Webhooks
2. Add endpoint: `https://your-project.supabase.co/stripe-webhook` (create this function)
3. Subscribe to events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

---

## Schema Tables

| Table | Description |
|-------|-------------|
| `organizations` | Customer tenants with plan/billing info |
| `users` | Users linked to orgs via Clerk auth |
| `api_keys` | SDK authentication keys |
| `endpoints` | Monitored API endpoints |
| `events` | Ingested request data (high-volume) |
| `alerts` | Threat detections |
| `scans` | Port/vulnerability scan results |
| `reports` | Compliance reports (SOC2, GDPR, ISO27001) |
| `webhook_configs` | Alert delivery integrations |
| `audit_log` | Immutable action audit trail |

## Edge Functions

### `create-org`
- **Trigger**: Clerk `user.created` webhook
- **Action**: Creates organization + first API key
- **Returns**: org_id, plaintext API key (one time only)

### `verify-sdk-key`
- **Trigger**: SDK requests with `Authorization: Bearer sk_live_...`
- **Action**: Validates key, updates `last_used_at`, logs to audit
- **Returns**: `{ valid: true, org_id: "..." }`

## Security

- **Row Level Security (RLS)** enabled on all tables
- **Organization isolation** via `org_id` in every table
- **API keys** stored as hashed values (never plaintext)
- **Audit log** is immutable (no UPDATE/DELETE allowed)
- **Service role key** should only be used in server-side Edge Functions

## Environment Variables Reference

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Public anon key (safe for client) |
| `SUPABASE_SERVICE_ROLE_KEY` | Secret service role key (server only) |
| `STRIPE_SECRET_KEY` | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `CLERK_SECRET_KEY` | Clerk API secret key |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |

## Troubleshooting

### "Relation does not exist"
- Run the migration: `supabase db push`
- Or execute `schema.sql` in SQL Editor

### RLS policy errors
- Check that the user has an org_id that matches the data
- Verify JWT claims include the user ID

### Edge Function deployment fails
- Ensure you're logged in: `supabase login`
- Check function syntax and dependencies

---

## Development

```bash
# Start local Supabase
supabase start

# Apply local changes
supabase db reset

# Test Edge Functions locally
supabase functions serve create-org
```
