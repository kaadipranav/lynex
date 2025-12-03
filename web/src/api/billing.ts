import { apiClient } from './client';

export interface SubscriptionTier {
  events_per_month: number;
  retention_days: number;
  projects: number;
  team_members: number;
  alerts: number;
}

export interface Subscription {
  user_id: string;
  tier: 'free' | 'pro' | 'business';
  status: 'active' | 'canceled' | 'past_due';
  current_period_start: string;
  current_period_end: string;
  events_used_this_period: number;
}

export interface UsageStats {
  subscription: {
    tier: string;
    status: string;
    period_start: string;
    period_end: string;
  };
  usage: {
    allowed: boolean;
    used: number;
    limit: number | 'unlimited';
    remaining?: number;
    percentage?: number;
  };
  limits: SubscriptionTier;
}

export interface Plan {
  id: string;
  name: string;
  price: number;
  interval: string;
  features: SubscriptionTier;
  whop_url?: string;
}

// Note: Billing service runs on port 8002
const BILLING_BASE = 'http://localhost:8002/api/v1';

export const billingApi = {
  getSubscription: async (userId: string) => {
    const response = await apiClient.get<{ subscription: Subscription; limits: SubscriptionTier }>(
      `${BILLING_BASE}/billing/subscription`,
      { params: { user_id: userId } }
    );
    return response.data;
  },

  getUsage: async (userId: string) => {
    const response = await apiClient.get<UsageStats>(
      `${BILLING_BASE}/billing/usage`,
      { params: { user_id: userId } }
    );
    return response.data;
  },

  checkLimit: async (userId: string) => {
    const response = await apiClient.get<{ allowed: boolean; used: number; limit: number }>(
      `${BILLING_BASE}/billing/check-limit`,
      { params: { user_id: userId } }
    );
    return response.data;
  },

  activateLicense: async (userId: string, licenseKey: string) => {
    const response = await apiClient.post(
      `${BILLING_BASE}/billing/activate-license`,
      { license_key: licenseKey },
      { params: { user_id: userId } }
    );
    return response.data;
  },

  getPlans: async () => {
    const response = await apiClient.get<{ plans: Plan[] }>(
      `${BILLING_BASE}/billing/plans`
    );
    return response.data.plans;
  },
};
