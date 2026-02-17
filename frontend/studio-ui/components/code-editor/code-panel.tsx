'use client';

import * as React from 'react';
import dynamic from 'next/dynamic';
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Sparkles,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { CodeTab, GenerationState, ValidationStatus } from '@/types';

// Dynamic import for Monaco to avoid SSR issues
const MonacoEditor = dynamic(
  () => import('@monaco-editor/react').then((mod) => mod.default),
  { ssr: false, loading: () => <EditorSkeleton /> }
);

// ============================================================================
// Types
// ============================================================================

interface CodePanelProps {
  activeTab: CodeTab;
  onTabChange: (tab: CodeTab) => void;
  flowCode: string;
  agentsYaml: string;
  requirements: string;
  stateCode: string;
  onCodeChange: (tab: CodeTab, content: string) => void;
  validationStatus: ValidationStatus | null;
  generationState: GenerationState;
  className?: string;
}

// ============================================================================
// Monaco Theme
// ============================================================================

const monacoTheme = {
  base: 'vs-dark' as const,
  inherit: true,
  rules: [
    { token: 'comment', foreground: '6F7A96', fontStyle: 'italic' },
    { token: 'keyword', foreground: '8E5CFF' },
    { token: 'string', foreground: '22C55E' },
    { token: 'number', foreground: 'FF4FA3' },
    { token: 'type', foreground: '2DE2FF' },
    { token: 'function', foreground: '2DE2FF' },
    { token: 'variable', foreground: 'F4F7FF' },
  ],
  colors: {
    'editor.background': '#111C36',
    'editor.foreground': '#F4F7FF',
    'editorLineNumber.foreground': '#3D4666',
    'editorLineNumber.activeForeground': '#AAB3C5',
    'editor.selectionBackground': '#2DE2FF30',
    'editor.lineHighlightBackground': '#1E2746',
    'editorCursor.foreground': '#2DE2FF',
    'editor.inactiveSelectionBackground': '#2DE2FF15',
    'editorIndentGuide.background': '#2A345640',
    'editorIndentGuide.activeBackground': '#2A3456',
    'editorWidget.background': '#111C36',
    'editorWidget.border': '#2A3456',
    'scrollbarSlider.background': '#3D466680',
    'scrollbarSlider.hoverBackground': '#3D4666',
  },
};

// ============================================================================
// Editor Skeleton
// ============================================================================

function EditorSkeleton() {
  return (
    <div className="h-full bg-[#111C36] rounded-b-lg p-4 space-y-2">
      {[...Array(15)].map((_, i) => (
        <div
          key={i}
          className="h-4 bg-surface-2 rounded shimmer"
          style={{ width: `${Math.random() * 40 + 60}%`, marginLeft: `${Math.floor(i / 3) * 20}px` }}
        />
      ))}
    </div>
  );
}

// ============================================================================
// Generation State Indicator
// ============================================================================

interface GenerationIndicatorProps {
  state: GenerationState;
}

const GenerationIndicator: React.FC<GenerationIndicatorProps> = ({ state }) => {
  const states = {
    idle: {
      icon: <Sparkles className="w-4 h-4" />,
      color: 'text-text-muted',
      label: 'Ready to generate',
      animate: false,
    },
    analyzing: {
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
      color: 'text-accent-purple',
      label: 'Analyzing...',
      animate: true,
    },
    generating: {
      icon: <RefreshCw className="w-4 h-4 animate-spin" />,
      color: 'text-accent-cyan',
      label: 'Generating...',
      animate: true,
    },
    validating: {
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
      color: 'text-info',
      label: 'Validating...',
      animate: true,
    },
    complete: {
      icon: <CheckCircle className="w-4 h-4" />,
      color: 'text-success',
      label: 'Complete',
      animate: false,
    },
    error: {
      icon: <XCircle className="w-4 h-4" />,
      color: 'text-error',
      label: 'Error',
      animate: false,
    },
  };

  const config = states[state];

  return (
    <div className={cn('flex items-center gap-2 text-sm', config.color)}>
      {config.icon}
      <span>{config.label}</span>
    </div>
  );
};

// ============================================================================
// Validation Panel
// ============================================================================

interface ValidationPanelProps {
  status: ValidationStatus | null;
}

const ValidationPanel: React.FC<ValidationPanelProps> = ({ status }) => {
  if (!status) {
    return (
      <div className="px-4 py-3 bg-bg-tertiary rounded-lg text-sm text-text-muted">
        Run validation to check code quality
      </div>
    );
  }

  const errorCount = status.errors.filter((e) => e.severity === 'error').length;
  const warningCount = status.warnings.length;
  const infoCount = status.errors.filter((e) => e.severity === 'info').length;

  return (
    <div className="space-y-2">
      {/* Score */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-text-secondary">Quality Score</span>
        <span
          className={cn(
            'text-lg font-bold',
            status.score >= 80 ? 'text-success' : status.score >= 50 ? 'text-warning' : 'text-error'
          )}
        >
          {Math.round(status.score)}
        </span>
      </div>

      {/* Status Items */}
      <div className="flex items-center gap-4">
        {/* Patterns */}
        <div className="flex items-center gap-1.5">
          {status.isValid ? (
            <CheckCircle className="w-4 h-4 text-success" />
          ) : (
            <XCircle className="w-4 h-4 text-error" />
          )}
          <span className="text-sm text-text-secondary">Patterns</span>
        </div>

        {/* Warnings */}
        {warningCount > 0 && (
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-warning" />
            <span className="text-sm text-warning">{warningCount} Warnings</span>
          </div>
        )}

        {/* Errors */}
        {errorCount > 0 && (
          <div className="flex items-center gap-1.5">
            <XCircle className="w-4 h-4 text-error" />
            <span className="text-sm text-error">{errorCount} Errors</span>
          </div>
        )}
      </div>

      {/* Error Details */}
      {status.errors.length > 0 && (
        <div className="mt-3 space-y-1.5 max-h-32 overflow-y-auto">
          {status.errors.slice(0, 5).map((error, idx) => (
            <div
              key={idx}
              className={cn(
                'text-xs px-2 py-1.5 rounded',
                error.severity === 'error' ? 'bg-error/10 text-error' : 'bg-warning/10 text-warning'
              )}
            >
              {error.line && <span className="font-mono">L{error.line}: </span>}
              {error.message}
            </div>
          ))}
          {status.errors.length > 5 && (
            <div className="text-xs text-text-muted">
              +{status.errors.length - 5} more issues
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Code Panel Component
// ============================================================================

export const CodePanel: React.FC<CodePanelProps> = ({
  activeTab,
  onTabChange,
  flowCode,
  agentsYaml,
  requirements,
  stateCode,
  onCodeChange,
  validationStatus,
  generationState,
  className,
}) => {
  const [isEditorReady, setIsEditorReady] = React.useState(false);

  const handleEditorMount = () => {
    setIsEditorReady(true);
  };

  const getCodeForTab = (tab: CodeTab): string => {
    switch (tab) {
      case 'flow.py':
        return flowCode;
      case 'agents.yaml':
        return agentsYaml;
      case 'requirements.txt':
        return requirements;
      case 'state.py':
        return stateCode;
    }
  };

  const getLanguageForTab = (tab: CodeTab): string => {
    switch (tab) {
      case 'flow.py':
        return 'python';
      case 'agents.yaml':
        return 'yaml';
      case 'requirements.txt':
        return 'text';
      case 'state.py':
        return 'python';
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      onCodeChange(activeTab, value);
    }
  };

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface">
        <Tabs value={activeTab} onValueChange={(v) => onTabChange(v as CodeTab)}>
          <TabsList className="bg-bg-tertiary">
            <TabsTrigger value="flow.py">flow.py</TabsTrigger>
            <TabsTrigger value="agents.yaml">agents.yaml</TabsTrigger>
            <TabsTrigger value="state.py">state.py</TabsTrigger>
            <TabsTrigger value="requirements.txt">requirements.txt</TabsTrigger>
          </TabsList>
        </Tabs>

        <GenerationIndicator state={generationState} />
      </div>

      {/* Editor */}
      <div className="flex-1 min-h-0">
        {flowCode || agentsYaml || requirements || stateCode ? (
          <MonacoEditor
            height="100%"
            language={getLanguageForTab(activeTab)}
            value={getCodeForTab(activeTab)}
            onChange={handleEditorChange}
            onMount={handleEditorMount}
            theme="laias-dark"
            beforeMount={(monaco) => {
              monaco.editor.defineTheme('laias-dark', monacoTheme);
            }}
            options={{
              minimap: { enabled: false },
              fontSize: 13,
              fontFamily: "'JetBrains Mono', Menlo, monospace",
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 2,
              wordWrap: 'on',
              padding: { top: 16, bottom: 16 },
              scrollbar: {
                verticalScrollbarSize: 8,
                horizontalScrollbarSize: 8,
              },
              renderLineHighlight: 'line',
              cursorBlinking: 'smooth',
              cursorSmoothCaretAnimation: 'on',
            }}
          />
        ) : (
          <div className="h-full flex items-center justify-center bg-[#111C36]">
            <div className="text-center">
              <Sparkles className="w-8 h-8 text-text-muted mx-auto mb-3" />
              <p className="text-sm text-text-muted">
                Generated code will appear here
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Validation Panel */}
      <div className="flex-shrink-0 p-4 border-t border-border bg-surface">
        <ValidationPanel status={validationStatus} />
      </div>
    </div>
  );
};
