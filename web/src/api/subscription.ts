import { client } from './client';

export interface UsageStats {
  tier: 'free' | 'pro' | 'enterprise';
  usage: number;
  limit: number;
  percent_used: number;
}

export const getUsageStats = async (): Promise<UsageStats> => {
  const response = await client.get('/subscription/usage');
  return response.data;
};
