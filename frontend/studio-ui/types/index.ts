/**
 * Studio UI Types
 * Types specific to the Agent Builder interface
 */

// ============================================================================
// Re-export shared types
// ============================================================================

export type {
  GenerateAgentRequest,
  GenerateAgentResponse,
  ValidateCodeRequest,
  ValidateCodeResponse,
  AgentListResponse,
  AgentDetailResponse,
  AgentUpdateRequest,
  AgentInfo,
  HTTPValidationError,
  AgentComplexity,
  AgentTaskType,
  LLMProvider,
  // Docker Orchestrator types
  DeployAgentRequest,
  DeploymentResponse,
} from '../../shared/types';

export { AVAILABLE_TOOLS, DEFAULT_AGENT_FORM } from '../../shared/types';

export type {
  AgentFormData,
  ToolId,
  AsyncState,
  LoadingState,
  LogEntry,
  LogStreamEvent,
} from '../../shared/types';

// ============================================================================
// Studio UI Specific Types
// ============================================================================

/**
 * Builder page section identifiers
 */
export type BuilderSection = 'description' | 'type' | 'tools' | 'advanced' | 'deploy';

/**
 * Code editor file tabs
 */
export type CodeTab = 'flow.py' | 'agents.yaml' | 'requirements.txt' | 'state.py';

/**
 * Generation state for the builder
 */
export type GenerationState = 'idle' | 'analyzing' | 'generating' | 'validating' | 'complete' | 'error';

/**
 * Validation status for code preview
 */
export interface ValidationStatus {
  isValid: boolean;
  errors: Array<{
    line?: number;
    column?: number;
    message: string;
    severity: 'error' | 'warning' | 'info';
  }>;
  warnings: Array<{
    line?: number;
    message: string;
  }>;
  score: number;
}

/**
 * Code file state
 */
export interface CodeFile {
  filename: CodeTab;
  content: string;
  language: 'python' | 'yaml' | 'text';
  isDirty: boolean;
}

/**
 * Prompt suggestion chip
 */
export interface PromptSuggestion {
  id: string;
  label: string;
  prompt: string;
}

/**
 * Available prompt suggestions
 */
export const PROMPT_SUGGESTIONS: PromptSuggestion[] = [
  {
    id: 'research',
    label: 'Research Agent',
    prompt: 'Create a web research agent that searches for information about a topic and summarizes the findings in a structured report.',
  },
  {
    id: 'data-analysis',
    label: 'Data Analyzer',
    prompt: 'Build an agent that analyzes CSV data, identifies patterns, and generates insights with visualizations.',
  },
  {
    id: 'code-review',
    label: 'Code Reviewer',
    prompt: 'Design an agent that reviews Python code for best practices, potential bugs, and suggests improvements.',
  },
  {
    id: 'content-writer',
    label: 'Content Writer',
    prompt: 'Create an agent that writes blog posts on technical topics with proper structure and SEO optimization.',
  },
  {
    id: 'multi-research',
    label: 'Research Team',
    prompt: 'Build a team of 3 agents: one to gather data from multiple sources, one to analyze and cross-reference findings, and one to compile a comprehensive report.',
  },
];

/**
 * Advanced options form data
 */
export interface AdvancedOptions {
  provider: 'zai' | 'openai' | 'anthropic' | 'openrouter';
  model: string;
  memoryType: 'none' | 'buffer' | 'vector';
  analyticsEnabled: boolean;
}

/**
 * Default advanced options
 */
export const DEFAULT_ADVANCED_OPTIONS: AdvancedOptions = {
  provider: 'zai',
  model: 'default',
  memoryType: 'none',
  analyticsEnabled: false,
};

/**
 * Agent summary for list views
 * Used by the /agents page to display saved agents
 */
export interface AgentSummary {
  agent_id: string;
  agent_name: string;
  description: string;
  complexity: string;
  task_type: string;
  created_at: string;
  updated_at?: string;
  is_active?: boolean;
  tags?: string[];
}

/**
 * Regenerate request for agent modification
 */
export interface RegenerateRequest {
  agent_id: string;
  feedback: string;
  previous_code: string;
}

/**
 * Generic error response
 */
export interface ErrorResponse {
  detail: string | { message: string } | Array<{ msg: string; loc: string[] }>;
}

/**
 * Model options by provider
 */
export const MODELS_BY_PROVIDER: Record<string, string[]> = {
  zai: ['default'],
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-opus-4-6', 'claude-sonnet-4-5', 'claude-3-5-sonnet', 'claude-3-haiku'],
  openrouter: ['auto', 'anthropic/claude-opus-4', 'openai/gpt-4o'],
};
