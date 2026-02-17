'use client';

import { useState, useCallback, useEffect, useRef, Suspense } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Sparkles,
  ArrowRight,
  Play,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import Link from 'next/link';

import { useBuilderStore } from '@/store';
import { studioApi } from '@/lib/api';
import { AVAILABLE_TOOLS, PROMPT_SUGGESTIONS, MODELS_BY_PROVIDER } from '@/types';
import type { AgentFormData, CodeTab } from '@/types';
import { Button } from '@/components/ui/button';
import { Input, Textarea, Select } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { AppShell } from '@/components/layout/app-shell';
import { SectionPanel, ToolTile, PromptSuggestions } from '@/components/agent-builder';
import { CodePanel } from '@/components/code-editor';
import { cn, debounce } from '@/lib/utils';

const API_BASE = typeof window !== 'undefined'
  ? (window.location.hostname.includes('ngrok') ? 'https://laias-api.ngrok-free.app' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'))
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001');
const FETCH_TIMEOUT = 8000; // 8 second timeout for template loading

// ============================================================================
// Form Schema
// ============================================================================

const formSchema = z.object({
  description: z.string().min(10, 'Description must be at least 10 characters').max(2000),
  agent_name: z.string().optional(), // Auto-generated from description if not provided
  complexity: z.enum(['simple', 'moderate', 'complex']),
  task_type: z.enum(['research', 'development', 'automation', 'analysis', 'general']),
  max_agents: z.number().min(1).max(10),
  tools_requested: z.array(z.string()),
  provider: z.enum(['zai', 'openai', 'anthropic', 'openrouter']),
  model: z.string().optional(), // Model selection for chosen provider
});

type FormValues = z.infer<typeof formSchema>;

// ============================================================================
// Page Component
// ============================================================================

function CreateAgentPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [isGenerating, setIsGenerating] = useState(false);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [loadingTemplate, setLoadingTemplate] = useState(false);
  const [templateError, setTemplateError] = useState<string | null>(null);
  const [templateName, setTemplateName] = useState<string | null>(null);
  const [templateLoaded, setTemplateLoaded] = useState(false);
  const [activeTemplateId, setActiveTemplateId] = useState<string | null>(null);

  const {
    generationState,
    generationError,
    activeTab,
    validationStatus,
    codeFiles,
    generatedCode,
    setGenerationState,
    setGeneratedCode,
    setGenerationError,
    setValidationStatus,
    setActiveTab,
    updateCodeContent,
    resetGeneration,
  } = useBuilderStore();

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    trigger,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      description: '',
      agent_name: '',
      complexity: 'moderate',
      task_type: 'general',
      max_agents: 3,
      tools_requested: [],
      provider: 'zai',
      model: 'default',
    },
  });

  const watchedDescription = watch('description');
  const watchedTools = watch('tools_requested');
  const watchedProvider = watch('provider');
  const watchedModel = watch('model');

  // Load template data if coming from templates page
  useEffect(() => {
    const loadTemplate = async () => {
      // Get activeTemplateId from searchParams or window.location
      let activeTemplateId = searchParams.get('template');

      // Fallback to window.location if searchParams is empty (SSR hydration issue)
      if (!activeTemplateId && typeof window !== 'undefined') {
        const params = new URLSearchParams(window.location.search);
        activeTemplateId = params.get('template');
      }

      console.log('[CreatePage] loadTemplate triggered, activeTemplateId:', activeTemplateId);

      if (!activeTemplateId) {
        setTemplateError(null);
        setTemplateName(null);
        setActiveTemplateId(null);
        return;
      }

      // Set active template ID for UI display
      setActiveTemplateId(activeTemplateId);

      // Prevent double-loading
      if (templateLoaded) {
        console.log('[CreatePage] Template already loaded, skipping');
        return;
      }

      setLoadingTemplate(true);
      setTemplateError(null);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);

      try {
        const url = `${API_BASE}/api/templates/${activeTemplateId}`;
        console.log('[CreatePage] Fetching template from:', url);

        const response = await fetch(url, {
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`Template "${activeTemplateId}" not found. It may have been removed or renamed.`);
          }
          throw new Error(`Failed to load template: HTTP ${response.status}`);
        }

        const template = await response.json();
        console.log('[CreatePage] Template loaded:', template);
        setTemplateName(template.name || activeTemplateId);
        setTemplateLoaded(true);

        // Pre-fill form with template data
        if (template.sample_prompts?.[0]) {
          console.log('[CreatePage] Setting description:', template.sample_prompts[0]);
          setValue('description', template.sample_prompts[0], { shouldValidate: true });
        }
        if (template.default_complexity) {
          console.log('[CreatePage] Setting complexity:', template.default_complexity);
          setValue('complexity', template.default_complexity);
        }
        if (template.category) {
          console.log('[CreatePage] Setting task_type:', template.category);
          // Map category to valid task_type
          const validTaskTypes = ['research', 'development', 'automation', 'analysis', 'general'];
          const taskType = validTaskTypes.includes(template.category) ? template.category : 'general';
          setValue('task_type', taskType as any);
        }
        if (template.default_tools?.length) {
          console.log('[CreatePage] Setting tools:', template.default_tools);
          setValue('tools_requested', template.default_tools);
        }
        if (template.suggested_config?.llm_provider) {
          // Map llm_provider to valid provider
          const validProviders = ['zai', 'openai', 'anthropic', 'openrouter'];
          const provider = template.suggested_config.llm_provider.toLowerCase();
          const mappedProvider = validProviders.includes(provider) ? provider : 'zai';
          console.log('[CreatePage] Setting provider:', mappedProvider);
          setValue('provider', mappedProvider as any);
        }
        if (template.suggested_config?.max_agents) {
          console.log('[CreatePage] Setting max_agents:', template.suggested_config.max_agents);
          setValue('max_agents', template.suggested_config.max_agents);
        }

        console.log('[CreatePage] Template applied successfully');
      } catch (err) {
        console.error('[CreatePage] Template load error:', err);
        if (err instanceof Error && err.name === 'AbortError') {
          setTemplateError('Loading template timed out. Please check your connection and try again.');
        } else {
          setTemplateError(err instanceof Error ? err.message : 'Failed to load template');
        }
      } finally {
        setLoadingTemplate(false);
      }
    };

    loadTemplate();
  }, [searchParams, setValue, templateLoaded]);

  // Debounced validation for description field (500ms per blueprint E.3)
  const debouncedValidate = useRef(
    debounce((value: string) => {
      // Trigger validation on debounce for description
      if (value && value.length >= 10) {
        trigger('description');
      }
    }, 500)
  ).current;

  useEffect(() => {
    if (watchedDescription) {
      debouncedValidate(watchedDescription);
    }
  }, [watchedDescription, debouncedValidate]);

  // Tool toggle handler - matches blueprint signature
  const handleToolToggle = useCallback(
    (toolId: string, selected: boolean) => {
      const currentTools = watchedTools || [];
      const newTools = selected
        ? [...currentTools, toolId]
        : currentTools.filter((t) => t !== toolId);
      setValue('tools_requested', newTools);
    },
    [watchedTools, setValue]
  );

  // Prompt suggestion handler
  const handlePromptSelect = useCallback(
    (prompt: string) => {
      setValue('description', prompt);
    },
    [setValue]
  );

  // Generate agent_name from description if not provided
  const generateAgentName = (description: string): string => {
    // Take first 40 chars, remove special chars, convert to PascalCase
    const words = description
      .slice(0, 50)
      .replace(/[^a-zA-Z0-9\s]/g, '')
      .split(/\s+/)
      .filter(w => w.length > 0)
      .slice(0, 5);
    
    const name = words
      .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join('');
    
    // Ensure it starts with a letter and add Flow suffix
    const pascalName = name.replace(/^[0-9]+/, '') || 'Agent';
    return `${pascalName}Flow`;
  };

  // Generate handler
  const handleGenerate = async (data: FormValues) => {
    setIsGenerating(true);
    setGenerationError(null);
    resetGeneration();
    setGenerationState('analyzing');

    // Generate agent_name from description if not provided
    const agentName = data.agent_name || generateAgentName(data.description);
    console.log('[CreatePage] Generated agent_name:', agentName);

    try {
      setGenerationState('generating');
      
      // Build request payload matching backend Pydantic model
      // Backend requires: agent_name, llm_provider (not provider)
      // Backend does NOT have: save_agent field
      const requestPayload = {
        description: data.description,
        agent_name: agentName,
        complexity: data.complexity,
        task_type: data.task_type,
        max_agents: data.max_agents,
        tools_requested: data.tools_requested.length > 0 ? data.tools_requested : null,
        llm_provider: data.provider, // Map provider -> llm_provider
        model: data.model || undefined, // Include selected model (optional)
      };
      
      console.log('[CreatePage] Sending request:', requestPayload);
      
      const response = await studioApi.generateAgent(requestPayload as any);

      setGeneratedCode({
        agentId: response.agent_id || '',
        flowCode: response.flow_code || '',
        agentsYaml: response.agents_yaml || '',
        requirements: response.requirements?.join('\n') || '',
        stateCode: response.state_class || '',
      });

      setGenerationState('validating');

      // Validate the generated code
      if (response.flow_code) {
        const validation = await studioApi.validateCode(response.flow_code);
        setValidationStatus(validation);
      }

      setGenerationState('complete');
    } catch (error) {
      setGenerationState('error');
      setGenerationError(
        error instanceof Error ? error.message : 'Generation failed. Please try again.'
      );
    } finally {
      setIsGenerating(false);
    }
  };

  // Validate handler
  const handleValidate = async () => {
    const flowCode = codeFiles['flow.py']?.content;
    if (!flowCode) return;

    setGenerationState('validating');
    try {
      const validation = await studioApi.validateCode(flowCode);
      setValidationStatus(validation);
    } catch (error) {
      console.error('Validation failed:', error);
      setGenerationError(error instanceof Error ? error.message : 'Validation failed');
    } finally {
      setGenerationState('complete');
    }
  };

  // Deploy handler
  const handleDeploy = async () => {
    const flowCode = codeFiles['flow.py']?.content;
    const agentsYaml = codeFiles['agents.yaml']?.content;
    const agentId = generatedCode?.agentId || `agent_${Date.now()}`;
    const agentName = `Agent-${Date.now().toString(36)}`;

    if (!flowCode) {
      setGenerationError('No code to deploy. Generate an agent first.');
      return;
    }

    setGenerationState('generating');
    try {
      const deployment = await studioApi.deployAgent(
        agentId,
        agentName,
        flowCode,
        agentsYaml || '',
        codeFiles['requirements.txt']?.content,
        { auto_start: true, memory_limit: '512m' }
      );

      setGenerationState('complete');

      // Navigate to control room to see deployed agent
      window.open(`http://localhost:3001?agent=${deployment.container_id}`, '_blank');

      // TODO: Add proper client-side logging
      console.info('Agent deployed successfully', {
        agentId,
        containerId: deployment.container_id
      });
    } catch (error) {
      setGenerationState('error');
      setGenerationError(
        error instanceof Error ? error.message : 'Deployment failed. Please try again.'
      );
    }
  };

  // Clear template error and start fresh
  const handleClearTemplate = () => {
    router.push('/create');
  };

  // Page actions
  const pageActions = (
    <>
      <Button
        variant="outline"
        onClick={handleValidate}
        disabled={!codeFiles['flow.py']?.content || isGenerating}
      >
        Validate
      </Button>
      <Button
        variant="primary"
        onClick={handleDeploy}
        disabled={!validationStatus?.isValid}
        iconRight={<ArrowRight className="w-4 h-4" />}
      >
        Deploy
      </Button>
    </>
  );

  return (
    <AppShell title="Create Agent" actions={pageActions} fullWidth>
      {/* Template indicator with loading and error states */}
      {activeTemplateId && (
        <div className={cn(
          "border rounded-lg px-4 py-3 flex items-center justify-between",
          templateError
            ? "bg-error/10 border-error/30"
            : loadingTemplate
            ? "bg-surface-2 border-border"
            : "bg-accent-cyan/10 border-accent-cyan/30"
        )}>
          <div className="flex items-center gap-3">
            {loadingTemplate ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-accent-cyan border-t-transparent"></div>
                <span className="text-text-secondary">Loading template: {activeTemplateId}...</span>
              </>
            ) : templateError ? (
              <>
                <svg className="w-5 h-5 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <span className="text-error font-medium">Template Error</span>
                  <span className="text-text-secondary text-sm ml-2">{templateError}</span>
                </div>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 text-accent-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <span className="text-accent-cyan">Using template:</span>
                  <span className="text-text-primary font-medium ml-2">{templateName || activeTemplateId}</span>
                </div>
              </>
            )}
          </div>
          <div className="flex items-center gap-2">
            {templateError && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={templateError ? handleClearTemplate : () => router.push('/templates')}
            >
              {templateError ? 'Start Fresh' : 'Change Template'}
            </Button>
          </div>
        </div>
      )}

      {/* Builder Canvas - CSS Grid per blueprint */}
      <div className="builder-canvas grid grid-cols-1 lg:grid-cols-[240px_1fr_400px] xl:grid-cols-[240px_1fr_400px] gap-4 p-4 pt-2">
        {/* Left: Section Nav */}
        <nav className="hidden lg:block overflow-auto">
          <ul className="space-y-1">
            {[
              { id: 'description', label: 'Description', icon: '1' },
              { id: 'type', label: 'Type', icon: '2' },
              { id: 'tools', label: 'Tools', icon: '3' },
              { id: 'advanced', label: 'Advanced', icon: '4' },
            ].map((section) => (
              <li key={section.id}>
                <a
                  href={`#${section.id}`}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                    'hover:bg-surface',
                    section.id === 'description' && 'bg-surface border-l-2 border-accent-cyan'
                  )}
                >
                  <span className="w-5 h-5 flex items-center justify-center rounded-full bg-bg-tertiary text-xs font-medium">
                    {section.icon}
                  </span>
                  {section.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        {/* Center: Form */}
        <form onSubmit={handleSubmit(handleGenerate)} className="space-y-6 overflow-auto">
          {/* Description */}
          <SectionPanel
            title="Description"
            required
            accentColor="cyan"
          >
            <Controller
              name="description"
              control={control}
              render={({ field }) => (
                <Textarea
                  {...field}
                  disabled={loadingTemplate}
                  placeholder="Describe your AI agent in natural language. Be specific about what it should do, what tools it needs, and how it should behave."
                  rows={6}
                  error={errors.description?.message}
                />
              )}
            />
            <div className="flex justify-between items-center mt-2">
              <span className="text-xs text-text-muted">
                {watchedDescription?.length || 0}/2000
              </span>
            </div>
            <div className="mt-4">
              <p className="text-sm text-text-secondary mb-2">Try a prompt:</p>
              <PromptSuggestions
                suggestions={PROMPT_SUGGESTIONS}
                onSelect={handlePromptSelect}
              />
            </div>
          </SectionPanel>

          {/* Type Configuration */}
          <SectionPanel title="Agent Configuration" accentColor="purple">
            <div className="grid grid-cols-3 gap-4">
              <Controller
                name="complexity"
                control={control}
                render={({ field }) => (
                  <Select
                    label="Complexity"
                    {...field}
                    disabled={loadingTemplate}
                    options={[
                      { value: 'simple', label: 'Simple' },
                      { value: 'moderate', label: 'Moderate' },
                      { value: 'complex', label: 'Complex' },
                    ]}
                  />
                )}
              />
              <Controller
                name="task_type"
                control={control}
                render={({ field }) => (
                  <Select
                    label="Task Type"
                    {...field}
                    disabled={loadingTemplate}
                    options={[
                      { value: 'general', label: 'General' },
                      { value: 'research', label: 'Research' },
                      { value: 'development', label: 'Development' },
                      { value: 'automation', label: 'Automation' },
                      { value: 'analysis', label: 'Analysis' },
                    ]}
                  />
                )}
              />
              <Controller
                name="max_agents"
                control={control}
                render={({ field }) => (
                  <Input
                    label="Max Agents"
                    type="number"
                    min={1}
                    max={10}
                    {...field}
                    disabled={loadingTemplate}
                    onChange={(e) => field.onChange(parseInt(e.target.value, 10) || 1)}
                  />
                )}
              />
            </div>
          </SectionPanel>

          {/* Tools */}
          <SectionPanel title="Tools" accentColor="pink">
            {/* Tool category tabs */}
            <div className="flex flex-wrap gap-2 mb-4">
              {['all', 'web', 'files', 'code', 'database', 'communication', 'cloud', 'ai', 'data', 'browser', 'media', 'utility'].map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => {
                    const toolsEl = document.getElementById('tools-grid');
                    if (toolsEl) {
                      toolsEl.dataset.filter = cat;
                      // Force re-render of tools
                      const event = new CustomEvent('filterchange', { detail: cat });
                      toolsEl.dispatchEvent(event);
                    }
                  }}
                  className={cn(
                    'px-3 py-1.5 text-xs font-medium rounded-full transition-colors',
                    'bg-surface-2 hover:bg-surface border border-border',
                    'capitalize'
                  )}
                >
                  {cat === 'all' ? 'All Tools' : cat}
                </button>
              ))}
            </div>

            {/* Tools grid with categories */}
            <div id="tools-grid" className="space-y-6">
              {/* Group tools by category */}
              {(() => {
                const categories = [...new Set(AVAILABLE_TOOLS.map(t => (t as any).category || 'utility'))];
                return categories.map(category => (
                  <div key={category} className="tools-category" data-category={category}>
                    <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3 capitalize">
                      {category}
                    </h4>
                    <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                      {AVAILABLE_TOOLS.filter(t => (t as any).category === category).map((tool) => (
                        <ToolTile
                          key={tool.id}
                          id={tool.id}
                          name={tool.name}
                          description={tool.description}
                          selected={watchedTools?.includes(tool.id) || false}
                          onSelect={handleToolToggle}
                          disabled={loadingTemplate}
                        />
                      ))}
                    </div>
                  </div>
                ));
              })()}
            </div>

            {/* Selected tools summary */}
            {watchedTools && watchedTools.length > 0 && (
              <div className="mt-4 p-3 bg-accent-cyan/5 border border-accent-cyan/20 rounded-lg">
                <p className="text-sm text-text-secondary">
                  <span className="text-accent-cyan font-medium">{watchedTools.length}</span> tool{watchedTools.length !== 1 ? 's' : ''} selected
                </p>
              </div>
            )}
          </SectionPanel>

          {/* Advanced Options */}
          <SectionPanel
            title="Advanced Options"
            collapsible
            defaultCollapsed
            accentColor="cyan"
          >
            <div className="grid grid-cols-2 gap-4">
              <Controller
                name="provider"
                control={control}
                render={({ field }) => (
                  <Select
                    label="LLM Provider"
                    {...field}
                    disabled={loadingTemplate}
                    options={[
                      { value: 'zai', label: 'ZAI (Default)' },
                      { value: 'openai', label: 'OpenAI' },
                      { value: 'anthropic', label: 'Anthropic' },
                      { value: 'openrouter', label: 'OpenRouter' },
                    ]}
                  />
                )}
              />
              <Controller
                name="model"
                control={control}
                render={({ field }) => (
                  <Select
                    label="Model"
                    {...field}
                    disabled={loadingTemplate}
                    options={MODELS_BY_PROVIDER[watchedProvider]?.map((m) => ({
                      value: m,
                      label: m,
                    })) || [{ value: 'default', label: 'Default' }]}
                  />
                )}
              />
            </div>
          </SectionPanel>

          {/* Generate Button */}
          <div className="pt-4">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              disabled={isGenerating || loadingTemplate}
              iconLeft={isGenerating ? undefined : <Sparkles className="w-5 h-5" />}
            >
              {loadingTemplate ? (
                <span className="animate-pulse">Loading Template...</span>
              ) : isGenerating ? (
                <span className="animate-pulse">
                  {generationState === 'analyzing' && 'Analyzing...'}
                  {generationState === 'generating' && 'Generating...'}
                  {generationState === 'validating' && 'Validating...'}
                </span>
              ) : (
                'Generate Agent'
              )}
            </Button>
            {generationError && (
              <p className="mt-2 text-sm text-error text-center">{generationError}</p>
            )}
          </div>
        </form>

        {/* Right: Code Preview */}
        <div className="hidden lg:block">
          <CodePanel
            activeTab={activeTab}
            onTabChange={setActiveTab}
            flowCode={codeFiles['flow.py']?.content || ''}
            agentsYaml={codeFiles['agents.yaml']?.content || ''}
            requirements={codeFiles['requirements.txt']?.content || ''}
            stateCode={codeFiles['state.py']?.content || ''}
            onCodeChange={updateCodeContent}
            validationStatus={validationStatus}
            generationState={generationState}
          />
        </div>
      </div>
    </AppShell>
  );
}

export default function CreateAgentPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-accent-cyan"></div>
      </div>
    }>
      <CreateAgentPageContent />
    </Suspense>
  );
}
