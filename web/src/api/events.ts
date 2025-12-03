import { apiClient } from './client';

export interface Event {
  event_id: string;
  project_id: string;
  type: 'log' | 'error' | 'span' | 'token_usage' | 'model_response' | string;
  timestamp: string;
  sdk_name: string;
  sdk_version: string;
  body: any;
  context: any;
  estimated_cost_usd: number;
  queue_latency_ms: number;
}

export interface EventListResponse {
  events: Event[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface EventFilters {
  project_id: string;
  type?: string;
  limit?: number;
  offset?: number;
  start_time?: string;
  end_time?: string;
}

export const eventsApi = {
  list: async (filters: EventFilters) => {
    const params = new URLSearchParams();
    params.append('project_id', filters.project_id);
    if (filters.type) params.append('type', filters.type);
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());
    if (filters.start_time) params.append('start_time', filters.start_time);
    if (filters.end_time) params.append('end_time', filters.end_time);

    const response = await apiClient.get<EventListResponse>('/events', { params });
    return response.data;
  },

  get: async (eventId: string, projectId: string) => {
    const response = await apiClient.get<Event>(`/events/${eventId}`, {
      params: { project_id: projectId },
    });
    return response.data;
  },
};
