import { apiClient } from './client';

export interface OverviewStats {
  total_events: number;
  total_errors: number;
  error_rate_pct: number;
  total_cost_usd: number;
  total_tokens: number;
  avg_latency_ms: number | null;
}

export interface TokenUsageByModel {
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_cost_usd: number;
  request_count: number;
}

export interface EventCountByType {
  type: string;
  count: number;
}

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
}

export interface TimeSeriesResponse {
  metric: string;
  data: TimeSeriesPoint[];
}

export const statsApi = {
  getOverview: async (projectId: string, hours: number = 24) => {
    const response = await apiClient.get<OverviewStats>('/stats/overview', {
      params: { project_id: projectId, hours },
    });
    return response.data;
  },

  getTokenUsage: async (projectId: string, hours: number = 24) => {
    const response = await apiClient.get<TokenUsageByModel[]>('/stats/tokens', {
      params: { project_id: projectId, hours },
    });
    return response.data;
  },

  getEventsByType: async (projectId: string, hours: number = 24) => {
    const response = await apiClient.get<EventCountByType[]>('/stats/events-by-type', {
      params: { project_id: projectId, hours },
    });
    return response.data;
  },

  getTimeSeries: async (projectId: string, metric: string, hours: number = 24, interval: string = '1h') => {
    const response = await apiClient.get<TimeSeriesResponse>('/stats/timeseries', {
      params: { project_id: projectId, metric, hours, interval },
    });
    return response.data;
  },
};
