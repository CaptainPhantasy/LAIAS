/**
 * LAIAS Shared Types
 * Auto-generated from OpenAPI specs with convenience re-exports
 */

// ============================================================================
// Agent Generator Types (Port 8001)
// ============================================================================

export type {
  paths as AgentGeneratorPaths,
  operations as AgentGeneratorOperations,
  components as AgentGeneratorComponents,
} from './agent-generator';

// Request Types
export type GenerateAgentRequest = import('./agent-generator').components['schemas']['GenerateAgentRequest'];
export type RegenerateRequest = import('./agent-generator').components['schemas']['RegenerateRequest'];
export type ValidateCodeRequest = import('./agent-generator').components['schemas']['ValidateCodeRequest'];
export type AgentUpdateRequest = import('./agent-generator').components['schemas']['AgentUpdateRequest'];

// Response Types
export type GenerateAgentResponse = import('./agent-generator').components['schemas']['GenerateAgentResponse'];
export type ValidateCodeResponse = import('./agent-generator').components['schemas']['ValidateCodeResponse'];
export type AgentListResponse = import('./agent-generator').components['schemas']['AgentListResponse'];
export type AgentSummary = import('./agent-generator').components['schemas']['AgentSummary'];
export type AgentDetailResponse = import('./agent-generator').components['schemas']['AgentDetailResponse'];

// Shared Types
export type HealthResponse = import('./agent-generator').components['schemas']['HealthResponse'];
export type HealthCheck = import('./agent-generator').components['schemas']['HealthCheck'];
export type ErrorResponse = import('./agent-generator').components['schemas']['ErrorResponse'];

// Enums
export type AgentComplexity = 'simple' | 'moderate' | 'complex';
export type AgentTaskType = 'research' | 'development' | 'automation' | 'analysis' | 'general';
export type LLMProvider = 'zai' | 'openai' | 'anthropic' | 'openrouter';

// ============================================================================
// Docker Orchestrator Types (Port 8002)
// ============================================================================

export type {
  paths as DockerOrchestratorPaths,
  operations as DockerOrchestratorOperations,
  components as DockerOrchestratorComponents,
} from './docker-orchestrator';

// Request Types
export type DeployAgentRequest = import('./docker-orchestrator').components['schemas']['DeployAgentRequest'];

// Response Types
export type DeploymentResponse = import('./docker-orchestrator').components['schemas']['DeploymentResponse'];
export type ContainerListResponse = import('./docker-orchestrator').components['schemas']['ContainerListResponse'];
export type ContainerInfo = import('./docker-orchestrator').components['schemas']['ContainerInfo'];
export type ResourceUsage = import('./docker-orchestrator').components['schemas']['ResourceUsage'];
export type ActionResponse = import('./docker-orchestrator').components['schemas']['ActionResponse'];
export type ExecResponse = import('./docker-orchestrator').components['schemas']['ExecResponse'];
export type LogsResponse = import('./docker-orchestrator').components['schemas']['LogsResponse'];
export type MetricsResponse = import('./docker-orchestrator').components['schemas']['MetricsResponse'];

// Docker-specific Health Types (namespaced to avoid conflict)
export type DockerHealthResponse = import('./docker-orchestrator').components['schemas']['HealthResponse'];
export type DockerHealthCheck = import('./docker-orchestrator').components['schemas']['HealthCheck'];
export type DockerErrorResponse = import('./docker-orchestrator').components['schemas']['ErrorResponse'];

// Enums
export type ContainerStatus = 'running' | 'stopped' | 'paused' | 'exited' | 'error';
export type DeploymentStatus = 'created' | 'running' | 'stopped' | 'error';
export type LogLevel = 'debug' | 'info' | 'warning' | 'error';
export type ServiceHealthStatus = 'healthy' | 'degraded' | 'unhealthy';

// ============================================================================
// Log Entry Types (for streaming)
// ============================================================================

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  raw?: string;
}

// ============================================================================
// API Client Configuration
// ============================================================================

export interface ApiClientConfig {
  baseUrl: string;
  headers?: Record<string, string>;
  timeout?: number;
}

export const API_CONFIG = {
  agentGenerator: {
    baseUrl: process.env.NEXT_PUBLIC_AGENT_GENERATOR_URL || 'http://localhost:8001',
    timeout: 30000, // 30s for generation
  },
  dockerOrchestrator: {
    baseUrl: process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:8002',
    timeout: 10000, // 10s for container ops
  },
} as const;

// ============================================================================
// WebSocket Event Types (Log Streaming)
// ============================================================================

export interface LogStreamEvent {
  id: string;
  event: 'log' | 'connected' | 'disconnected' | 'error';
  data: LogEntry | { message: string };
}

// ============================================================================
// UI State Types
// ============================================================================

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Form Types (Studio UI)
// ============================================================================

export interface AgentFormData {
  description: string;
  complexity: AgentComplexity;
  task_type: AgentTaskType;
  max_agents: number;
  tools_requested: string[];
  provider: LLMProvider;
  save_agent: boolean;
}

export const DEFAULT_AGENT_FORM: AgentFormData = {
  description: '',
  complexity: 'moderate',
  task_type: 'general',
  max_agents: 3,
  tools_requested: [],
  provider: 'zai',
  save_agent: true,
};

// Available tools for selection
export const AVAILABLE_TOOLS = [
  { id: 'web_search', name: 'Web Search', description: 'Search the web for information' },
  { id: 'web_scraper', name: 'Web Scraper', description: 'Extract content from web pages' },
  { id: 'code_interpreter', name: 'Code Interpreter', description: 'Execute Python code' },
  { id: 'file_manager', name: 'File Manager', description: 'Read and write files' },
  { id: 'database', name: 'Database', description: 'Query database connections' },
  { id: 'api_connector', name: 'API Connector', description: 'Make HTTP requests to external APIs' },
] as const;

export type ToolId = typeof AVAILABLE_TOOLS[number]['id'];
