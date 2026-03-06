'use client';

import { useEffect, useId, useMemo, useState } from 'react';
import {
  getDeploymentOutputRuns,
  getDeploymentOutputRunDetail,
} from '@/lib/api';
import type {
  OutputRunDetailResponse,
  OutputRunListItem,
} from '@/types';

interface OutputArtifactsPanelProps {
  deploymentId: string;
}

export function OutputArtifactsPanel({ deploymentId }: OutputArtifactsPanelProps) {
  const runSelectId = useId();
  const [runs, setRuns] = useState<OutputRunListItem[]>([]);
  const [selectedRunId, setSelectedRunId] = useState('');
  const [detail, setDetail] = useState<OutputRunDetailResponse | null>(null);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadRuns() {
      if (!deploymentId) {
        setRuns([]);
        setSelectedRunId('');
        setDetail(null);
        return;
      }

      setIsLoadingRuns(true);
      setError(null);
      try {
        const response = await getDeploymentOutputRuns(deploymentId);
        if (!active) return;
        const nextRuns = response.runs || [];
        setRuns(nextRuns);
        const firstRun = nextRuns[0]?.run_id || '';
        setSelectedRunId(firstRun);
      } catch (e) {
        if (!active) return;
        setError('Failed to load output runs');
        setRuns([]);
        setSelectedRunId('');
        setDetail(null);
      } finally {
        if (active) setIsLoadingRuns(false);
      }
    }

    loadRuns();
    return () => {
      active = false;
    };
  }, [deploymentId]);

  useEffect(() => {
    let active = true;
    async function loadDetail() {
      if (!deploymentId || !selectedRunId) {
        setDetail(null);
        return;
      }

      setIsLoadingDetail(true);
      setError(null);
      try {
        const response = await getDeploymentOutputRunDetail(
          deploymentId,
          selectedRunId
        );
        if (!active) return;
        setDetail(response);
      } catch (e) {
        if (!active) return;
        setError('Failed to load run artifacts');
        setDetail(null);
      } finally {
        if (active) setIsLoadingDetail(false);
      }
    }

    loadDetail();
    return () => {
      active = false;
    };
  }, [deploymentId, selectedRunId]);

  const metricsJson = useMemo(() => {
    if (!detail) return '{}';
    return JSON.stringify(detail.metrics || {}, null, 2);
  }, [detail]);

  return (
    <div className="bg-surface border border-border rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary">Output Artifacts</h2>
        {deploymentId ? (
          <span className="text-xs text-text-muted font-mono">
            deployment: {deploymentId}
          </span>
        ) : null}
      </div>

      {!deploymentId ? (
        <p className="text-sm text-text-muted">
          No deployment ID available for this container yet.
        </p>
      ) : null}

      {deploymentId ? (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <label className="text-sm text-text-secondary" htmlFor={runSelectId}>
              Run
            </label>
            <select
              id={runSelectId}
              className="bg-surface-2 border border-border rounded px-2 py-1 text-sm text-text-primary min-w-[240px]"
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              disabled={isLoadingRuns || runs.length === 0}
            >
              {runs.length === 0 ? (
                <option value="">No runs</option>
              ) : (
                runs.map((run) => (
                  <option key={run.run_id} value={run.run_id}>
                    {run.run_id} ({run.event_count} events)
                  </option>
                ))
              )}
            </select>
          </div>

          {isLoadingRuns || isLoadingDetail ? (
            <p className="text-sm text-text-muted">Loading artifacts...</p>
          ) : null}

          {error ? <p className="text-sm text-red-400">{error}</p> : null}

          {detail ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-text-secondary">Summary</h3>
                <pre className="text-xs text-text-primary bg-surface-2 rounded p-3 overflow-auto max-h-[320px] whitespace-pre-wrap">
                  {detail.summary_markdown || 'No summary.md found'}
                </pre>
              </div>

              <div className="space-y-2">
                <h3 className="text-sm font-medium text-text-secondary">Metrics</h3>
                <pre className="text-xs text-text-primary bg-surface-2 rounded p-3 overflow-auto max-h-[320px]">
                  {metricsJson}
                </pre>
              </div>

              <div className="space-y-2 xl:col-span-2">
                <h3 className="text-sm font-medium text-text-secondary">Events</h3>
                <pre className="text-xs text-text-primary bg-surface-2 rounded p-3 overflow-auto max-h-[360px]">
                  {JSON.stringify(detail.events || [], null, 2)}
                </pre>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
