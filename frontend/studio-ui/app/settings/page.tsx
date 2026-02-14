'use client';

import * as React from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { SectionPanel } from '@/components/agent-builder/section-panel';
import { Input, Select } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';

export default function SettingsPage() {
  const [saved, setSaved] = React.useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <AppShell title="Settings">
      <div className="max-w-2xl space-y-6">
        {/* API Configuration */}
        <SectionPanel title="API Configuration" accentColor="cyan">
          <div className="space-y-4">
            <Input
              label="Agent Generator URL"
              defaultValue="http://localhost:8001"
              helperText="URL for the agent generator service"
            />
            <Input
              label="Docker Orchestrator URL"
              defaultValue="http://localhost:8002"
              helperText="URL for the docker orchestrator service"
            />
          </div>
        </SectionPanel>

        {/* Default Preferences */}
        <SectionPanel title="Default Preferences" accentColor="purple">
          <div className="space-y-4">
            <Select
              label="Default LLM Provider"
              defaultValue="zai"
              options={[
                { value: 'zai', label: 'ZAI (Default)' },
                { value: 'openai', label: 'OpenAI' },
                { value: 'anthropic', label: 'Anthropic' },
                { value: 'openrouter', label: 'OpenRouter' },
              ]}
            />
            <Select
              label="Default Complexity"
              defaultValue="moderate"
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
              defaultChecked
            />
            <Checkbox
              label="Show line numbers"
              description="Display line numbers in code editor"
              defaultChecked
            />
            <Checkbox
              label="Word wrap"
              description="Enable word wrap in code editor"
              defaultChecked
            />
          </div>
        </SectionPanel>

        {/* Save Button */}
        <div className="flex items-center gap-4 pt-4">
          <Button variant="primary" onClick={handleSave}>
            {saved ? 'Saved!' : 'Save Settings'}
          </Button>
          <Button variant="outline">
            Reset to Defaults
          </Button>
        </div>
      </div>
    </AppShell>
  );
}
