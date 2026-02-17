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
export type ValidateCodeRequest = import('./agent-generator').components['schemas']['ValidateCodeRequest'];
export type AgentUpdateRequest = import('./agent-generator').components['schemas']['AgentUpdateRequest'];

// Response Types
export type GenerateAgentResponse = import('./agent-generator').components['schemas']['GenerateAgentResponse'];
export type ValidateCodeResponse = import('./agent-generator').components['schemas']['ValidateCodeResponse'];
export type AgentListResponse = import('./agent-generator').components['schemas']['AgentListResponse'];
export type AgentInfo = import('./agent-generator').components['schemas']['AgentInfo'];
export type AgentDetailResponse = import('./agent-generator').components['schemas']['AgentDetailResponse'];

// Shared Types
export type HealthResponse = import('./agent-generator').components['schemas']['HealthResponse'];
export type HTTPValidationError = import('./agent-generator').components['schemas']['HTTPValidationError'];

// Enums
export type AgentComplexity = 'simple' | 'moderate' | 'complex';
export type AgentTaskType = 'research' | 'development' | 'automation' | 'analysis' | 'general';
export type LLMProvider = 'zai' | 'openai' | 'anthropic' | 'openrouter' | 'google' | 'mistral';

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
  agent_name: string;
  complexity: AgentComplexity;
  task_type: AgentTaskType;
  max_agents: number;
  tools_requested: string[];
  llm_provider: LLMProvider;
  include_memory: boolean;
  include_analytics: boolean;
}

export const DEFAULT_AGENT_FORM: AgentFormData = {
  description: '',
  agent_name: '',
  complexity: 'moderate',
  task_type: 'general',
  max_agents: 3,
  tools_requested: [],
  llm_provider: 'zai',
  include_memory: true,
  include_analytics: true,
};

// Available tools for selection - CrewAI compatible tool definitions
export const AVAILABLE_TOOLS = [
  // Web & Search Tools
  { id: 'SerperDevTool', name: 'Web Search (Serper)', description: 'Search the web using Serper API', category: 'web' },
  { id: 'DuckDuckGoSearchRun', name: 'Web Search (DuckDuckGo)', description: 'Search the web using DuckDuckGo', category: 'web' },
  { id: 'ScrapeWebsiteTool', name: 'Web Scraper', description: 'Extract content from web pages', category: 'web' },
  { id: 'WebsiteSearchTool', name: 'Website Search', description: 'Search within a specific website', category: 'web' },
  { id: 'SeleniumScrapingTool', name: 'Browser Scraper', description: 'Scrape JavaScript-rendered pages', category: 'web' },
  { id: 'FirecrawlScrapeWebsiteTool', name: 'Firecrawl Scraper', description: 'Advanced web scraping with Firecrawl', category: 'web' },

  // File & Document Tools
  { id: 'FileReadTool', name: 'File Reader', description: 'Read local files', category: 'files' },
  { id: 'DirectoryReadTool', name: 'Directory Reader', description: 'List and read directory contents', category: 'files' },
  { id: 'DirectorySearchTool', name: 'Directory Search', description: 'Search for files in directories', category: 'files' },
  { id: 'CSVSearchTool', name: 'CSV Search', description: 'Search and query CSV files', category: 'files' },
  { id: 'JSONSearchTool', name: 'JSON Search', description: 'Search JSON files', category: 'files' },
  { id: 'XMLSearchTool', name: 'XML Search', description: 'Search XML files', category: 'files' },
  { id: 'PDFSearchTool', name: 'PDF Search', description: 'Search and extract from PDFs', category: 'files' },
  { id: 'DOCXSearchTool', name: 'DOCX Search', description: 'Search Word documents', category: 'files' },
  { id: 'GithubSearchTool', name: 'GitHub Search', description: 'Search GitHub repositories', category: 'files' },

  // Code & Development Tools
  { id: 'CodeInterpreterTool', name: 'Code Interpreter', description: 'Execute Python code', category: 'code' },
  { id: 'CodeDocsSearchTool', name: 'Code Docs Search', description: 'Search code documentation', category: 'code' },
  { id: 'CodeSearchTool', name: 'Code Search', description: 'Search codebases', category: 'code' },
  { id: 'VBCodeInterpreterTool', name: 'VS Code Interpreter', description: 'Execute code in VS Code context', category: 'code' },

  // Database Tools
  { id: 'PostgreSQLTool', name: 'PostgreSQL', description: 'Query PostgreSQL databases', category: 'database' },
  { id: 'MySQLTool', name: 'MySQL', description: 'Query MySQL databases', category: 'database' },
  { id: 'SQLiteTool', name: 'SQLite', description: 'Query SQLite databases', category: 'database' },
  { id: 'SnowflakeTool', name: 'Snowflake', description: 'Query Snowflake data warehouse', category: 'database' },

  // Communication Tools
  { id: 'EmailTool', name: 'Email', description: 'Send and manage emails', category: 'communication' },
  { id: 'SlackTool', name: 'Slack', description: 'Send messages to Slack channels', category: 'communication' },
  { id: 'DiscordTool', name: 'Discord', description: 'Send messages to Discord', category: 'communication' },
  { id: 'TelegramTool', name: 'Telegram', description: 'Send Telegram messages', category: 'communication' },
  { id: 'WhatsAppTool', name: 'WhatsApp', description: 'Send WhatsApp messages', category: 'communication' },

  // AI & LLM Tools
  { id: 'AzureAiSearchTool', name: 'Azure AI Search', description: 'Search with Azure AI', category: 'ai' },
  { id: 'ChatOllama', name: 'Ollama Chat', description: 'Chat with local Ollama models', category: 'ai' },
  { id: 'LlamaIndexTool', name: 'LlamaIndex', description: 'Query documents with LlamaIndex', category: 'ai' },

  // Cloud & Infrastructure Tools
  { id: 'AWSTool', name: 'AWS', description: 'Interact with AWS services', category: 'cloud' },
  { id: 'GCSTool', name: 'Google Cloud Storage', description: 'Access GCS buckets', category: 'cloud' },
  { id: 'AzureStorageTool', name: 'Azure Storage', description: 'Access Azure storage', category: 'cloud' },
  { id: 'S3Tool', name: 'S3 Reader', description: 'Read from S3 buckets', category: 'cloud' },
  { id: 'CloudTool', name: 'Cloud Operations', description: 'General cloud operations', category: 'cloud' },

  // Data & Analytics Tools
  { id: 'PandasTool', name: 'Pandas', description: 'Data analysis with Pandas', category: 'data' },
  { id: 'NL2SQLTool', name: 'NL2SQL', description: 'Natural language to SQL', category: 'data' },
  { id: 'DatabricksTool', name: 'Databricks', description: 'Query Databricks', category: 'data' },

  // Browser Automation Tools
  { id: 'BrowserbaseLoadTool', name: 'Browserbase', description: 'Browser automation with Browserbase', category: 'browser' },
  { id: 'PlaywrightTool', name: 'Playwright', description: 'Browser automation with Playwright', category: 'browser' },
  { id: 'ScrapflyScrapeWebsiteTool', name: 'Scrapfly', description: 'Web scraping with Scrapfly', category: 'browser' },

  // Content & Media Tools
  { id: 'YoutubeVideoSearchTool', name: 'YouTube Search', description: 'Search YouTube videos', category: 'media' },
  { id: 'YoutubeChannelSearchTool', name: 'YouTube Channel', description: 'Search YouTube channels', category: 'media' },
  { id: 'EXASearchTool', name: 'EXA Search', description: 'AI-powered web search', category: 'web' },

  // Utility Tools
  { id: 'BaseTool', name: 'Custom Tool', description: 'Base class for custom tools', category: 'utility' },
] as const;

export type ToolId = typeof AVAILABLE_TOOLS[number]['id'];
