import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, APIKey, APIKeyWithSecret } from '../api/projects';
import { Plus, Key, Trash2, RefreshCw, Eye, EyeOff, Copy, Check } from 'lucide-react';

export default function SettingsPage() {
  const projectId = 'proj_demo';
  const queryClient = useQueryClient();
  
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyEnv, setNewKeyEnv] = useState<'test' | 'live'>('test');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<APIKeyWithSecret | null>(null);
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);

  // Fetch API keys
  const { data: keys, isLoading } = useQuery({
    queryKey: ['api-keys', projectId],
    queryFn: () => projectsApi.listKeys(projectId),
  });

  // Create key mutation
  const createKeyMutation = useMutation({
    mutationFn: () => projectsApi.createKey(projectId, { name: newKeyName, environment: newKeyEnv }),
    onSuccess: (data) => {
      setNewlyCreatedKey(data);
      setNewKeyName('');
      setShowCreateForm(false);
      queryClient.invalidateQueries({ queryKey: ['api-keys', projectId] });
    },
  });

  // Revoke key mutation
  const revokeKeyMutation = useMutation({
    mutationFn: (keyId: string) => projectsApi.revokeKey(projectId, keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys', projectId] });
    },
  });

  const copyToClipboard = async (text: string, keyId: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedKeyId(keyId);
    setTimeout(() => setCopiedKeyId(null), 2000);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your project and API keys</p>
      </div>

      {/* Newly Created Key Alert */}
      {newlyCreatedKey && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Key className="w-5 h-5 text-green-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-green-800">API Key Created!</h3>
              <p className="text-sm text-green-700 mt-1">
                Copy this key now. You won't be able to see it again.
              </p>
              <div className="mt-3 flex items-center gap-2">
                <code className="flex-1 bg-green-100 px-3 py-2 rounded font-mono text-sm break-all">
                  {newlyCreatedKey.key}
                </code>
                <button
                  onClick={() => copyToClipboard(newlyCreatedKey.key, 'new')}
                  className="p-2 bg-green-600 text-white rounded hover:bg-green-700"
                >
                  {copiedKeyId === 'new' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <button
                onClick={() => setNewlyCreatedKey(null)}
                className="mt-3 text-sm text-green-600 hover:underline"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys Section */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-900">API Keys</h2>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700"
          >
            <Plus className="w-4 h-4" />
            Create Key
          </button>
        </div>

        {/* Create Key Form */}
        {showCreateForm && (
          <div className="p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex items-end gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Key Name</label>
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Production Server"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Environment</label>
                <select
                  value={newKeyEnv}
                  onChange={(e) => setNewKeyEnv(e.target.value as 'test' | 'live')}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="test">Test</option>
                  <option value="live">Live</option>
                </select>
              </div>
              <button
                onClick={() => createKeyMutation.mutate()}
                disabled={!newKeyName || createKeyMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {createKeyMutation.isPending ? 'Creating...' : 'Create'}
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Keys List */}
        <div className="divide-y divide-gray-100">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : keys?.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No API keys yet. Create one to get started.
            </div>
          ) : (
            keys?.map((key) => (
              <div key={key.id} className="p-4 flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{key.name}</span>
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                      key.environment === 'live' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {key.environment}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500 font-mono mt-1">
                    {key.key_prefix}•••••••••••••••••
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    Created: {new Date(key.created_at).toLocaleDateString()}
                    {key.last_used_at && ` • Last used: ${new Date(key.last_used_at).toLocaleDateString()}`}
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to revoke this API key?')) {
                      revokeKeyMutation.mutate(key.id);
                    }
                  }}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  title="Revoke Key"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
