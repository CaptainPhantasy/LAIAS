'use client';

import * as React from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/app-shell';
import { SectionPanel } from '@/components/agent-builder/section-panel';
import { Input, Select } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';

const STORAGE_KEY = 'laias-settings';

interface Settings {
  agentGeneratorUrl: string;
  dockerOrchestratorUrl: string;
  defaultLlmProvider: string;
  defaultComplexity: string;
  autoValidate: boolean;
  showLineNumbers: boolean;
  wordWrap: boolean;
}

const DEFAULTS: Settings = {
  agentGeneratorUrl: process.env.NEXT_PUBLIC_AGENT_GENERATOR_URL || 'http://localhost:4521',
  dockerOrchestratorUrl: process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:4522',
  defaultLlmProvider: 'zai',
  defaultComplexity: 'moderate',
  autoValidate: true,
  showLineNumbers: true,
  wordWrap: true,
};

function loadSettings(): Settings {
  if (typeof window === 'undefined') return DEFAULTS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULTS;
    return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return DEFAULTS;
  }
}

export default function SettingsPage() {
  const [settings, setSettings] = React.useState<Settings>(DEFAULTS);
  const [saved, setSaved] = React.useState(false);

  React.useEffect(() => {
    setSettings(loadSettings());
  }, []);

  const update = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setSettings(DEFAULTS);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <AppShell title="Settings">
      <div className="max-w-2xl space-y-6">
        {/* Team Settings Link */}
        <SectionPanel title="Team" accentColor="purple">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-white font-medium">Team Collaboration</h3>
              <p className="text-sm text-gray-500">Manage team members and roles</p>
            </div>
            <Link href="/settings/team">
              <Button variant="outline">Manage Team</Button>
            </Link>
          </div>
        </SectionPanel>

        {/* API Configuration */}
        <SectionPanel title="API Configuration" accentColor="cyan">
          <div className="space-y-4">
            <Input
              label="Agent Generator URL"
              value={settings.agentGeneratorUrl}
              onChange={(e) => update('agentGeneratorUrl', e.target.value)}
              helperText="URL for the agent generator service"
            />
            <Input
              label="Docker Orchestrator URL"
              value={settings.dockerOrchestratorUrl}
              onChange={(e) => update('dockerOrchestratorUrl', e.target.value)}
              helperText="URL for the docker orchestrator service"
            />
          </div>
        </SectionPanel>

        {/* Default Preferences */}
        <SectionPanel title="Default Preferences" accentColor="purple">
          <div className="space-y-4">
            <Select
              label="Default LLM Provider"
              value={settings.defaultLlmProvider}
              onChange={(e) => update('defaultLlmProvider', e.target.value)}
              options={[
                { value: 'zai', label: 'ZAI (Default)' },
                { value: 'openai', label: 'OpenAI' },
                { value: 'anthropic', label: 'Anthropic' },
                { value: 'openrouter', label: 'OpenRouter' },
              ]}
            />
            <Select
              label="Default Complexity"
              value={settings.defaultComplexity}
              onChange={(e) => update('defaultComplexity', e.target.value)}
              options={[
                { value: 'simple', label: 'Simple' },
                { value: 'moderate', label: 'Moderate' },
                { value: 'complex', label: 'Complex' },
              ]}
            />
          </div>
        </SectionPanel>

        {/* Editor Settings */}
        <SectionPanel title="Editor Settings" accentColor="pink">
          <div className="space-y-4">
            <Checkbox
              label="Auto-validate on generation"
              description="Automatically validate code after generation"
              checked={settings.autoValidate}
              onChange={(e) => update('autoValidate', e.target.checked)}
            />
            <Checkbox
              label="Show line numbers"
              description="Display line numbers in code editor"
              checked={settings.showLineNumbers}
              onChange={(e) => update('showLineNumbers', e.target.checked)}
            />
            <Checkbox
              label="Word wrap"
              description="Enable word wrap in code editor"
              checked={settings.wordWrap}
              onChange={(e) => update('wordWrap', e.target.checked)}
            />
          </div>
        </SectionPanel>

        {/* Save Button */}
        <div className="flex items-center gap-4 pt-4">
          <Button variant="primary" onClick={handleSave}>
            {saved ? 'Saved!' : 'Save Settings'}
          </Button>
          <Button variant="outline" onClick={handleReset}>
            Reset to Defaults
          </Button>
        </div>
      </div>
    </AppShell>
  );
}
