-- =============================================================================
-- SentinelAPI - Supabase Database Schema
-- Version: 1.0.0
-- Description: Multi-tenant API security monitoring platform schema
-- =============================================================================

-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- ORGANIZATIONS
-- Each organization is a customer/tenant in the multi-tenant system.
-- Plan can be: starter, pro, enterprise
-- =============================================================================
CREATE TABLE organizations (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name          TEXT NOT NULL,
    plan          TEXT NOT NULL DEFAULT 'starter' CHECK (plan IN ('starter', 'pro', 'enterprise')),
    stripe_customer_id TEXT UNIQUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_organizations_stripe_customer_id ON organizations(stripe_customer_id);
CREATE INDEX idx_organizations_plan ON organizations(plan);

-- =============================================================================
-- USERS
-- Users belong to organizations. Auth handled by Clerk.
-- The id matches Clerk's user ID (external auth).
-- =============================================================================
CREATE TABLE users (
    id            UUID PRIMARY KEY,  -- Clerk user ID (external)
    email         TEXT NOT NULL,
    name          TEXT,
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role          TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_org_id ON users(org_id);
CREATE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_users_org_email ON users(org_id, email);

-- =============================================================================
-- API KEYS
-- Org-level keys for SDK authentication.
-- key_hash stores the hashed value (never store plaintext).
-- prefix is the first 8 chars shown in the UI for identification.
-- =============================================================================
CREATE TABLE api_keys (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    key_hash      TEXT NOT NULL,
    prefix        TEXT NOT NULL,  -- First 8 chars for display (e.g., "sk_live_a1b2c3d4")
    name          TEXT NOT NULL,
    env           TEXT NOT NULL DEFAULT 'production' CHECK (env IN ('production', 'staging', 'development')),
    last_used_at  TIMESTAMPTZ,
    expires_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at    TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_org_id ON api_keys(org_id);
CREATE INDEX idx_api_keys_prefix ON api_keys(prefix);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

-- =============================================================================
-- ENDPOINTS
-- Monitored API endpoints per organization.
-- Represents the APIs customers want to track/secure.
-- =============================================================================
CREATE TABLE endpoints (
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

CREATE INDEX idx_endpoints_org_id ON endpoints(org_id);
CREATE INDEX idx_endpoints_active ON endpoints(org_id, active);
CREATE INDEX idx_endpoints_url ON endpoints(url);

-- =============================================================================
-- EVENTS
-- Ingested API request data. High-volume table — partition by date if needed.
-- anomaly_score: 0.0 (normal) to 1.0 (highly anomalous), computed by Claude API.
-- =============================================================================
CREATE TABLE events (
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

-- High-volume indexes for common query patterns
CREATE INDEX idx_events_org_id ON events(org_id);
CREATE INDEX idx_events_endpoint_id ON events(endpoint_id);
CREATE INDEX idx_events_created_at ON events(org_id, created_at DESC);
CREATE INDEX idx_events_anomaly_score ON events(org_id, anomaly_score DESC) WHERE anomaly_score > 0.5;
CREATE INDEX idx_events_ip ON events(org_id, ip);
CREATE INDEX idx_events_threat_type ON events(org_id, threat_type) WHERE threat_type IS NOT NULL;

-- =============================================================================
-- ALERTS
-- Threat detections generated from event analysis.
-- severity: low, medium, high, critical
-- type: injection, anomaly, scan, breach, rate_limit, etc.
-- =============================================================================
CREATE TABLE alerts (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_id      UUID REFERENCES events(id) ON DELETE SET NULL,
    severity      TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    type          TEXT NOT NULL,  -- e.g., 'sql_injection', 'rate_limit', 'data_breach'
    title         TEXT NOT NULL,
    description   TEXT,
    remediation   TEXT,
    resolved      BOOLEAN NOT NULL DEFAULT false,
    resolved_by   UUID REFERENCES users(id),
    resolved_at   TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_org_id ON alerts(org_id);
CREATE INDEX idx_alerts_severity ON alerts(org_id, severity);
CREATE INDEX idx_alerts_resolved ON alerts(org_id, resolved);
CREATE INDEX idx_alerts_created_at ON alerts(org_id, created_at DESC);
CREATE INDEX idx_alerts_type ON alerts(org_id, type);

-- =============================================================================
-- SCANS
-- Port scan and vulnerability scan results.
-- status: pending, running, completed, failed
-- open_ports: JSONB array of discovered ports
-- risks: JSONB array of risk findings
-- =============================================================================
CREATE TABLE scans (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    target        TEXT NOT NULL,  -- IP or hostname being scanned
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

CREATE INDEX idx_scans_org_id ON scans(org_id);
CREATE INDEX idx_scans_status ON scans(org_id, status);
CREATE INDEX idx_scans_target ON scans(target);
CREATE INDEX idx_scans_created_at ON scans(org_id, created_at DESC);

-- =============================================================================
-- REPORTS
-- Compliance reports (SOC2, GDPR, ISO 27001).
-- status: generating, ready, failed
-- content: stored as text/markdown when ready
-- =============================================================================
CREATE TABLE reports (
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

CREATE INDEX idx_reports_org_id ON reports(org_id);
CREATE INDEX idx_reports_type ON reports(org_id, type);
CREATE INDEX idx_reports_status ON reports(org_id, status);
CREATE INDEX idx_reports_created_at ON reports(org_id, created_at DESC);

-- =============================================================================
-- WEBHOOK CONFIGURATIONS
-- Integrations for alert delivery (Slack, email, generic HTTP).
-- config: JSONB storing channel/endpoint-specific settings
-- =============================================================================
CREATE TABLE webhook_configs (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    type          TEXT NOT NULL CHECK (type IN ('slack', 'email', 'generic', 'pagerduty', 'discord')),
    config        JSONB NOT NULL DEFAULT '{}',
    -- Slack: { channel: "#alerts", webhook_url: "..." }
    -- Email: { recipients: ["admin@company.com"], smtp_config: {...} }
    -- Generic: { url: "https://...", headers: {...}, secret: "..." }
    active        BOOLEAN NOT NULL DEFAULT true,
    events        TEXT[] DEFAULT '{}',  -- Which event types to send: ['alert.created', 'alert.resolved', 'scan.completed']
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_webhook_configs_org_id ON webhook_configs(org_id);
CREATE INDEX idx_webhook_configs_active ON webhook_configs(org_id, active);
CREATE INDEX idx_webhook_configs_type ON webhook_configs(type);

-- =============================================================================
-- AUDIT LOG
-- Immutable log of all significant actions for compliance and security.
-- This table should only allow INSERT (no UPDATE/DELETE via app).
-- =============================================================================
CREATE TABLE audit_log (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    action        TEXT NOT NULL,  -- e.g., 'api_key.created', 'alert.resolved', 'user.invited'
    resource      TEXT NOT NULL,  -- e.g., 'api_keys', 'alerts', 'users'
    resource_id   UUID,
    details       JSONB DEFAULT '{}',
    ip_address    TEXT,
    user_agent    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_org_id ON audit_log(org_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(org_id, action);
CREATE INDEX idx_audit_log_resource ON audit_log(org_id, resource);
CREATE INDEX idx_audit_log_created_at ON audit_log(org_id, created_at DESC);

-- Prevent updates/deletes on audit_log to maintain immutability
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log entries cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_immutable
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();

-- =============================================================================
-- UPDATED_AT trigger helper
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_endpoints_updated_at
    BEFORE UPDATE ON endpoints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_webhook_configs_updated_at
    BEFORE UPDATE ON webhook_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- All tables have org_id-based isolation for multi-tenant security.
-- =============================================================================

-- Enable RLS on all tables
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

-- Helper function to get current user's org_id from JWT claims
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

-- Organizations: users can see their own org
CREATE POLICY "Users can view own organization"
    ON organizations FOR SELECT
    USING (id = get_user_org_id());

CREATE POLICY "Users can update own organization"
    ON organizations FOR UPDATE
    USING (id = get_user_org_id());

-- Users: org members can see other org members
CREATE POLICY "Org members can view other org members"
    ON users FOR SELECT
    USING (org_id = get_user_org_id());

CREATE POLICY "Admins can insert org members"
    ON users FOR INSERT
    WITH CHECK (org_id = get_user_org_id());

CREATE POLICY "Admins can update org members"
    ON users FOR UPDATE
    USING (org_id = get_user_org_id());

-- API Keys: only admins/owners can manage, all org members can view
CREATE POLICY "Org members can view api_keys"
    ON api_keys FOR SELECT
    USING (org_id = get_user_org_id());

CREATE POLICY "Admins can manage api_keys"
    ON api_keys FOR ALL
    USING (org_id = get_user_org_id());

-- Endpoints: all org members can CRUD
CREATE POLICY "Org members can manage endpoints"
    ON endpoints FOR ALL
    USING (org_id = get_user_org_id());

-- Events: all org members can view/insert (SDK inserts, UI reads)
CREATE POLICY "Org members can view events"
    ON events FOR SELECT
    USING (org_id = get_user_org_id());

CREATE POLICY "Service role or SDK can insert events"
    ON events FOR INSERT
    WITH CHECK (org_id = get_user_org_id());

-- Alerts: all org members can view/resolve
CREATE POLICY "Org members can view alerts"
    ON alerts FOR SELECT
    USING (org_id = get_user_org_id());

CREATE POLICY "Org members can resolve alerts"
    ON alerts FOR UPDATE
    USING (org_id = get_user_org_id());

CREATE POLICY "System can create alerts"
    ON alerts FOR INSERT
    WITH CHECK (org_id = get_user_org_id());

-- Scans: all org members can view/initiate
CREATE POLICY "Org members can view scans"
    ON scans FOR SELECT
    USING (org_id = get_user_org_id());

CREATE POLICY "Org members can create scans"
    ON scans FOR INSERT
    WITH CHECK (org_id = get_user_org_id());

CREATE POLICY "Org members can update scans"
    ON scans FOR UPDATE
    USING (org_id = get_user_org_id());

-- Reports: all org members can view
CREATE POLICY "Org members can view reports"
    ON reports FOR SELECT
    USING (org_id = get_user_org_id());

CREATE POLICY "Admins can manage reports"
    ON reports FOR ALL
    USING (org_id = get_user_org_id());

-- Webhook configs: only admins can manage
CREATE POLICY "Org members can view webhook_configs"
    ON webhook_configs FOR SELECT
    USING (org_id = get_user_org_id());

CREATE POLICY "Admins can manage webhook_configs"
    ON webhook_configs FOR ALL
    USING (org_id = get_user_org_id());

-- Audit log: all org members can view
CREATE POLICY "Org members can view audit_log"
    ON audit_log FOR SELECT
    USING (org_id = get_user_org_id());

CREATE POLICY "System can insert audit_log"
    ON audit_log FOR INSERT
    WITH CHECK (org_id = get_user_org_id());

-- =============================================================================
-- USEFUL VIEWS
-- =============================================================================

-- Active alerts summary by severity
CREATE OR REPLACE VIEW alert_summary AS
SELECT
    org_id,
    severity,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE resolved = false) as unresolved_count
FROM alerts
GROUP BY org_id, severity;

-- Recent events with high anomaly scores
CREATE OR REPLACE VIEW high_risk_events AS
SELECT
    e.*,
    o.name as org_name
FROM events e
JOIN organizations o ON o.id = e.org_id
WHERE e.anomaly_score > 0.7;

COMMENT ON TABLE organizations IS 'Customer organizations/tenants. Each org represents a paying customer.';
COMMENT ON TABLE users IS 'Users belonging to organizations. ID matches Clerk external auth.';
COMMENT ON TABLE api_keys IS 'Organization-level API keys for SDK authentication. key_hash is SHA-256 of the actual key.';
COMMENT ON TABLE endpoints IS 'Monitored API endpoints that customers want to track.';
COMMENT ON TABLE events IS 'Ingested API request data. High-volume table - consider partitioning by date.';
COMMENT ON TABLE alerts IS 'Threat detections generated from event analysis by Claude API.';
COMMENT ON TABLE scans IS 'Port and vulnerability scan results.';
COMMENT ON TABLE reports IS 'Compliance reports (SOC2, GDPR, ISO 27001).';
COMMENT ON TABLE webhook_configs IS 'Webhook integrations for alert delivery (Slack, email, generic HTTP).';
COMMENT ON TABLE audit_log IS 'Immutable audit log of all significant actions.';
