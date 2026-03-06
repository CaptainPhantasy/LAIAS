"""Initial schema from init.sql

Revision ID: 001_initial
Revises: 
Create Date: 2026-03-06

This migration captures the initial database schema defined in
infrastructure/init.sql. It includes agents, deployments, execution
logs/metrics, and team collaboration tables.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.String(50), primary_key=True, 
                  server_default=sa.text("'gen_' || substr(md5(random()::text), 1, 12)")),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('flow_code', sa.Text, nullable=False),
        sa.Column('agents_yaml', sa.Text),
        sa.Column('state_class', sa.Text),
        sa.Column('complexity', sa.String(20)),
        sa.Column('task_type', sa.String(50)),
        sa.Column('tools', postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column('requirements', postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column('llm_provider', sa.String(20), server_default='openai'),
        sa.Column('model', sa.String(50), server_default='gpt-4o'),
        sa.Column('estimated_cost_per_run', sa.Numeric(10, 4)),
        sa.Column('complexity_score', sa.Integer),
        sa.Column('validation_status', postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column('flow_diagram', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint("complexity IN ('simple', 'moderate', 'complex')", name='ck_agents_complexity'),
        sa.CheckConstraint("task_type IN ('research', 'development', 'analysis', 'automation', 'general')", 
                          name='ck_agents_task_type'),
        sa.CheckConstraint('complexity_score BETWEEN 1 AND 10', name='ck_agents_complexity_score'),
    )
    
    # Deployments table
    op.create_table(
        'deployments',
        sa.Column('id', sa.String(50), primary_key=True,
                  server_default=sa.text("'deploy_' || substr(md5(random()::text), 1, 12)")),
        sa.Column('agent_id', sa.String(50), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('container_id', sa.String(100)),
        sa.Column('container_name', sa.String(100)),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('cpu_limit', sa.Numeric(4, 2), server_default='1.0'),
        sa.Column('memory_limit', sa.String(20), server_default='512m'),
        sa.Column('environment_vars', postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('stopped_at', sa.DateTime(timezone=True)),
        sa.Column('last_error', sa.Text),
        sa.Column('error_count', sa.Integer, server_default='0'),
        sa.CheckConstraint("status IN ('pending', 'creating', 'starting', 'running', 'stopped', 'error', 'terminated')",
                          name='ck_deployments_status'),
    )
    
    # Execution logs table
    op.create_table(
        'execution_logs',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('deployment_id', sa.String(50), sa.ForeignKey('deployments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('source', sa.String(100)),
        sa.Column('metadata', postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint("level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')", 
                          name='ck_execution_logs_level'),
    )
    
    # Execution metrics table
    op.create_table(
        'execution_metrics',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('deployment_id', sa.String(50), sa.ForeignKey('deployments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cpu_percent', sa.Numeric(5, 2)),
        sa.Column('memory_usage_mb', sa.Numeric(10, 2)),
        sa.Column('tokens_used', sa.Integer, server_default='0'),
        sa.Column('api_calls', sa.Integer, server_default='0'),
        sa.Column('estimated_cost', sa.Numeric(10, 4), server_default='0'),
        sa.Column('execution_duration_seconds', sa.Integer),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('password_hash', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('last_login', sa.DateTime(timezone=True)),
    )
    
    # Teams table
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Team members table
    op.create_table(
        'team_members',
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='CASCADE'),
                 primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'),
                 primary_key=True),
        sa.Column('role', sa.String(50), server_default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint("role IN ('owner', 'admin', 'member', 'viewer')", name='ck_team_members_role'),
    )
    
    # Add team/owner columns to agents (if not exists - handled by migration)
    op.add_column('agents', sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')))
    op.add_column('agents', sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id')))
    
    # Add team column to deployments
    op.add_column('deployments', sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id')))
    
    # Create indexes
    op.create_index('idx_agents_created_at', 'agents', [sa.text('created_at DESC')])
    op.create_index('idx_agents_task_type', 'agents', ['task_type'])
    op.create_index('idx_agents_owner', 'agents', ['owner_id'])
    op.create_index('idx_agents_team', 'agents', ['team_id'])
    
    op.create_index('idx_deployments_agent_id', 'deployments', ['agent_id'])
    op.create_index('idx_deployments_status', 'deployments', ['status'])
    op.create_index('idx_deployments_created_at', 'deployments', [sa.text('created_at DESC')])
    op.create_index('idx_deployments_team', 'deployments', ['team_id'])
    
    op.create_index('idx_execution_logs_deployment_id', 'execution_logs', ['deployment_id'])
    op.create_index('idx_execution_logs_timestamp', 'execution_logs', [sa.text('timestamp DESC')])
    op.create_index('idx_execution_logs_level', 'execution_logs', ['level'])
    
    op.create_index('idx_execution_metrics_deployment_id', 'execution_metrics', ['deployment_id'])
    
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_teams_slug', 'teams', ['slug'])
    op.create_index('idx_teams_owner', 'teams', ['owner_id'])
    op.create_index('idx_team_members_team', 'team_members', ['team_id'])
    op.create_index('idx_team_members_user', 'team_members', ['user_id'])
    
    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    
    # Create trigger on agents
    op.execute("""
        CREATE TRIGGER update_agents_updated_at
            BEFORE UPDATE ON agents
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_agents_updated_at ON agents")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop indexes
    op.drop_index('idx_team_members_user', 'team_members')
    op.drop_index('idx_team_members_team', 'team_members')
    op.drop_index('idx_teams_owner', 'teams')
    op.drop_index('idx_teams_slug', 'teams')
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_execution_metrics_deployment_id', 'execution_metrics')
    op.drop_index('idx_execution_logs_level', 'execution_logs')
    op.drop_index('idx_execution_logs_timestamp', 'execution_logs')
    op.drop_index('idx_execution_logs_deployment_id', 'execution_logs')
    op.drop_index('idx_deployments_team', 'deployments')
    op.drop_index('idx_deployments_created_at', 'deployments')
    op.drop_index('idx_deployments_status', 'deployments')
    op.drop_index('idx_deployments_agent_id', 'deployments')
    op.drop_index('idx_agents_team', 'agents')
    op.drop_index('idx_agents_owner', 'agents')
    op.drop_index('idx_agents_task_type', 'agents')
    op.drop_index('idx_agents_created_at', 'agents')
    
    # Drop columns added to existing tables
    op.drop_column('deployments', 'team_id')
    op.drop_column('agents', 'team_id')
    op.drop_column('agents', 'owner_id')
    
    # Drop tables in reverse order
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_table('users')
    op.drop_table('execution_metrics')
    op.drop_table('execution_logs')
    op.drop_table('deployments')
    op.drop_table('agents')
