import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

interface PromptVersion {
  version_id: string;
  prompt_name: string;
  version_number: number;
  template: string;
  model?: string;
  created_by: string;
  created_at: string;
  usage_count: number;
  avg_cost?: number;
  avg_latency_ms?: number;
}

interface PromptSummary {
  prompt_name: string;
  latest_version: PromptVersion;
  version_count: number;
}

export default function PromptsPage() {
  const navigate = useNavigate();
  const [prompts, setPrompts] = useState<PromptSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    prompt_name: '',
    template: '',
    model: 'gpt-4',
    temperature: 0.7,
  });

  useEffect(() => {
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/prompts');
      setPrompts(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch prompts');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/prompts', formData);
      setShowCreateModal(false);
      setFormData({ prompt_name: '', template: '', model: 'gpt-4', temperature: 0.7 });
      fetchPrompts();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create prompt version');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading prompts...</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Prompt Versions</h1>
          <p className="text-gray-400 mt-1">
            Track, version, and compare your prompt templates
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          + New Version
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-white mb-4">Create Prompt Version</h2>
            <form onSubmit={handleCreatePrompt} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Prompt Name
                </label>
                <input
                  type="text"
                  value={formData.prompt_name}
                  onChange={(e) => setFormData({ ...formData, prompt_name: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  placeholder="customer_support_agent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Template
                </label>
                <textarea
                  value={formData.template}
                  onChange={(e) => setFormData({ ...formData, template: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white font-mono text-sm"
                  rows={12}
                  placeholder="You are a helpful AI assistant..."
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Model
                  </label>
                  <select
                    value={formData.model}
                    onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  >
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                    <option value="gpt-4o">GPT-4o</option>
                    <option value="gpt-4o-mini">GPT-4o Mini</option>
                    <option value="claude-3-opus">Claude 3 Opus</option>
                    <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                    <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Temperature
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={formData.temperature}
                    onChange={(e) =>
                      setFormData({ ...formData, temperature: parseFloat(e.target.value) })
                    }
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
                >
                  Create Version
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Prompts List */}
      <div className="space-y-4">
        {prompts.length === 0 ? (
          <div className="text-center py-12 bg-gray-800/50 rounded-lg">
            <p className="text-gray-400 mb-4">No prompts yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="text-blue-400 hover:text-blue-300"
            >
              Create your first prompt version
            </button>
          </div>
        ) : (
          prompts.map((prompt) => (
            <div
              key={prompt.prompt_name}
              className="bg-gray-800 rounded-lg p-5 border border-gray-700 hover:border-gray-600 cursor-pointer transition-colors"
              onClick={() => navigate(`/prompts/${prompt.prompt_name}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-white">
                      {prompt.prompt_name}
                    </h3>
                    <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs font-medium">
                      {prompt.version_count} version{prompt.version_count !== 1 ? 's' : ''}
                    </span>
                  </div>

                  <div className="text-sm text-gray-300 space-y-1">
                    <p>
                      <span className="text-gray-400">Latest:</span>{' '}
                      <span className="text-white">
                        v{prompt.latest_version.version_number}
                      </span>
                      {' '} · {' '}
                      <span className="text-gray-400">Model:</span>{' '}
                      <span className="text-white">{prompt.latest_version.model || 'N/A'}</span>
                    </p>
                    {prompt.latest_version.usage_count > 0 && (
                      <p>
                        <span className="text-gray-400">Usage:</span>{' '}
                        <span className="text-white">{prompt.latest_version.usage_count} calls</span>
                        {prompt.latest_version.avg_cost && (
                          <>
                            {' '} · {' '}
                            <span className="text-gray-400">Avg Cost:</span>{' '}
                            <span className="text-white">
                              ${prompt.latest_version.avg_cost.toFixed(4)}
                            </span>
                          </>
                        )}
                      </p>
                    )}
                  </div>
                </div>

                <div className="text-right text-sm text-gray-400">
                  <p>{new Date(prompt.latest_version.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
