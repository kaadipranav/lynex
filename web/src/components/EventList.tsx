import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { eventsApi } from '../api/events';
import { EventCard } from './EventCard';
import { Loader2, RefreshCw } from 'lucide-react';

interface EventListProps {
  projectId: string;
  typeFilter?: string;
}

export function EventList({ projectId, typeFilter }: EventListProps) {
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['events', projectId, typeFilter, page],
    queryFn: () => eventsApi.list({
      project_id: projectId,
      type: typeFilter === 'all' ? undefined : typeFilter,
      limit: pageSize,
      offset: page * pageSize,
    }),
    refetchInterval: 10000, // Auto-refresh every 10s
  });

  if (isLoading && page === 0) {
    return (
      <div className="flex justify-center items-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
        Error loading events. Is the backend running?
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-500">
          Showing {data?.events.length || 0} events
        </div>
        <button 
          onClick={() => refetch()}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 text-gray-600 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="space-y-3">
        {data?.events.map((event) => (
          <EventCard key={event.event_id} event={event} />
        ))}
        
        {data?.events.length === 0 && (
          <div className="text-center py-12 text-gray-500 bg-gray-50 rounded-lg border border-dashed border-gray-300">
            No events found for this filter.
          </div>
        )}
      </div>

      <div className="flex justify-center gap-4 pt-4">
        <button
          onClick={() => setPage(p => Math.max(0, p - 1))}
          disabled={page === 0}
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <span className="flex items-center text-sm text-gray-600">
          Page {page + 1}
        </span>
        <button
          onClick={() => setPage(p => p + 1)}
          disabled={!data?.has_more}
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  );
}
