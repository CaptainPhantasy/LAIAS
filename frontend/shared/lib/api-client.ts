/**
 * LAIAS API Client
 * Type-safe API client for Studio UI and Control Room
 */

import {
  API_CONFIG,
  type GenerateAgentRequest,
  type GenerateAgentResponse,
  type ValidateCodeRequest,
  type ValidateCodeResponse,
  type AgentListResponse,
  type AgentDetailResponse,
  type AgentUpdateRequest,
  type RegenerateRequest,
  type DeployAgentRequest,
  type DeploymentResponse,
  type ContainerListResponse,
  type ContainerInfo,
  type ActionResponse,
  type LogsResponse,
  type MetricsResponse,
  type HealthResponse,
  type ErrorResponse,
  type LogEntry,
} from '../types';

// ============================================================================
// Error Handling
// ============================================================================

export class ApiError extends Error {
  constructor(
    public status: number,
    public data: ErrorResponse | null,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: ErrorResponse | null = null;
    try {
      errorData = await response.json();
    } catch {
      // Response wasn't JSON
    }
    throw new ApiError(
      response.status,
      errorData,
      errorData?.message || `HTTP ${response.status}: ${response.statusText}`
    );
  }
  return response.json();
}

// ============================================================================
// Agent Generator API Client (Port 8001)
// ============================================================================

const AGENT_API = API_CONFIG.agentGenerator;

export const agentGeneratorApi = {
  /**
   * Generate an agent from natural language description
   */
  async generateAgent(request: GenerateAgentRequest): Promise<GenerateAgentResponse> {
    const response = await fetch(`${AGENT_API.baseUrl}/api/generate-agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<GenerateAgentResponse>(response);
  },

  /**
   * Regenerate an agent with modifications
   */
  async regenerateAgent(request: RegenerateRequest): Promise<GenerateAgentResponse> {
    const response = await fetch(`${AGENT_API.baseUrl}/api/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<GenerateAgentResponse>(response);
  },

  /**
   * Validate generated code
   */
  async validateCode(request: ValidateCodeRequest): Promise<ValidateCodeResponse> {
    const response = await fetch(`${AGENT_API.baseUrl}/api/validate-code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<ValidateCodeResponse>(response);
  },

  /**
   * Get validation rules
   */
  async getValidationRules(): Promise<{ rules: Array<{ name: string; description: string; severity: 'error' | 'warning' | 'info' }> }> {
    const response = await fetch(`${AGENT_API.baseUrl}/api/validation-rules`);
    return handleResponse(response);
  },

  /**
   * List saved agents
   */
  async listAgents(params?: {
    limit?: number;
    offset?: number;
    task_type?: string;
    complexity?: 'simple' | 'moderate' | 'complex';
  }): Promise<AgentListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    if (params?.task_type) searchParams.set('task_type', params.task_type);
    if (params?.complexity) searchParams.set('complexity', params.complexity);

    const url = `${AGENT_API.baseUrl}/api/agents?${searchParams.toString()}`;
    const response = await fetch(url);
    return handleResponse<AgentListResponse>(response);
  },

  /**
   * Get agent by ID
   */
  async getAgent(agentId: string): Promise<AgentDetailResponse> {
    const response = await fetch(`${AGENT_API.baseUrl}/api/agents/${agentId}`);
    return handleResponse<AgentDetailResponse>(response);
  },

  /**
   * Update agent
   */
  async updateAgent(agentId: string, request: AgentUpdateRequest): Promise<AgentDetailResponse> {
    const response = await fetch(`${AGENT_API.baseUrl}/api/agents/${agentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<AgentDetailResponse>(response);
  },

  /**
   * Delete agent
   */
  async deleteAgent(agentId: string): Promise<void> {
    const response = await fetch(`${AGENT_API.baseUrl}/api/agents/${agentId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new ApiError(response.status, null, `Failed to delete agent: ${response.statusText}`);
    }
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${AGENT_API.baseUrl}/health`);
    return handleResponse<HealthResponse>(response);
  },
} as const;

// ============================================================================
// Docker Orchestrator API Client (Port 8002)
// ============================================================================

const DOCKER_API = API_CONFIG.dockerOrchestrator;

export const dockerOrchestratorApi = {
  /**
   * Deploy agent to container
   */
  async deployAgent(request: DeployAgentRequest): Promise<DeploymentResponse> {
    const response = await fetch(`${DOCKER_API.baseUrl}/api/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<DeploymentResponse>(response);
  },

  /**
   * Remove deployment
   */
  async removeDeployment(deploymentId: string): Promise<void> {
    const response = await fetch(`${DOCKER_API.baseUrl}/api/deploy/${deploymentId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new ApiError(response.status, null, `Failed to remove deployment: ${response.statusText}`);
    }
  },

  /**
   * List containers
   */
  async listContainers(params?: {
    all?: boolean;
    status?: 'running' | 'stopped' | 'paused' | 'all';
    agent_id?: string;
  }): Promise<ContainerListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.all) searchParams.set('all', 'true');
    if (params?.status) searchParams.set('status', params.status);
    if (params?.agent_id) searchParams.set('agent_id', params.agent_id);

    const url = `${DOCKER_API.baseUrl}/api/containers?${searchParams.toString()}`;
    const response = await fetch(url);
    return handleResponse<ContainerListResponse>(response);
  },

  /**
   * Get container details
   */
  async getContainer(containerId: string): Promise<ContainerInfo> {
    const response = await fetch(`${DOCKER_API.baseUrl}/api/containers/${containerId}`);
    return handleResponse<ContainerInfo>(response);
  },

  /**
   * Start container
   */
  async startContainer(containerId: string): Promise<ActionResponse> {
    const response = await fetch(`${DOCKER_API.baseUrl}/api/containers/${containerId}/start`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  /**
   * Stop container
   */
  async stopContainer(containerId: string, timeout?: number): Promise<ActionResponse> {
    const response = await fetch(`${DOCKER_API.baseUrl}/api/containers/${containerId}/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timeout }),
    });
    return handleResponse<ActionResponse>(response);
  },

  /**
   * Restart container
   */
  async restartContainer(containerId: string, timeout?: number): Promise<ActionResponse> {
    const response = await fetch(`${DOCKER_API.baseUrl}/api/containers/${containerId}/restart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timeout }),
    });
    return handleResponse<ActionResponse>(response);
  },

  /**
   * Execute command in container
   */
  async execInContainer(containerId: string, command: string[]): Promise<{ exit_code: number; output: string }> {
    const response = await fetch(`${DOCKER_API.baseUrl}/api/containers/${containerId}/exec`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    });
    return handleResponse(response);
  },

  /**
   * Remove container
   */
  async removeContainer(containerId: string, options?: { force?: boolean; remove_volumes?: boolean }): Promise<void> {
    const response = await fetch(`${DOCKER_API.baseUrl}/api/containers/${containerId}/remove`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options || {}),
    });
    if (!response.ok) {
      throw new ApiError(response.status, null, `Failed to remove container: ${response.statusText}`);
    }
  },

  /**
   * Get container metrics
   */
  async getContainerMetrics(containerId: string): Promise<MetricsResponse> {
    const response = await fetch(`${DOCKER_API.baseUrl}/api/containers/${containerId}/metrics`);
    return handleResponse<MetricsResponse>(response);
  },

  /**
   * Get container logs
   */
  async getContainerLogs(
    containerId: string,
    params?: {
      tail?: number;
      since?: string;
      timestamps?: boolean;
      offset?: number;
      limit?: number;
    }
  ): Promise<LogsResponse> {
    const searchParams = new URLSearchParams();
    if (params?.tail) searchParams.set('tail', String(params.tail));
    if (params?.since) searchParams.set('since', params.since);
    if (params?.timestamps !== undefined) searchParams.set('timestamps', String(params.timestamps));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    if (params?.limit) searchParams.set('limit', String(params.limit));

    const url = `${DOCKER_API.baseUrl}/api/logs/${containerId}?${searchParams.toString()}`;
    const response = await fetch(url);
    return handleResponse<LogsResponse>(response);
  },

  /**
   * Create log stream connection (Server-Sent Events)
   */
  streamContainerLogs(containerId: string, onLog: (entry: LogEntry) => void, onError?: (error: Error) => void): () => void {
    const eventSource = new EventSource(`${DOCKER_API.baseUrl}/api/logs/${containerId}/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.level && data.message) {
          onLog(data as LogEntry);
        }
      } catch {
        // Non-JSON message, ignore
      }
    };

    eventSource.onerror = (error) => {
      onError?.(new Error('Log stream connection error'));
      eventSource.close();
    };

    // Return cleanup function
    return () => {
      eventSource.close();
    };
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${DOCKER_API.baseUrl}/health`);
    return handleResponse<HealthResponse>(response);
  },
} as const;

// ============================================================================
// React Hooks (if using React)
// ============================================================================

export function createApiHooks() {
  // These are placeholder implementations that can be expanded
  // with a state management library like SWR, React Query, or Zustand

  return {
    useAgentGenerator: () => agentGeneratorApi,
    useDockerOrchestrator: () => dockerOrchestratorApi,
  };
}

// ============================================================================
// Export
// ============================================================================

export const api = {
  agentGenerator: agentGeneratorApi,
  dockerOrchestrator: dockerOrchestratorApi,
} as const;

export default api;
