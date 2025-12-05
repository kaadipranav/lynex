import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';

interface PromptVersion {
  version_id: string;
  prompt_name: string;
  version_number: number;
  template: string;
  model?: string;
  temperature?: number;
  created_at: string;
  usage_count: number;
  avg_cost?: number;
  avg_latency_ms?: number;
  success_rate?: number;
}

interface PromptDiff {
  version_a_number: number;
  version_b_number: number;
  added_lines: string[];
  removed_lines: string[];
  unchanged_lines: string[];
  model_changed: boolean;
  temperature_changed: boolean;
  cost_delta?: number;
  latency_delta?: number;
  success_rate_delta?: number;
}

export default function PromptDetailPage() {
  const { promptName } = useParams<{ promptName: string }>();
  const navigate = useNavigate();
  
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [selectedVersionA, setSelectedVersionA] = useState<number | null>(null);
  const [selectedVersionB, setSelectedVersionB] = useState<number | null>(null);
  const [diff, setDiff] = useState<PromptDiff | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVersions();
  }, [promptName]);

  useEffect(() => {
    if (selectedVersionA !== null && selectedVersionB !== null) {
      fetchDiff();
    } else {
      setDiff(null);
    }
  }, [selectedVersionA, selectedVersionB]);

  const fetchVersions = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/prompts/${promptName}/versions`);
      const versionsList = response.data;
      setVersions(versionsList);
      
      // Auto-select latest two versions for diff
      if (versionsList.length >= 2) {
        setSelectedVersionA(versionsList[1].version_number);
        setSelectedVersionB(versionsList[0].version_number);
      } else if (versionsList.length === 1) {
        setSelectedVersionB(versionsList[0].version_number);
      }
      
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch versions');
    } finally {
      setLoading(false);
    }
  };

  const fetchDiff = async () => {
    if (selectedVersionA === null || selectedVersionB === null) return;
    
    try {
      const response = await api.get(`/prompts/${promptName}/diff`, {
        params: {
          version_a: selectedVersionA,
          version_b: selectedVersionB,
        },
      });
      setDiff(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to compute diff');
    }
  };

  const versionA = versions.find(v => v.version_number === selectedVersionA);
  const versionB = versions.find(v => v.version_number === selectedVersionB);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading versions...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <button
          onClick={() => navigate('/prompts')}
          className="text-gray-400 hover:text-white mb-2 flex items-center gap-1"
        >
          ← Back to Prompts
        </button>
        <h1 className="text-2xl font-bold text-white">{promptName}</h1>
        <p className="text-gray-400">{versions.length} versions</p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Version Selectors */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Version A (Base)
            </label>
            <select
              value={selectedVersionA || ''}
              onChange={(e) => setSelectedVersionA(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            >
              <option value="">Select version...</option>
              {versions.map((v) => (
                <option key={v.version_number} value={v.version_number}>
                  v{v.version_number} - {new Date(v.created_at).toLocaleDateString()}
                  {v.model && ` (${v.model})`}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Version B (Compare)
            </label>
            <select
              value={selectedVersionB || ''}
              onChange={(e) => setSelectedVersionB(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            >
              <option value="">Select version...</option>
              {versions.map((v) => (
                <option key={v.version_number} value={v.version_number}>
                  v{v.version_number} - {new Date(v.created_at).toLocaleDateString()}
                  {v.model && ` (${v.model})`}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Diff View */}
      {diff && versionA && versionB ? (
        <div className="space-y-6">
          {/* Performance Metrics Comparison */}
          {(diff.cost_delta !== null || diff.latency_delta !== null) && (
            <div className="bg-gray-800 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-white mb-3">Performance Comparison</h2>
              <div className="grid grid-cols-3 gap-4">
                {diff.cost_delta !== undefined && diff.cost_delta !== null && (
                  <div>
                    <p className="text-sm text-gray-400">Cost Delta</p>
                    <p className={`text-xl font-bold ${diff.cost_delta > 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {diff.cost_delta > 0 ? '+' : ''}${diff.cost_delta.toFixed(4)}
                    </p>
                  </div>
                )}
                {diff.latency_delta !== undefined && diff.latency_delta !== null && (
                  <div>
                    <p className="text-sm text-gray-400">Latency Delta</p>
                    <p className={`text-xl font-bold ${diff.latency_delta > 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {diff.latency_delta > 0 ? '+' : ''}{diff.latency_delta.toFixed(0)}ms
                    </p>
                  </div>
                )}
                {diff.success_rate_delta !== undefined && diff.success_rate_delta !== null && (
                  <div>
                    <p className="text-sm text-gray-400">Success Rate Delta</p>
                    <p className={`text-xl font-bold ${diff.success_rate_delta > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {diff.success_rate_delta > 0 ? '+' : ''}{(diff.success_rate_delta * 100).toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Template Diff */}
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-white">Template Changes</h2>
              <div className="flex gap-4 text-sm">
                <span className="text-green-400">+{diff.added_lines.length} added</span>
                <span className="text-red-400">-{diff.removed_lines.length} removed</span>
              </div>
            </div>

            {diff.model_changed && (
              <div className="mb-3 p-2 bg-yellow-500/10 border border-yellow-500/50 rounded text-yellow-400 text-sm">
                ⚠️ Model changed: {versionA.model} → {versionB.model}
              </div>
            )}

            {diff.temperature_changed && (
              <div className="mb-3 p-2 bg-blue-500/10 border border-blue-500/50 rounded text-blue-400 text-sm">
                ℹ️ Temperature changed: {versionA.temperature} → {versionB.temperature}
              </div>
            )}

            <div className="font-mono text-sm bg-gray-900 rounded p-4 overflow-x-auto">
              {/* Render diff line by line */}
              {renderDiffLines(diff)}
            </div>
          </div>

          {/* Side-by-Side View */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-white">v{versionA.version_number}</h3>
                {versionA.usage_count > 0 && (
                  <span className="text-xs text-gray-400">{versionA.usage_count} uses</span>
                )}
              </div>
              <pre className="text-sm text-gray-300 whitespace-pre-wrap bg-gray-900 rounded p-3 overflow-auto max-h-96">
                {versionA.template}
              </pre>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-white">v{versionB.version_number}</h3>
                {versionB.usage_count > 0 && (
                  <span className="text-xs text-gray-400">{versionB.usage_count} uses</span>
                )}
              </div>
              <pre className="text-sm text-gray-300 whitespace-pre-wrap bg-gray-900 rounded p-3 overflow-auto max-h-96">
                {versionB.template}
              </pre>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-gray-400">
          Select two versions to compare
        </div>
      )}
    </div>
  );
}

function renderDiffLines(diff: PromptDiff) {
  // Simple unified diff rendering
  const lines: JSX.Element[] = [];
  let key = 0;

  diff.removed_lines.forEach((line) => {
    lines.push(
      <div key={key++} className="bg-red-500/10 text-red-400 px-2 py-0.5">
        - {line}
      </div>
    );
  });

  diff.added_lines.forEach((line) => {
    lines.push(
      <div key={key++} className="bg-green-500/10 text-green-400 px-2 py-0.5">
        + {line}
      </div>
    );
  });

  if (lines.length === 0) {
    return <div className="text-gray-400">No changes in template</div>;
  }

  return lines;
}
