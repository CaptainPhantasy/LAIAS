'use client';

import * as React from 'react';
import { ChevronRight, Folder, FolderOpen, Loader2, Plus, X } from 'lucide-react';

import { studioApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import type { FileBrowserEntry } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface FileBrowserProps {
  onSelect: (path: string) => void;
  selectedPath: string;
  className?: string;
}

function sortEntries(entries: FileBrowserEntry[]): FileBrowserEntry[] {
  return [...entries].sort((a, b) => a.name.localeCompare(b.name));
}

export function FileBrowser({ onSelect, selectedPath, className }: FileBrowserProps) {
  const [rootEntries, setRootEntries] = React.useState<FileBrowserEntry[]>([]);
  const [currentPath, setCurrentPath] = React.useState('');
  const [expandedPaths, setExpandedPaths] = React.useState<Set<string>>(new Set());
  const [loadingPaths, setLoadingPaths] = React.useState<Set<string>>(new Set());
  const [childrenByPath, setChildrenByPath] = React.useState<Record<string, FileBrowserEntry[]>>({});
  const [isLoadingRoot, setIsLoadingRoot] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [showNewFolder, setShowNewFolder] = React.useState(false);
  const [newFolderName, setNewFolderName] = React.useState('');
  const [creatingFolder, setCreatingFolder] = React.useState(false);

  const loadRoot = React.useCallback(async () => {
    setIsLoadingRoot(true);
    setError(null);
    try {
      const response = await studioApi.browseFilesystem();
      setRootEntries(sortEntries(response.entries));
      setCurrentPath(response.current_path);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to load directories');
    } finally {
      setIsLoadingRoot(false);
    }
  }, []);

  React.useEffect(() => {
    void loadRoot();
  }, [loadRoot]);

  const loadChildren = React.useCallback(async (path: string) => {
    setLoadingPaths((prev) => new Set(prev).add(path));
    setError(null);

    try {
      const response = await studioApi.browseFilesystem(path);
      setChildrenByPath((prev) => ({
        ...prev,
        [path]: sortEntries(response.entries),
      }));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to load subdirectories');
    } finally {
      setLoadingPaths((prev) => {
        const next = new Set(prev);
        next.delete(path);
        return next;
      });
    }
  }, []);

  const handleToggleExpand = React.useCallback(
    async (path: string) => {
      const isExpanded = expandedPaths.has(path);
      if (isExpanded) {
        setExpandedPaths((prev) => {
          const next = new Set(prev);
          next.delete(path);
          return next;
        });
        return;
      }

      setExpandedPaths((prev) => new Set(prev).add(path));
      if (!childrenByPath[path]) {
        await loadChildren(path);
      }
    },
    [childrenByPath, expandedPaths, loadChildren]
  );

  const handleCreateFolder = React.useCallback(async () => {
    const trimmed = newFolderName.trim();
    if (!trimmed) {
      return;
    }

    const basePath = selectedPath || currentPath;
    const normalizedBasePath = basePath.endsWith('/') ? basePath.slice(0, -1) : basePath;
    const targetPath = normalizedBasePath ? `${normalizedBasePath}/${trimmed}` : trimmed;

    setCreatingFolder(true);
    setError(null);
    try {
      await studioApi.createDirectory(targetPath);
      setNewFolderName('');
      setShowNewFolder(false);
      await loadRoot();
      onSelect(targetPath);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : 'Failed to create folder');
    } finally {
      setCreatingFolder(false);
    }
  }, [currentPath, loadRoot, newFolderName, onSelect, selectedPath]);

  const renderEntries = React.useCallback(
    (entries: FileBrowserEntry[], depth = 0): React.ReactNode => {
      return entries.map((entry) => {
        const isExpanded = expandedPaths.has(entry.path);
        const isSelected = selectedPath === entry.path;
        const isLoading = loadingPaths.has(entry.path);
        const children = childrenByPath[entry.path] || [];

        return (
          <div key={entry.path} className="space-y-1">
            <div
              className={cn(
                'group flex items-center gap-2 rounded-md px-2 py-1.5',
                'border border-transparent hover:border-border hover:bg-surface-2',
                isSelected && 'border-accent-cyan/30 bg-accent-cyan/10'
              )}
              style={{ paddingLeft: `${depth * 14 + 8}px` }}
              data-testid="file-browser-entry"
            >
              <button
                type="button"
                className="flex h-5 w-5 items-center justify-center rounded text-text-secondary hover:bg-bg-tertiary"
                onClick={() => void handleToggleExpand(entry.path)}
                aria-label={isExpanded ? 'Collapse directory' : 'Expand directory'}
              >
                {isLoading ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <ChevronRight className={cn('h-3.5 w-3.5 transition-transform', isExpanded && 'rotate-90')} />
                )}
              </button>

              <button
                type="button"
                className="flex min-w-0 flex-1 items-center gap-2 text-left"
                onClick={() => onSelect(entry.path)}
              >
                {isExpanded ? (
                  <FolderOpen className="h-4 w-4 shrink-0 text-accent-cyan" />
                ) : (
                  <Folder className="h-4 w-4 shrink-0 text-text-secondary" />
                )}
                <span className="truncate text-sm text-text-primary">{entry.name}</span>
              </button>
            </div>

            {isExpanded && children.length > 0 && <div>{renderEntries(children, depth + 1)}</div>}
          </div>
        );
      });
    },
    [childrenByPath, expandedPaths, handleToggleExpand, loadingPaths, onSelect, selectedPath]
  );

  return (
    <div className={cn('rounded-lg border border-border bg-surface p-3', className)}>
      <div className="mb-3 flex items-center justify-between border-b border-border pb-2">
        <p className="text-xs text-text-secondary">Current: {currentPath || '/'}</p>
        <button
          type="button"
          onClick={() => setShowNewFolder((prev) => !prev)}
          className="inline-flex items-center gap-1 text-xs font-medium text-accent-cyan hover:text-accent-cyan/80"
        >
          <Plus className="h-3.5 w-3.5" />
          New Folder
        </button>
      </div>

      {showNewFolder && (
        <div className="mb-3 rounded-md border border-border bg-bg-tertiary p-2">
          <div className="flex items-center gap-2">
            <Input
              value={newFolderName}
              onChange={(event) => setNewFolderName(event.target.value)}
              placeholder="folder-name"
              className="h-9"
              disabled={creatingFolder}
            />
            <Button
              type="button"
              size="sm"
              variant="primary"
              onClick={() => void handleCreateFolder()}
              disabled={creatingFolder || !newFolderName.trim()}
            >
              {creatingFolder ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create'}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => {
                setShowNewFolder(false);
                setNewFolderName('');
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {error && <p className="mb-3 text-sm text-error">{error}</p>}

      {isLoadingRoot ? (
        <div className="flex items-center gap-2 py-6 text-sm text-text-secondary">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading directories...
        </div>
      ) : rootEntries.length === 0 ? (
        <p className="py-6 text-sm text-text-secondary">No directories found.</p>
      ) : (
        <div className="max-h-72 overflow-auto pr-1">{renderEntries(rootEntries)}</div>
      )}
    </div>
  );
}
