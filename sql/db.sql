-- ============================================
-- 1. Tenants
-- ============================================
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,                          -- Unique tenant name
    settings JSONB DEFAULT '{}'::jsonb,                 -- Configurable tenant settings
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tenants_name ON tenants (name);        -- Optimize lookups by name


-- ============================================
-- 2. Users
-- ============================================
CREATE EXTENSION IF NOT EXISTS citext;                  -- For case-insensitive emails

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email CITEXT UNIQUE NOT NULL,                       -- Case-insensitive uniqueness
    password_hash TEXT NOT NULL,                        -- Store hash, not raw password
    name TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_users_email ON users (email);


-- ============================================
-- 3. Memberships (Many-to-Many: Users <-> Tenants)
-- ============================================
CREATE TABLE memberships (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    PRIMARY KEY (user_id, tenant_id)
);

CREATE INDEX idx_memberships_tenant ON memberships (tenant_id);
CREATE INDEX idx_memberships_user ON memberships (user_id);


-- ============================================
-- 4. Prompts
-- ============================================
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    created_by UUID REFERENCES users (id),
    title TEXT NOT NULL,
    description TEXT,
    is_archived BOOLEAN DEFAULT FALSE,
    current_version_id UUID, -- Latest version pointer
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX idx_prompts_tenant ON prompts (tenant_id);
CREATE INDEX idx_prompts_created_by ON prompts (created_by);
CREATE INDEX idx_prompts_is_archived ON prompts (tenant_id, is_archived);
CREATE INDEX idx_prompts_title_search ON prompts (title);


-- ============================================
-- 5. Prompt Versions
-- ============================================
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID NOT NULL REFERENCES prompts (id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,                    -- Sequential versioning
    body TEXT NOT NULL,                                 -- Actual prompt text
    style TEXT,                                         -- Optional formatting/style
    created_by UUID REFERENCES users (id),
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_prompt_version UNIQUE (prompt_id, version_number)
);

-- Indexes
CREATE INDEX idx_prompt_versions_prompt ON prompt_versions (prompt_id);
CREATE INDEX idx_prompt_versions_latest ON prompt_versions (prompt_id DESC, version_number DESC);


-- ============================================
-- 6. Prompt Metadata (Key-Value Pairs)
-- ============================================
CREATE TABLE prompt_metadata (
    id SERIAL PRIMARY KEY,
    prompt_id UUID NOT NULL REFERENCES prompts (id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT,
    CONSTRAINT unique_prompt_metadata UNIQUE (prompt_id, key) -- Prevent duplicate keys
);

CREATE INDEX idx_prompt_metadata_key ON prompt_metadata (key);
CREATE INDEX idx_prompt_metadata_prompt ON prompt_metadata (prompt_id);


-- ============================================
-- 7. Prompt Tags
-- ============================================
CREATE TABLE prompt_tags (
    id SERIAL PRIMARY KEY,
    prompt_id UUID NOT NULL REFERENCES prompts (id) ON DELETE CASCADE,
    tag TEXT NOT NULL
);

CREATE INDEX idx_prompt_tags_tag ON prompt_tags (tag);
CREATE INDEX idx_prompt_tags_prompt ON prompt_tags (prompt_id);


-- ============================================
-- 8. Audit Log
-- ============================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID NOT NULL REFERENCES prompts (id) ON DELETE CASCADE,
    user_id UUID REFERENCES users (id),
    action TEXT NOT NULL CHECK (
        action IN ('create', 'update', 'rollback', 'delete')
    ),
    old_version UUID REFERENCES prompt_versions (id),
    new_version UUID REFERENCES prompt_versions (id),
    timestamp TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_log_prompt ON audit_log (prompt_id);
CREATE INDEX idx_audit_log_user ON audit_log (user_id);
CREATE INDEX idx_audit_log_action ON audit_log (action);


-- ============================================
-- 9. Refresh Tokens
-- ============================================
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_valid ON refresh_tokens (user_id, revoked, expires_at);


-- ============================================
-- 10. API Keys
-- ============================================
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    hash TEXT UNIQUE NOT NULL, -- Secure hash
    prefix TEXT NOT NULL,      -- Short identifier for logging
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_tenant ON api_keys (tenant_id);
CREATE INDEX idx_api_keys_prefix ON api_keys (prefix);
