import { apiClient } from './client';

export interface UsageStats {
  tier: 'free' | 'pro' | 'enterprise';
  usage: number;
  limit: number;
  percent_used: number;
}

export const getUsageStats = async (): Promise<UsageStats> => {
  const response = await apiClient.get('/subscription/usage');
  return response.data;
};
