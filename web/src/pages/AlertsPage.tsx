import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

interface AlertRule {
  rule_id: string;
  project_id: string;
  name: string;
  event_type: string;
  condition: 'count' | 'sum' | 'avg';
  field?: string;
  threshold: number;
  window_seconds: number;
  channels: string[];
  enabled: boolean;
  created_at: string;
}

export default function AlertsPage() {
  const navigate = useNavigate();
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    event_type: 'error',
    condition: 'count' as 'count' | 'sum' | 'avg',
    field: '',
    threshold: 10,
    window_seconds: 300,
    channels: ['email'],
  });

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const response = await api.get('/alerts/rules');
      setRules(response.data.rules || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch alert rules');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/alerts/rules', formData);
      setShowCreateForm(false);
      setFormData({
        name: '',
        event_type: 'error',
        condition: 'count',
        field: '',
        threshold: 10,
        window_seconds: 300,
        channels: ['email'],
      });
      fetchRules();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create alert rule');
    }
  };

  const handleToggleEnabled = async (ruleId: string, currentEnabled: boolean) => {
    try {
      await api.patch(`/alerts/rules/${ruleId}`, { enabled: !currentEnabled });
      fetchRules();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update rule');
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!window.confirm('Are you sure you want to delete this alert rule?')) {
      return;
    }
    try {
      await api.delete(`/alerts/rules/${ruleId}`);
      fetchRules();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete rule');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading alert rules...</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Alert Rules</h1>
          <p className="text-gray-400 mt-1">
            Configure alerts for errors, high costs, and performance issues
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          + Create Rule
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Create Form Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-lg">
            <h2 className="text-xl font-bold text-white mb-4">Create Alert Rule</h2>
            <form onSubmit={handleCreateRule} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Rule Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Event Type
                </label>
                <select
                  value={formData.event_type}
                  onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                >
                  <option value="error">Error</option>
                  <option value="token_usage">Token Usage</option>
                  <option value="span">Span</option>
                  <option value="model_response">Model Response</option>
                  <option value="*">All Events</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Condition
                </label>
                <select
                  value={formData.condition}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      condition: e.target.value as 'count' | 'sum' | 'avg',
                    })
                  }
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                >
                  <option value="count">Count</option>
                  <option value="sum">Sum</option>
                  <option value="avg">Average</option>
                </select>
              </div>

              {(formData.condition === 'sum' || formData.condition === 'avg') && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Field
                  </label>
                  <input
                    type="text"
                    value={formData.field}
                    onChange={(e) => setFormData({ ...formData, field: e.target.value })}
                    placeholder="e.g., estimated_cost_usd, latency_ms"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Threshold
                </label>
                <input
                  type="number"
                  value={formData.threshold}
                  onChange={(e) =>
                    setFormData({ ...formData, threshold: parseFloat(e.target.value) })
                  }
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Time Window (seconds)
                </label>
                <input
                  type="number"
                  value={formData.window_seconds}
                  onChange={(e) =>
                    setFormData({ ...formData, window_seconds: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
                >
                  Create Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rules List */}
      <div className="space-y-4">
        {rules.length === 0 ? (
          <div className="text-center py-12 bg-gray-800/50 rounded-lg">
            <p className="text-gray-400 mb-4">No alert rules configured</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="text-blue-400 hover:text-blue-300"
            >
              Create your first rule
            </button>
          </div>
        ) : (
          rules.map((rule) => (
            <div
              key={rule.rule_id}
              className="bg-gray-800 rounded-lg p-4 border border-gray-700"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-white">{rule.name}</h3>
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${rule.enabled
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-500/20 text-gray-400'
                        }`}
                    >
                      {rule.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-300 space-y-1">
                    <p>
                      <span className="text-gray-400">Event Type:</span>{' '}
                      <span className="text-white">{rule.event_type}</span>
                    </p>
                    <p>
                      <span className="text-gray-400">Condition:</span>{' '}
                      <span className="text-white">
                        {rule.condition}
                        {rule.field && ` of ${rule.field}`} &gt; {rule.threshold}
                      </span>
                    </p>
                    <p>
                      <span className="text-gray-400">Window:</span>{' '}
                      <span className="text-white">{rule.window_seconds}s</span>
                    </p>
                    <p>
                      <span className="text-gray-400">Channels:</span>{' '}
                      <span className="text-white">{rule.channels.join(', ')}</span>
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggleEnabled(rule.rule_id, rule.enabled)}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm"
                  >
                    {rule.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => handleDeleteRule(rule.rule_id)}
                    className="px-3 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
