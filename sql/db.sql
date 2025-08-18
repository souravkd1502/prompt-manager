-- ========== 1. Tenants ==========
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT now()
);

-- ========== 2. Users ==========
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    tenant_id UUID NOT NULL,
    username TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_users_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

-- ========== 3. Prompts ==========
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    tenant_id UUID NOT NULL,
    created_by UUID,
    title TEXT NOT NULL,
    description TEXT,
    is_archived BOOLEAN DEFAULT FALSE,
    current_version_id UUID, -- Points to latest version
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_prompts_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
    CONSTRAINT fk_prompts_created_by FOREIGN KEY (created_by) REFERENCES users (id),
    CONSTRAINT fk_prompts_current_version FOREIGN KEY (current_version_id) REFERENCES prompt_versions (id)
);

-- ========== 4. Prompt Versions ==========
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    prompt_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    body TEXT NOT NULL,
    style TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_prompt_versions_prompt FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
    CONSTRAINT fk_prompt_versions_created_by FOREIGN KEY (created_by) REFERENCES users (id),
    CONSTRAINT unique_prompt_version UNIQUE (prompt_id, version_number)
);

-- ========== 5. Prompt Metadata ==========
CREATE TABLE prompt_metadata (
    id SERIAL PRIMARY KEY,
    prompt_id UUID NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    CONSTRAINT fk_prompt_metadata_prompt FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
);

-- ========== 6. Prompt Tags ==========
CREATE TABLE prompt_tags (
    id SERIAL PRIMARY KEY,
    prompt_id UUID NOT NULL,
    tag TEXT,
    CONSTRAINT fk_prompt_tags_prompt FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
);

-- ========== 7. Audit Log ==========
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    prompt_id UUID NOT NULL,
    user_id UUID,
    action TEXT CHECK (
        action IN (
            'create',
            'update',
            'rollback',
            'delete'
        )
    ),
    old_version UUID,
    new_version UUID,
    timestamp TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_audit_log_prompt FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
    CONSTRAINT fk_audit_log_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_audit_log_old_version FOREIGN KEY (old_version) REFERENCES prompt_versions (id),
    CONSTRAINT fk_audit_log_new_version FOREIGN KEY (new_version) REFERENCES prompt_versions (id)
);