import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';

interface SpanData {
  event_id: string;
  trace_id: string;
  parent_event_id?: string;
  type: string;
  timestamp: string;
  name?: string;
  duration_ms?: number;
  status?: string;
  body: Record<string, any>;
  context?: Record<string, any>;
  estimated_cost_usd?: number;
  children: SpanData[];
}

interface TraceData {
  trace_id: string;
  project_id: string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  total_events: number;
  root_spans: SpanData[];
  metadata: Record<string, any>;
}

const TraceView: React.FC = () => {
  const { traceId } = useParams<{ traceId: string }>();
  const navigate = useNavigate();
  const [trace, setTrace] = useState<TraceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSpan, setSelectedSpan] = useState<SpanData | null>(null);

  useEffect(() => {
    loadTrace();
  }, [traceId]);

  const loadTrace = async () => {
    if (!traceId) return;
    
    try {
      setLoading(true);
      const projectId = localStorage.getItem('current_project_id');
      const response = await api.get(`/traces/${traceId}`, {
        params: { project_id: projectId }
      });
      setTrace(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail?.error || 'Failed to load trace');
    } finally {
      setLoading(false);
    }
  };

  const renderSpan = (span: SpanData, depth: number = 0) => {
    const indent = depth * 24;
    const hasChildren = span.children && span.children.length > 0;
    
    // Color coding by type
    const typeColors: Record<string, string> = {
      span: 'bg-blue-100 border-blue-400',
      model_response: 'bg-purple-100 border-purple-400',
      tool_call: 'bg-green-100 border-green-400',
      error: 'bg-red-100 border-red-400',
      log: 'bg-gray-100 border-gray-400',
    };
    
    const colorClass = typeColors[span.type] || 'bg-gray-100 border-gray-400';
    const isSelected = selectedSpan?.event_id === span.event_id;
    
    return (
      <div key={span.event_id} className="mb-1">
        <div
          style={{ marginLeft: `${indent}px` }}
          className={`p-3 border-l-4 rounded cursor-pointer transition-all ${colorClass} ${
            isSelected ? 'ring-2 ring-blue-500 shadow-md' : 'hover:shadow-sm'
          }`}
          onClick={() => setSelectedSpan(span)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {hasChildren && (
                <span className="text-xs text-gray-500">▼</span>
              )}
              <span className="font-medium text-sm">
                {span.name || span.type}
              </span>
              <span className="text-xs text-gray-500 font-mono">
                {span.type}
              </span>
            </div>
            
            <div className="flex items-center space-x-4 text-xs">
              {span.duration_ms && (
                <span className="text-gray-600">
                  {span.duration_ms.toFixed(2)}ms
                </span>
              )}
              {span.estimated_cost_usd && (
                <span className="text-green-600 font-semibold">
                  ${span.estimated_cost_usd.toFixed(4)}
                </span>
              )}
              {span.status && (
                <span className={`px-2 py-1 rounded ${
                  span.status === 'success' ? 'bg-green-200 text-green-800' :
                  span.status === 'error' ? 'bg-red-200 text-red-800' :
                  'bg-yellow-200 text-yellow-800'
                }`}>
                  {span.status}
                </span>
              )}
            </div>
          </div>
          
          {span.body?.message && (
            <div className="mt-1 text-xs text-gray-600 truncate">
              {span.body.message}
            </div>
          )}
        </div>
        
        {hasChildren && (
          <div className="mt-1">
            {span.children.map(child => renderSpan(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-500">Loading trace...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded">
        <p className="text-red-800">{error}</p>
        <button
          onClick={() => navigate(-1)}
          className="mt-2 text-sm text-red-600 hover:underline"
        >
          ← Go back
        </button>
      </div>
    );
  }

  if (!trace) {
    return <div>Trace not found</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-blue-600 hover:underline mb-2"
        >
          ← Back to traces
        </button>
        
        <h1 className="text-2xl font-bold mb-2">Trace Visualization</h1>
        
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-gray-500">Trace ID</div>
              <div className="font-mono text-xs">{trace.trace_id}</div>
            </div>
            <div>
              <div className="text-gray-500">Duration</div>
              <div className="font-semibold">{trace.duration_ms.toFixed(2)}ms</div>
            </div>
            <div>
              <div className="text-gray-500">Events</div>
              <div className="font-semibold">{trace.total_events}</div>
            </div>
            <div>
              <div className="text-gray-500">Started</div>
              <div className="text-xs">
                {new Date(trace.start_time).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Span Tree */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <h2 className="text-lg font-semibold mb-4">Span Tree</h2>
            <div className="space-y-1">
              {trace.root_spans.map(span => renderSpan(span))}
            </div>
          </div>
        </div>

        {/* Span Details */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border p-4 sticky top-6">
            <h2 className="text-lg font-semibold mb-4">Span Details</h2>
            
            {selectedSpan ? (
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-500">Event ID</label>
                  <div className="text-xs font-mono bg-gray-50 p-2 rounded">
                    {selectedSpan.event_id}
                  </div>
                </div>
                
                <div>
                  <label className="text-sm text-gray-500">Type</label>
                  <div className="text-sm font-medium">{selectedSpan.type}</div>
                </div>
                
                <div>
                  <label className="text-sm text-gray-500">Timestamp</label>
                  <div className="text-xs">
                    {new Date(selectedSpan.timestamp).toLocaleString()}
                  </div>
                </div>
                
                {selectedSpan.duration_ms && (
                  <div>
                    <label className="text-sm text-gray-500">Duration</label>
                    <div className="text-sm font-medium">
                      {selectedSpan.duration_ms.toFixed(2)}ms
                    </div>
                  </div>
                )}
                
                <div>
                  <label className="text-sm text-gray-500">Body</label>
                  <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-64">
                    {JSON.stringify(selectedSpan.body, null, 2)}
                  </pre>
                </div>
                
                {selectedSpan.context && Object.keys(selectedSpan.context).length > 0 && (
                  <div>
                    <label className="text-sm text-gray-500">Context</label>
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-64">
                      {JSON.stringify(selectedSpan.context, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-gray-500">
                Click on a span to view details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TraceView;
