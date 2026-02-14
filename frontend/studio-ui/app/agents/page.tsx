'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Search, Filter, MoreVertical, Trash2, Copy, ExternalLink } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/input';
import { studioApi } from '@/lib/api';
import { cn, formatDate, formatRelativeTime } from '@/lib/utils';
import type { AgentSummary } from '@/types';

// ============================================================================
// Page Component
// ============================================================================

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [complexityFilter, setComplexityFilter] = useState<string>('all');

  // Fetch agents
  useEffect(() => {
    const fetchAgents = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await studioApi.listAgents({
          complexity: complexityFilter !== 'all' ? complexityFilter as 'simple' | 'moderate' | 'complex' : undefined,
        });
        setAgents(response.agents || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load agents');
      } finally {
        setIsLoading(false);
      }
    };
    fetchAgents();
  }, [complexityFilter]);

  // Filter by search
  const filteredAgents = agents.filter((agent) =>
    agent.description?.toLowerCase().includes(search.toLowerCase())
  );

  // Complexity badge color
  const getComplexityBadge = (complexity: string) => {
    switch (complexity) {
      case 'simple':
        return <Badge variant="success">Simple</Badge>;
      case 'moderate':
        return <Badge variant="warning">Moderate</Badge>;
      case 'complex':
        return <Badge variant="error">Complex</Badge>;
      default:
        return <Badge>{complexity}</Badge>;
    }
  };

  // Task type badge
  const getTaskTypeBadge = (taskType: string) => {
    return <Badge variant="outline">{taskType}</Badge>;
  };

  const pageActions = (
    <Link href="/create">
      <Button variant="primary" size="sm" iconLeft={<Plus className="w-4 h-4" />}>
        Create Agent
      </Button>
    </Link>
  );

  return (
    <AppShell title="Agents" actions={pageActions}>
      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            placeholder="Search agents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select
          value={complexityFilter}
          onChange={(e) => setComplexityFilter(e.target.value)}
          options={[
            { value: 'all', label: 'All Complexity' },
            { value: 'simple', label: 'Simple' },
            { value: 'moderate', label: 'Moderate' },
            { value: 'complex', label: 'Complex' },
          ]}
        />
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-error/10 border border-error/30 rounded-lg p-4 mb-6">
          <p className="text-error">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-surface rounded-lg shimmer" />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredAgents.length === 0 && (
        <div className="text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-surface flex items-center justify-center">
            <Search className="w-8 h-8 text-text-muted" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No agents found</h3>
          <p className="text-text-secondary mb-6">
            {search
              ? 'Try adjusting your search or filters'
              : 'Create your first agent to get started'}
          </p>
          {!search && (
            <Link href="/create">
              <Button variant="primary" iconLeft={<Plus className="w-4 h-4" />}>
                Create Agent
              </Button>
            </Link>
          )}
        </div>
      )}

      {/* Agent Grid */}
      {!isLoading && filteredAgents.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map((agent) => (
            <AgentCard key={agent.agent_id} agent={agent} />
          ))}
        </div>
      )}
    </AppShell>
  );
}

// ============================================================================
// Agent Card Component
// ============================================================================

interface AgentCardProps {
  agent: AgentSummary;
}

function AgentCard({ agent }: AgentCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  const getComplexityBadge = (complexity: string) => {
    switch (complexity) {
      case 'simple':
        return <Badge variant="success" size="sm">Simple</Badge>;
      case 'moderate':
        return <Badge variant="warning" size="sm">Moderate</Badge>;
      case 'complex':
        return <Badge variant="error" size="sm">Complex</Badge>;
      default:
        return <Badge size="sm">{complexity}</Badge>;
    }
  };

  return (
    <Card variant="interactive" className="group">
      <CardHeader
        description={
          <p className="text-sm text-text-secondary line-clamp-2 mt-1">
            {agent.description || 'No description'}
          </p>
        }
        action={
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(!showMenu);
              }}
              className="p-1.5 rounded hover:bg-surface-2 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <MoreVertical className="w-4 h-4 text-text-muted" />
            </button>
            {showMenu && (
              <div className="absolute right-0 top-full mt-1 w-36 bg-surface border border-border rounded-lg shadow-lg z-10 py-1">
                <Link
                  href={`/agents/${agent.agent_id}`}
                  className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Details
                </Link>
                <button className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-2 w-full">
                  <Copy className="w-4 h-4" />
                  Duplicate
                </button>
                <button className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-2 w-full text-error">
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            )}
          </div>
        }
      >
        <div className="flex items-center gap-2">
          {getComplexityBadge(agent.complexity || 'moderate')}
          {agent.task_type && (
            <Badge variant="outline" size="sm">
              {agent.task_type}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="text-xs text-text-muted">
          Updated {formatRelativeTime(agent.updated_at ?? agent.created_at ?? '')}
        </div>
      </CardContent>

      <CardFooter>
        <Link href={`/create?agent=${agent.agent_id}`} className="flex-1">
          <Button variant="outline" size="sm" fullWidth>
            Edit
          </Button>
        </Link>
        <Link href={`/agents/${agent.agent_id}/deploy`}>
          <Button variant="primary" size="sm">
            Deploy
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
}
