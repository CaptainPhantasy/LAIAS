-- =============================================================================
-- LAIAS Database Schema
-- Legacy AI Agent Studio
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- AGENTS TABLE
-- Stores generated agent definitions and code
-- =============================================================================
CREATE TABLE agents (
    id VARCHAR(50) PRIMARY KEY DEFAULT 'gen_' || substr(md5(random()::text), 1, 12),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Generated code (Godzilla pattern)
    flow_code TEXT NOT NULL,
    agents_yaml TEXT,
    state_class TEXT,
    
    -- Configuration
    complexity VARCHAR(20) CHECK (complexity IN ('simple', 'moderate', 'complex')),
    task_type VARCHAR(50) CHECK (task_type IN ('research', 'development', 'analysis', 'automation', 'general')),
    tools JSONB DEFAULT '[]'::jsonb,
    requirements JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    llm_provider VARCHAR(20) DEFAULT 'openai',
    model VARCHAR(50) DEFAULT 'gpt-4o',
    estimated_cost_per_run DECIMAL(10, 4),
    complexity_score INTEGER CHECK (complexity_score BETWEEN 1 AND 10),
    
    -- Validation
    validation_status JSONB DEFAULT '{}'::jsonb,
    flow_diagram TEXT,

    version INTEGER NOT NULL DEFAULT 1,
    latest_version INTEGER NOT NULL DEFAULT 1,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_versions (
    id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    flow_code TEXT,
    agents_yaml TEXT,
    state_class TEXT,
    requirements JSONB DEFAULT '[]'::jsonb,
    validation_status JSONB DEFAULT '{}'::jsonb,
    flow_diagram TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_summary TEXT,
    CONSTRAINT uq_agent_versions_agent_version UNIQUE (agent_id, version)
);

-- =============================================================================
-- DEPLOYMENTS TABLE
-- Tracks container deployments for each agent
-- =============================================================================
CREATE TABLE deployments (
    id VARCHAR(50) PRIMARY KEY DEFAULT 'deploy_' || substr(md5(random()::text), 1, 12),
    agent_id VARCHAR(50) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    
    -- Container info
    container_id VARCHAR(100),
    container_name VARCHAR(100),
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'creating', 'starting', 'running', 'stopped', 'error', 'terminated')),
    
    -- Resource limits
    cpu_limit DECIMAL(4, 2) DEFAULT 1.0,
    memory_limit VARCHAR(20) DEFAULT '512m',
    
    -- Environment
    environment_vars JSONB DEFAULT '{}'::jsonb,
    
    -- Lifecycle timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    stopped_at TIMESTAMP WITH TIME ZONE,
    
    -- Error tracking
    last_error TEXT,
    error_count INTEGER DEFAULT 0
);

-- =============================================================================
-- EXECUTION LOGS TABLE
-- Stores logs from agent executions
-- =============================================================================
CREATE TABLE execution_logs (
    id BIGSERIAL PRIMARY KEY,
    deployment_id VARCHAR(50) NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    
    -- Log data
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    source VARCHAR(100),
    
    -- Structured data
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- EXECUTION METRICS TABLE
-- Stores performance metrics per execution
-- =============================================================================
CREATE TABLE execution_metrics (
    id BIGSERIAL PRIMARY KEY,
    deployment_id VARCHAR(50) NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    
    -- Resource usage
    cpu_percent DECIMAL(5, 2),
    memory_usage_mb DECIMAL(10, 2),
    
    -- Execution stats
    tokens_used INTEGER DEFAULT 0,
    api_calls INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10, 4) DEFAULT 0,
    
    -- Duration
    execution_duration_seconds INTEGER,
    
    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- CREW RUNS TABLE
-- Top-level run records for structured execution tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS crew_runs (
    id VARCHAR(120) PRIMARY KEY,
    deployment_id VARCHAR(50) NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- TASK RESULTS TABLE
-- Per-task structured results from CrewAI events/callbacks
-- =============================================================================
CREATE TABLE IF NOT EXISTS task_results (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(120) NOT NULL REFERENCES crew_runs(id) ON DELETE CASCADE,
    deployment_id VARCHAR(50) NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    task_name VARCHAR(255),
    agent_role VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'completed'
        CHECK (status IN ('started', 'completed', 'failed')),
    output_raw TEXT,
    output_json JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- LLM CALLS TABLE
-- LLM-level observability and cost accounting
-- =============================================================================
CREATE TABLE IF NOT EXISTS llm_calls (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(120) NOT NULL REFERENCES crew_runs(id) ON DELETE CASCADE,
    deployment_id VARCHAR(50) NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    call_id VARCHAR(255),
    model VARCHAR(255),
    call_type VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'completed'
        CHECK (status IN ('started', 'completed', 'failed')),
    error TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- TOOL USAGE TABLE
-- Tool invocation observability
-- =============================================================================
CREATE TABLE IF NOT EXISTS tool_usage (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(120) NOT NULL REFERENCES crew_runs(id) ON DELETE CASCADE,
    deployment_id VARCHAR(50) NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    tool_args JSONB DEFAULT '{}'::jsonb,
    output TEXT,
    from_cache BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'completed'
        CHECK (status IN ('started', 'completed', 'failed')),
    error TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================
CREATE INDEX idx_agents_created_at ON agents(created_at DESC);
CREATE INDEX idx_agents_task_type ON agents(task_type);
CREATE INDEX idx_deployments_agent_id ON deployments(agent_id);
CREATE INDEX idx_deployments_status ON deployments(status);
CREATE INDEX idx_deployments_created_at ON deployments(created_at DESC);
CREATE INDEX idx_execution_logs_deployment_id ON execution_logs(deployment_id);
CREATE INDEX idx_execution_logs_timestamp ON execution_logs(timestamp DESC);
CREATE INDEX idx_execution_logs_level ON execution_logs(level);
CREATE INDEX idx_execution_metrics_deployment_id ON execution_metrics(deployment_id);
CREATE INDEX IF NOT EXISTS idx_agent_versions_agent_id ON agent_versions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_versions_version ON agent_versions(version);
CREATE INDEX IF NOT EXISTS idx_agent_versions_agent_id_version ON agent_versions(agent_id, version);
CREATE INDEX IF NOT EXISTS idx_crew_runs_deployment_id ON crew_runs(deployment_id);
CREATE INDEX IF NOT EXISTS idx_task_results_run_id ON task_results(run_id);
CREATE INDEX IF NOT EXISTS idx_task_results_deployment_id ON task_results(deployment_id);
CREATE INDEX IF NOT EXISTS idx_llm_calls_run_id ON llm_calls(run_id);
CREATE INDEX IF NOT EXISTS idx_llm_calls_deployment_id ON llm_calls(deployment_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_run_id ON tool_usage(run_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_deployment_id ON tool_usage(deployment_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at DESC);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update updated_at timestamp on agents
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- TEAM COLLABORATION TABLES
-- =============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Team membership
CREATE TABLE IF NOT EXISTS team_members (
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (team_id, user_id),
    CONSTRAINT valid_role CHECK (role IN ('owner', 'admin', 'member', 'viewer'))
);

-- Update agents table with team associations
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agents' AND column_name = 'owner_id'
    ) THEN
        ALTER TABLE agents ADD COLUMN owner_id UUID REFERENCES users(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agents' AND column_name = 'team_id'
    ) THEN
        ALTER TABLE agents ADD COLUMN team_id UUID REFERENCES teams(id);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agents' AND column_name = 'version'
    ) THEN
        ALTER TABLE agents ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agents' AND column_name = 'latest_version'
    ) THEN
        ALTER TABLE agents ADD COLUMN latest_version INTEGER NOT NULL DEFAULT 1;
    END IF;
END $$;

-- Update deployments table with team association
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'deployments' AND column_name = 'team_id'
    ) THEN
        ALTER TABLE deployments ADD COLUMN team_id UUID REFERENCES teams(id);
    END IF;
END $$;

-- =============================================================================
-- INDEXES FOR TEAM TABLES
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_teams_slug ON teams(slug);
CREATE INDEX IF NOT EXISTS idx_teams_owner ON teams(owner_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(owner_id);
CREATE INDEX IF NOT EXISTS idx_agents_team ON agents(team_id);
CREATE INDEX IF NOT EXISTS idx_deployments_team ON deployments(team_id);

-- =============================================================================
-- SEED DATA FOR DEVELOPMENT
-- =============================================================================
-- Dev user is only seeded when LAIAS_SEED_DEV_DATA is set.
-- In production, real users are created via the /auth/register endpoint.
-- The DO block checks the environment variable via current_setting() with a
-- fallback so it never errors on a clean Postgres instance.
DO $$
BEGIN
    IF current_setting('app.seed_dev_data', true) = 'true' THEN
        INSERT INTO users (id, email, name)
        VALUES ('00000000-0000-0000-0000-000000000000', 'dev@laias.local', 'Dev User')
        ON CONFLICT (id) DO NOTHING;
        RAISE NOTICE 'Dev user seeded (app.seed_dev_data=true)';
    END IF;
END $$;
