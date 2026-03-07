'use client';

import * as React from 'react';

import type { OutputConfig, OutputFormat } from '@/types';
import { SectionPanel } from './section-panel';
import { FileBrowser } from './file-browser';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input, Select } from '@/components/ui/input';

interface OutputConfigPanelProps {
  outputConfig: OutputConfig;
  onConfigChange: (config: Partial<OutputConfig>) => void;
  disabled?: boolean;
}

export function OutputConfigPanel({
  outputConfig,
  onConfigChange,
  disabled = false,
}: OutputConfigPanelProps) {
  const [isBrowserOpen, setIsBrowserOpen] = React.useState(false);
  const [destinationError, setDestinationError] = React.useState<string | null>(null);

  const handleFormatChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    onConfigChange({ output_format: event.target.value as OutputFormat });
  };

  const handleDestinationChange = (destination: 'postgres' | 'files', checked: boolean) => {
    const nextDestinations = {
      ...outputConfig.output_destinations,
      [destination]: checked,
    };

    if (!nextDestinations.postgres && !nextDestinations.files) {
      setDestinationError('At least one destination must remain enabled.');
      return;
    }

    setDestinationError(null);
    onConfigChange({ output_destinations: nextDestinations });
  };

  return (
    <SectionPanel
      title="Output Configuration"
      accentColor="cyan"
      description="Configure where and how agent outputs are saved"
    >
      <div className="space-y-5">
        <div className="space-y-3">
          <p className="text-sm font-medium text-text-primary">Output Path</p>
          <div className="flex gap-2">
            <Input
              value={outputConfig.output_path}
              onChange={(event) => onConfigChange({ output_path: event.target.value })}
              placeholder="/var/laias/outputs"
              disabled={disabled}
            />
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsBrowserOpen((prev) => !prev)}
              disabled={disabled}
            >
              {isBrowserOpen ? 'Close' : 'Browse'}
            </Button>
          </div>

          {isBrowserOpen && (
            <FileBrowser
              selectedPath={outputConfig.output_path}
              onSelect={(path) => {
                onConfigChange({ output_path: path });
                setIsBrowserOpen(false);
              }}
            />
          )}
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-text-primary">Output Format</p>
          <Select
            value={outputConfig.output_format}
            onChange={handleFormatChange}
            disabled={disabled}
            options={[
              { value: 'markdown', label: 'Markdown' },
              { value: 'html', label: 'HTML' },
            ]}
          />
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-text-primary">Output Destinations</p>
          <Checkbox
            checked={outputConfig.output_destinations.postgres}
            onChange={(event) => handleDestinationChange('postgres', event.target.checked)}
            label="Save to Database"
            description="Persist structured events and metrics in PostgreSQL."
            disabled={disabled}
          />
          <Checkbox
            checked={outputConfig.output_destinations.files}
            onChange={(event) => handleDestinationChange('files', event.target.checked)}
            label="Save to Files"
            description="Write artifacts to the selected output directory."
            disabled={disabled}
          />
          {destinationError && <p className="text-sm text-error">{destinationError}</p>}
        </div>
      </div>
    </SectionPanel>
  );
}
