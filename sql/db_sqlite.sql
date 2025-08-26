-- ============================================
-- 1. Tenants
-- ============================================
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,       -- Auto-increment tenant ID
    name TEXT UNIQUE NOT NULL,                  -- Unique tenant name
    limit_users INTEGER,                        -- Optional user quota
    limit_projects INTEGER,                     -- Optional project quota
    limit_api_requests_per_day INTEGER,         -- Optional daily API quota
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
);

CREATE INDEX idx_tenants_name ON tenants (name);


-- ============================================
-- 2. Users
-- ============================================
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,       -- Auto-increment user ID
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,  -- Case-insensitive email
    password_hash TEXT NOT NULL,
    name TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
);

CREATE INDEX idx_users_email ON users (email);


-- ============================================
-- 3. Memberships (Users <-> Tenants Many-to-Many)
-- ============================================
CREATE TABLE memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,       -- Auto-increment membership ID
    user_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    UNIQUE (user_id, tenant_id),                -- Prevent duplicate memberships
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX idx_memberships_tenant ON memberships (tenant_id);
CREATE INDEX idx_memberships_user ON memberships (user_id);


-- ============================================
-- 4. Prompts
-- ============================================
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    created_by INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,                           -- Store latest active text
    is_archived INTEGER DEFAULT 0,                       -- Boolean (0/1)
    current_version_id INTEGER,                          -- Latest version reference
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users (id),
    FOREIGN KEY (current_version_id) REFERENCES prompt_versions (id)
);

CREATE INDEX idx_prompts_tenant ON prompts (tenant_id);
CREATE INDEX idx_prompts_created_by ON prompts (created_by);
CREATE INDEX idx_prompts_is_archived ON prompts (tenant_id, is_archived);
CREATE INDEX idx_prompts_title_search ON prompts (title);

-- ============================================
-- 5. Prompt Versions
-- ============================================
CREATE TABLE prompt_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    prompt_text TEXT NOT NULL,                           -- Actual version text
    style TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users (id),
    UNIQUE (prompt_id, version_number)                   -- Prevent duplicates
);

CREATE INDEX idx_prompt_versions_prompt ON prompt_versions (prompt_id);
CREATE INDEX idx_prompt_versions_latest ON prompt_versions (prompt_id, version_number DESC);

-- ============================================
-- 6. Tags
-- ============================================
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
);

CREATE INDEX idx_tags_name ON tags (name);

-- ============================================
-- 7. Prompt ↔ Tags (Many-to-Many bridge table)
-- ============================================
CREATE TABLE prompt_tags (
    prompt_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    assigned_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
    PRIMARY KEY (prompt_id, tag_id)                      -- Prevent duplicates
);

CREATE INDEX idx_prompt_tags_prompt ON prompt_tags (prompt_id);
CREATE INDEX idx_prompt_tags_tag ON prompt_tags (tag_id);



-- ============================================
-- 8. Audit Log
-- ============================================
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    prompt_id TEXT NOT NULL,
    user_id TEXT,
    action TEXT NOT NULL CHECK (action IN ('create', 'update', 'rollback', 'delete')),
    old_version TEXT,
    new_version TEXT,
    timestamp DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (old_version) REFERENCES prompt_versions (id),
    FOREIGN KEY (new_version) REFERENCES prompt_versions (id)
);

CREATE INDEX idx_audit_log_prompt ON audit_log (prompt_id);
CREATE INDEX idx_audit_log_user ON audit_log (user_id);
CREATE INDEX idx_audit_log_action ON audit_log (action);


-- ============================================
-- 9. Refresh Tokens
-- ============================================
CREATE TABLE refresh_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked INTEGER DEFAULT 0,                          -- Boolean stored as 0/1
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_valid ON refresh_tokens (user_id, revoked, expires_at);


-- ============================================
-- 10. API Keys
-- ============================================
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    hash TEXT UNIQUE NOT NULL,
    prefix TEXT NOT NULL,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    last_used_at DATETIME,
    FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX idx_api_keys_tenant ON api_keys (tenant_id);
CREATE INDEX idx_api_keys_prefix ON api_keys (prefix);
