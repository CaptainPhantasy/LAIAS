'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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

// ============================================================================
// Form Schema
// ============================================================================

const formSchema = z.object({
  description: z.string().min(10, 'Description must be at least 10 characters').max(2000),
  complexity: z.enum(['simple', 'moderate', 'complex']),
  task_type: z.enum(['research', 'development', 'automation', 'analysis', 'general']),
  max_agents: z.number().min(1).max(10),
  tools_requested: z.array(z.string()),
  provider: z.enum(['zai', 'openai', 'anthropic', 'openrouter']),
  save_agent: z.boolean(),
});

type FormValues = z.infer<typeof formSchema>;

// ============================================================================
// Page Component
// ============================================================================

export default function CreateAgentPage() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);

  const {
    generationState,
    generationError,
    activeTab,
    validationStatus,
    codeFiles,
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
      complexity: 'moderate',
      task_type: 'general',
      max_agents: 3,
      tools_requested: [],
      provider: 'zai',
      save_agent: true,
    },
  });

  const watchedDescription = watch('description');
  const watchedTools = watch('tools_requested');
  const watchedProvider = watch('provider');

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

  // Generate handler
  const handleGenerate = async (data: FormValues) => {
    setIsGenerating(true);
    setGenerationError(null);
    resetGeneration();
    setGenerationState('analyzing');

    try {
      setGenerationState('generating');
      const response = await studioApi.generateAgent({
        description: data.description,
        complexity: data.complexity,
        task_type: data.task_type,
        max_agents: data.max_agents,
        tools_requested: data.tools_requested,
        provider: data.provider,
        save_agent: data.save_agent,
      });

      setGeneratedCode({
        agentId: response.agent_id || '',
        flowCode: response.flow_code || '',
        agentsYaml: response.agents_config
          ? typeof response.agents_config === 'string'
            ? response.agents_config
            : JSON.stringify(response.agents_config, null, 2)
          : '',
        requirements: '',
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
    } finally {
      setGenerationState('complete');
    }
  };

  // Deploy handler
  const handleDeploy = async () => {
    // TODO: Implement deploy logic
    console.log('Deploy triggered');
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
                    onChange={(e) => field.onChange(parseInt(e.target.value, 10) || 1)}
                  />
                )}
              />
            </div>
          </SectionPanel>

          {/* Tools */}
          <SectionPanel title="Tools" accentColor="pink">
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {AVAILABLE_TOOLS.map((tool) => (
                <ToolTile
                  key={tool.id}
                  id={tool.id}
                  name={tool.name}
                  description={tool.description}
                  selected={watchedTools?.includes(tool.id) || false}
                  onSelect={handleToolToggle}
                />
              ))}
            </div>
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
                    options={[
                      { value: 'zai', label: 'ZAI (Default)' },
                      { value: 'openai', label: 'OpenAI' },
                      { value: 'anthropic', label: 'Anthropic' },
                      { value: 'openrouter', label: 'OpenRouter' },
                    ]}
                  />
                )}
              />
              <Select
                label="Model"
                options={MODELS_BY_PROVIDER[watchedProvider]?.map((m) => ({
                  value: m,
                  label: m,
                })) || [{ value: 'default', label: 'Default' }]}
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
              disabled={isGenerating}
              iconLeft={isGenerating ? undefined : <Sparkles className="w-5 h-5" />}
            >
              {isGenerating ? (
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
            onCodeChange={updateCodeContent}
            validationStatus={validationStatus}
            generationState={generationState}
          />
        </div>
      </div>
    </AppShell>
  );
}
