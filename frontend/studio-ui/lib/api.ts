/**
 * Studio UI API Client
 * Type-safe API client specifically for the Studio UI
 */

import type {
  GenerateAgentRequest,
  GenerateAgentResponse,
  ValidateCodeRequest,
  ValidateCodeResponse,
  AgentListResponse,
  AgentDetailResponse,
  AgentUpdateRequest,
  DeployAgentRequest,
  DeploymentResponse,
  HTTPValidationError,
  RegenerateRequest,
  ErrorResponse,
  AgentSummary,
  FileBrowserResponse,
} from '../types';

import type { GenerationState, ValidationStatus, CodeTab } from '../types';

// ============================================================================
// API Configuration
// ============================================================================

const AGENT_API_URL = process.env.NEXT_PUBLIC_AGENT_GENERATOR_URL || 'http://localhost:4521';
const DOCKER_API_URL = process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:4522';

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
    const errorMessage = typeof errorData?.detail === 'string'
      ? errorData.detail
      : (errorData?.detail as { message?: string })?.message
      || `HTTP ${response.status}: ${response.statusText}`;
    throw new ApiError(
      response.status,
      errorData,
      errorMessage
    );
  }
  return response.json();
}

// ============================================================================
// Studio API Functions
// ============================================================================

/**
 * Generate an agent from natural language
 */
export async function generateAgent(request: GenerateAgentRequest): Promise<GenerateAgentResponse> {
  const response = await fetch(`${AGENT_API_URL}/api/generate-agent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<GenerateAgentResponse>(response);
}

/**
 * Regenerate an agent with modifications
 * NOTE: Backend expects query params, not JSON body
 */
export async function regenerateAgent(request: RegenerateRequest): Promise<GenerateAgentResponse> {
  const params = new URLSearchParams({
    agent_id: request.agent_id,
    feedback: request.feedback,
    previous_code: request.previous_code,
  });
  const response = await fetch(`${AGENT_API_URL}/api/regenerate?${params}`, {
    method: 'POST',
  });
  return handleResponse<GenerateAgentResponse>(response);
}

/**
 * Validate generated code
 */
export async function validateCode(code: string, strictMode = false): Promise<ValidationStatus> {
  const response = await fetch(`${AGENT_API_URL}/api/validate-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });

  const data = await handleResponse<ValidateCodeResponse>(response);

  return {
    isValid: data.is_valid ?? false,
    errors: data.syntax_errors?.map((msg: string) => ({
      line: undefined,
      column: undefined,
      message: msg,
      severity: 'error' as const,
    })) ?? [],
    warnings: data.warnings?.map((msg: string) => ({
      line: undefined,
      message: msg,
    })) ?? [],
    score: data.pattern_compliance_score ?? 0,
  };
}

/**
 * Get validation rules
 */
export async function getValidationRules() {
  const response = await fetch(`${AGENT_API_URL}/api/validation-rules`);
  return handleResponse<{
    rules: Array<{ name: string; description: string; severity: 'error' | 'warning' | 'info' }>
  }>(response);
}

/**
 * List saved agents
 */
export async function listAgents(params?: {
  limit?: number;
  offset?: number;
  task_type?: string;
  complexity?: 'simple' | 'moderate' | 'complex';
}): Promise<{ agents: AgentSummary[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));
  if (params?.task_type) searchParams.set('task_type', params.task_type);
  if (params?.complexity) searchParams.set('complexity', params.complexity);

  const url = `${AGENT_API_URL}/api/agents?${searchParams.toString()}`;
  const response = await fetch(url);
  const data = await handleResponse<{ agents?: Record<string, unknown>[]; total: number }>(response);
  return {
    agents: (data.agents || []) as unknown as AgentSummary[],
    total: data.total,
  };
}

/**
 * Get agent by ID
 */
export async function getAgent(agentId: string): Promise<AgentDetailResponse> {
  const response = await fetch(`${AGENT_API_URL}/api/agents/${agentId}`);
  return handleResponse<AgentDetailResponse>(response);
}

/**
 * Update agent
 */
export async function updateAgent(agentId: string, request: AgentUpdateRequest): Promise<AgentDetailResponse> {
  const response = await fetch(`${AGENT_API_URL}/api/agents/${agentId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<AgentDetailResponse>(response);
}

/**
 * Delete agent
 */
export async function deleteAgent(agentId: string): Promise<void> {
  const response = await fetch(`${AGENT_API_URL}/api/agents/${agentId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new ApiError(response.status, null, `Failed to delete agent: ${response.statusText}`);
  }
}

/**
 * Deploy agent to container via the Agent Generator proxy.
 * The backend handles the Generator → Orchestrator handoff internally.
 * Frontend no longer needs direct access to the Docker Orchestrator.
 */
export async function deployAgent(
  agentId: string,
  agentName: string,
  flowCode: string,
  agentsYaml: string,
  requirements?: string,
  options?: {
    auto_start?: boolean;
    memory_limit?: string;
    cpu_limit?: number;
    environment_vars?: Record<string, string>;
    output_config?: { postgres: boolean; files: boolean };
    output_path?: string;
    output_format?: 'markdown' | 'html';
  }
): Promise<DeploymentResponse> {
  const request = {
    agent_id: agentId,
    agent_name: agentName,
    flow_code: flowCode,
    agents_yaml: agentsYaml || '',
    auto_start: options?.auto_start ?? true,
    memory_limit: options?.memory_limit ?? '512m',
    cpu_limit: options?.cpu_limit ?? 1.0,
    output_config: options?.output_config,
    output_path: options?.output_path,
    output_format: options?.output_format,
  };

  const response = await fetch(`${AGENT_API_URL}/api/deploy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  return handleResponse<DeploymentResponse>(response);
}

/**
 * Generate and deploy in a single server-side call.
 * The backend handles the Generator → Orchestrator handoff internally.
 */
export async function generateAndDeploy(
  request: GenerateAgentRequest
): Promise<{ generation: GenerateAgentResponse; deployment: DeploymentResponse }> {
  const response = await fetch(`${AGENT_API_URL}/api/generate-and-deploy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<{ generation: GenerateAgentResponse; deployment: DeploymentResponse }>(response);
}

/**
 * Health check for agent generator
 */
export async function healthCheck() {
  const response = await fetch(`${AGENT_API_URL}/health`);
  return handleResponse(response);
}

/**
 * Browse filesystem directory
 */
export async function browseFilesystem(path?: string): Promise<FileBrowserResponse> {
  const url = path
    ? `${DOCKER_API_URL}/filesystem/browse?path=${encodeURIComponent(path)}`
    : `${DOCKER_API_URL}/filesystem/browse`;
  const response = await fetch(url);
  return handleResponse<FileBrowserResponse>(response);
}

/**
 * Create a directory in the filesystem
 */
export async function createDirectory(path: string): Promise<{ path: string }> {
  const response = await fetch(`${DOCKER_API_URL}/filesystem/mkdir`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  return handleResponse<{ path: string }>(response);
}

// ============================================================================
// React Query / SWR Keys (if using those libraries)
// ============================================================================

export const queryKeys = {
  agents: {
    list: (params?: Record<string, unknown>) => ['agents', 'list', params] as const,
    detail: (id: string) => ['agents', 'detail', id] as const,
    validationRules: () => ['agents', 'validation-rules'] as const,
  },
} as const;

// ============================================================================
// Export all
// ============================================================================

export const studioApi = {
  generateAgent,
  regenerateAgent,
  validateCode,
  getValidationRules,
  listAgents,
  getAgent,
  updateAgent,
  deleteAgent,
  deployAgent,
  generateAndDeploy,
  healthCheck,
  browseFilesystem,
  createDirectory,
} as const;

export default studioApi;
