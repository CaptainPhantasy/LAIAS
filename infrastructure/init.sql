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
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
