import { useState } from 'react';
import { EventList } from '../components/EventList';
import { Filter } from 'lucide-react';

export default function EventsPage() {
  const [typeFilter, setTypeFilter] = useState<string>('all');
  
  // Hardcoded for MVP
  const projectId = 'proj_demo';

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Events Timeline</h1>
          <p className="text-gray-500 mt-1">Real-time stream of AI interactions</p>
        </div>

        <div className="flex items-center gap-2 bg-white p-1 border border-gray-200 rounded-lg shadow-sm">
          <Filter className="w-4 h-4 text-gray-400 ml-2" />
          <select 
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="border-none text-sm focus:ring-0 text-gray-700 py-1 pr-8 pl-2 bg-transparent"
          >
            <option value="all">All Types</option>
            <option value="model_response">Model Responses</option>
            <option value="token_usage">Token Usage</option>
            <option value="error">Errors</option>
            <option value="log">Logs</option>
          </select>
        </div>
      </div>

      <EventList projectId={projectId} typeFilter={typeFilter} />
    </div>
  );
}
