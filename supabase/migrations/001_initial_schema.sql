-- =============================================================================
-- SentinelAPI - Initial Schema Migration
-- Version: 1.0.0
-- Apply with: supabase db push or run in SQL Editor
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- ORGANIZATIONS
-- =============================================================================
CREATE TABLE IF NOT EXISTS organizations (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name          TEXT NOT NULL,
    plan          TEXT NOT NULL DEFAULT 'starter' CHECK (plan IN ('starter', 'pro', 'enterprise')),
    stripe_customer_id TEXT UNIQUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE INDEX idx_organizations_stripe_customer_id ON organizations(stripe_customer_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_organizations_plan ON organizations(plan);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- USERS
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY,
    email         TEXT NOT NULL,
    name          TEXT,
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role          TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE INDEX idx_users_org_id ON users(org_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_users_email ON users(email);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE UNIQUE INDEX idx_users_org_email ON users(org_id, email);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- API KEYS
-- =============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    key_hash      TEXT NOT NULL,
    prefix        TEXT NOT NULL,
    name          TEXT NOT NULL,
    env           TEXT NOT NULL DEFAULT 'production' CHECK (env IN ('production', 'staging', 'development')),
    last_used_at  TIMESTAMPTZ,
    expires_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at    TIMESTAMPTZ
);

DO $$ BEGIN
    CREATE INDEX idx_api_keys_org_id ON api_keys(org_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_api_keys_prefix ON api_keys(prefix);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- ENDPOINTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS endpoints (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    url           TEXT NOT NULL,
    method        TEXT NOT NULL DEFAULT 'GET' CHECK (method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD')),
    description   TEXT,
    active        BOOLEAN NOT NULL DEFAULT true,
    tags          TEXT[] DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE INDEX idx_endpoints_org_id ON endpoints(org_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_endpoints_active ON endpoints(org_id, active);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_endpoints_url ON endpoints(url);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- EVENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS events (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    endpoint_id   UUID REFERENCES endpoints(id) ON DELETE SET NULL,
    method        TEXT NOT NULL,
    path          TEXT NOT NULL,
    status_code   INTEGER,
    latency_ms    INTEGER,
    request_size  INTEGER,
    response_size INTEGER,
    ip            TEXT,
    user_agent    TEXT,
    headers       JSONB DEFAULT '{}',
    request_body  JSONB,
    response_body JSONB,
    anomaly_score REAL DEFAULT 0.0 CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
    threat_type   TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE INDEX idx_events_org_id ON events(org_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_events_endpoint_id ON events(endpoint_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_events_created_at ON events(org_id, created_at DESC);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_events_anomaly_score ON events(org_id, anomaly_score DESC) WHERE anomaly_score > 0.5;
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_events_ip ON events(org_id, ip);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_events_threat_type ON events(org_id, threat_type) WHERE threat_type IS NOT NULL;
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- ALERTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_id      UUID REFERENCES events(id) ON DELETE SET NULL,
    severity      TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    type          TEXT NOT NULL,
    title         TEXT NOT NULL,
    description   TEXT,
    remediation   TEXT,
    resolved      BOOLEAN NOT NULL DEFAULT false,
    resolved_by   UUID REFERENCES users(id),
    resolved_at   TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE INDEX idx_alerts_org_id ON alerts(org_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_alerts_severity ON alerts(org_id, severity);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_alerts_resolved ON alerts(org_id, resolved);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_alerts_created_at ON alerts(org_id, created_at DESC);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_alerts_type ON alerts(org_id, type);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- SCANS
-- =============================================================================
CREATE TABLE IF NOT EXISTS scans (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    target        TEXT NOT NULL,
    scan_type     TEXT NOT NULL DEFAULT 'port' CHECK (scan_type IN ('port', 'vulnerability', 'full')),
    status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    open_ports    JSONB DEFAULT '[]',
    services      JSONB DEFAULT '[]',
    risks         JSONB DEFAULT '[]',
    summary       TEXT,
    error_message TEXT,
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE INDEX idx_scans_org_id ON scans(org_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_scans_status ON scans(org_id, status);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_scans_target ON scans(target);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_scans_created_at ON scans(org_id, created_at DESC);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- REPORTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS reports (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    type          TEXT NOT NULL CHECK (type IN ('soc2', 'gdpr', 'iso27001', 'custom')),
    period_start  DATE NOT NULL,
    period_end    DATE NOT NULL,
    status        TEXT NOT NULL DEFAULT 'generating' CHECK (status IN ('generating', 'ready', 'failed')),
    content       TEXT,
    summary       JSONB,
    created_by    UUID REFERENCES users(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at  TIMESTAMPTZ
);

DO $$ BEGIN
    CREATE INDEX idx_reports_org_id ON reports(org_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_reports_type ON reports(org_id, type);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_reports_status ON reports(org_id, status);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_reports_created_at ON reports(org_id, created_at DESC);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- WEBHOOK CONFIGS
-- =============================================================================
CREATE TABLE IF NOT EXISTS webhook_configs (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    type          TEXT NOT NULL CHECK (type IN ('slack', 'email', 'generic', 'pagerduty', 'discord')),
    config        JSONB NOT NULL DEFAULT '{}',
    active        BOOLEAN NOT NULL DEFAULT true,
    events        TEXT[] DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE INDEX idx_webhook_configs_org_id ON webhook_configs(org_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_webhook_configs_active ON webhook_configs(org_id, active);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_webhook_configs_type ON webhook_configs(type);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- AUDIT LOG
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    action        TEXT NOT NULL,
    resource      TEXT NOT NULL,
    resource_id   UUID,
    details       JSONB DEFAULT '{}',
    ip_address    TEXT,
    user_agent    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$ BEGIN
    CREATE INDEX idx_audit_log_org_id ON audit_log(org_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_audit_log_action ON audit_log(org_id, action);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_audit_log_resource ON audit_log(org_id, resource);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE INDEX idx_audit_log_created_at ON audit_log(org_id, created_at DESC);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Audit log immutability trigger (idempotent)
DO $$ BEGIN
    CREATE TRIGGER audit_log_immutable
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- TRIGGERS & FUNCTIONS
-- =============================================================================

-- updated_at helper function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers (idempotent via DO blocks)
DO $$ BEGIN
    CREATE TRIGGER update_organizations_updated_at
        BEFORE UPDATE ON organizations
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_endpoints_updated_at
        BEFORE UPDATE ON endpoints
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_webhook_configs_updated_at
        BEFORE UPDATE ON webhook_configs
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Audit log immutability function
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log entries cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- RLS - Enable and create policies (idempotent)
-- =============================================================================

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE endpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- get_user_org_id helper
CREATE OR REPLACE FUNCTION get_user_org_id()
RETURNS UUID AS $$
BEGIN
    RETURN (
        SELECT org_id::UUID
        FROM users
        WHERE id = (current_setting('request.jwt.claim.sub', true))::UUID
    );
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Organizations policies
DO $$ BEGIN
    CREATE POLICY "Users can view own organization"
        ON organizations FOR SELECT
        USING (id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Users can update own organization"
        ON organizations FOR UPDATE
        USING (id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Users policies
DO $$ BEGIN
    CREATE POLICY "Org members can view other org members"
        ON users FOR SELECT
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Admins can insert org members"
        ON users FOR INSERT
        WITH CHECK (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Admins can update org members"
        ON users FOR UPDATE
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- API Keys policies
DO $$ BEGIN
    CREATE POLICY "Org members can view api_keys"
        ON api_keys FOR SELECT
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Admins can manage api_keys"
        ON api_keys FOR ALL
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Endpoints policies
DO $$ BEGIN
    CREATE POLICY "Org members can manage endpoints"
        ON endpoints FOR ALL
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Events policies
DO $$ BEGIN
    CREATE POLICY "Org members can view events"
        ON events FOR SELECT
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Service role or SDK can insert events"
        ON events FOR INSERT
        WITH CHECK (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Alerts policies
DO $$ BEGIN
    CREATE POLICY "Org members can view alerts"
        ON alerts FOR SELECT
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Org members can resolve alerts"
        ON alerts FOR UPDATE
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "System can create alerts"
        ON alerts FOR INSERT
        WITH CHECK (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Scans policies
DO $$ BEGIN
    CREATE POLICY "Org members can view scans"
        ON scans FOR SELECT
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Org members can create scans"
        ON scans FOR INSERT
        WITH CHECK (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Org members can update scans"
        ON scans FOR UPDATE
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Reports policies
DO $$ BEGIN
    CREATE POLICY "Org members can view reports"
        ON reports FOR SELECT
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Admins can manage reports"
        ON reports FOR ALL
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Webhook configs policies
DO $$ BEGIN
    CREATE POLICY "Org members can view webhook_configs"
        ON webhook_configs FOR SELECT
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Admins can manage webhook_configs"
        ON webhook_configs FOR ALL
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Audit log policies
DO $$ BEGIN
    CREATE POLICY "Org members can view audit_log"
        ON audit_log FOR SELECT
        USING (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "System can insert audit_log"
        ON audit_log FOR INSERT
        WITH CHECK (org_id = get_user_org_id());
EXCEPTION WHEN duplicate_object THEN null;
END $$;
