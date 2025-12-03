import { useState } from 'react';
import { Event } from '../api/events';
import { ChevronDown, ChevronUp, Clock, AlertCircle, Terminal, Zap, Database } from 'lucide-react';
import { cn } from '../lib/utils';

interface EventCardProps {
  event: Event;
}

const EventIcon = ({ type }: { type: string }) => {
  switch (type) {
    case 'error':
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    case 'token_usage':
      return <Zap className="w-5 h-5 text-yellow-500" />;
    case 'model_response':
      return <Database className="w-5 h-5 text-blue-500" />;
    default:
      return <Terminal className="w-5 h-5 text-gray-500" />;
  }
};

export function EventCard({ event }: EventCardProps) {
  const [expanded, setExpanded] = useState(false);

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleString();
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      <div 
        className="p-4 cursor-pointer flex items-center gap-4"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-shrink-0">
          <EventIcon type={event.type} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn(
              "px-2 py-0.5 text-xs font-medium rounded-full uppercase",
              event.type === 'error' ? "bg-red-100 text-red-700" :
              event.type === 'token_usage' ? "bg-yellow-100 text-yellow-700" :
              "bg-gray-100 text-gray-700"
            )}>
              {event.type}
            </span>
            <span className="text-sm text-gray-500 font-mono truncate">
              {event.event_id}
            </span>
          </div>
          
          <div className="text-sm text-gray-900 truncate">
            {getEventSummary(event)}
          </div>
        </div>

        <div className="flex flex-col items-end gap-1 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatTime(event.timestamp)}
          </div>
          {event.estimated_cost_usd > 0 && (
            <div className="font-medium text-green-600">
              ${event.estimated_cost_usd.toFixed(6)}
            </div>
          )}
        </div>

        <div className="text-gray-400">
          {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-100 p-4 bg-gray-50 rounded-b-lg overflow-x-auto">
          <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
            <div>
              <span className="font-semibold text-gray-500">SDK:</span> {event.sdk_name} v{event.sdk_version}
            </div>
            <div>
              <span className="font-semibold text-gray-500">Latency:</span> {event.queue_latency_ms}ms
            </div>
          </div>
          
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Event Body</h4>
            <pre className="bg-gray-900 text-gray-100 p-3 rounded text-xs font-mono overflow-auto max-h-96">
              {JSON.stringify(event.body, null, 2)}
            </pre>
          </div>

          {Object.keys(event.context).length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Context</h4>
              <pre className="bg-gray-100 text-gray-700 p-3 rounded text-xs font-mono overflow-auto">
                {JSON.stringify(event.context, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function getEventSummary(event: Event): string {
  if (event.type === 'error') {
    return event.body.message || 'Unknown Error';
  }
  if (event.type === 'model_response') {
    return `${event.body.model} • ${event.body.usage?.totalTokens || 0} tokens`;
  }
  if (event.type === 'token_usage') {
    return `${event.body.model} • ${event.body.totalTokens} tokens`;
  }
  if (event.type === 'log') {
    return event.body.message || 'Log entry';
  }
  return JSON.stringify(event.body).slice(0, 100);
}
