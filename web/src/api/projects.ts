import { apiClient } from './client';

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface APIKey {
  id: string;
  project_id: string;
  name: string;
  environment: 'test' | 'live';
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

export interface APIKeyWithSecret extends APIKey {
  key: string;
}

export const projectsApi = {
  list: async () => {
    const response = await apiClient.get<Project[]>('/projects');
    return response.data;
  },

  get: async (projectId: string) => {
    const response = await apiClient.get<Project>(`/projects/${projectId}`);
    return response.data;
  },

  create: async (data: { name: string; description?: string }) => {
    const response = await apiClient.post<Project>('/projects', data);
    return response.data;
  },

  update: async (projectId: string, data: { name?: string; description?: string }) => {
    const response = await apiClient.patch<Project>(`/projects/${projectId}`, data);
    return response.data;
  },

  delete: async (projectId: string) => {
    await apiClient.delete(`/projects/${projectId}`);
  },

  // API Keys
  listKeys: async (projectId: string) => {
    const response = await apiClient.get<APIKey[]>(`/projects/${projectId}/keys`);
    return response.data;
  },

  createKey: async (projectId: string, data: { name: string; environment: 'test' | 'live' }) => {
    const response = await apiClient.post<APIKeyWithSecret>(`/projects/${projectId}/keys`, data);
    return response.data;
  },

  revokeKey: async (projectId: string, keyId: string) => {
    await apiClient.delete(`/projects/${projectId}/keys/${keyId}`);
  },

  regenerateKey: async (projectId: string, keyId: string) => {
    const response = await apiClient.post<APIKeyWithSecret>(`/projects/${projectId}/keys/${keyId}/regenerate`);
    return response.data;
  },
};
