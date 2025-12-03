import { useQuery } from '@tanstack/react-query';
import { statsApi } from '../api/stats';
import { StatCard } from '../components/StatCard';
import { RequestsChart, TokenUsageChart } from '../components/Charts';
import { Activity, AlertTriangle, DollarSign, Zap, Clock } from 'lucide-react';
import { useState } from 'react';

export default function DashboardPage() {
  const projectId = 'proj_demo';
  const [timeRange, setTimeRange] = useState(24); // hours

  // Fetch Overview Stats
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ['stats', 'overview', projectId, timeRange],
    queryFn: () => statsApi.getOverview(projectId, timeRange),
    refetchInterval: 30000,
  });

  // Fetch Request Volume Time Series
  const { data: requestSeries, isLoading: loadingRequests } = useQuery({
    queryKey: ['stats', 'timeseries', 'requests', projectId, timeRange],
    queryFn: () => statsApi.getTimeSeries(projectId, 'requests', timeRange, timeRange > 24 ? '1d' : '1h'),
    refetchInterval: 30000,
  });

  // Fetch Token Usage by Model
  const { data: tokenUsage, isLoading: loadingTokens } = useQuery({
    queryKey: ['stats', 'tokens', projectId, timeRange],
    queryFn: () => statsApi.getTokenUsage(projectId, timeRange),
    refetchInterval: 30000,
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Overview of your AI application performance</p>
        </div>
        
        <select 
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="bg-white border border-gray-300 text-gray-700 text-sm rounded-lg focus:ring-indigo-500 focus:border-indigo-500 block p-2.5"
        >
          <option value={1}>Last Hour</option>
          <option value={24}>Last 24 Hours</option>
          <option value={168}>Last 7 Days</option>
          <option value={720}>Last 30 Days</option>
        </select>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Requests"
          value={overview?.total_events.toLocaleString() || 0}
          icon={Activity}
          loading={loadingOverview}
        />
        <StatCard
          title="Error Rate"
          value={`${overview?.error_rate_pct.toFixed(2)}%`}
          icon={AlertTriangle}
          loading={loadingOverview}
          className={overview && overview.error_rate_pct > 5 ? "border-red-200 bg-red-50" : ""}
        />
        <StatCard
          title="Total Cost"
          value={`$${overview?.total_cost_usd.toFixed(4)}`}
          icon={DollarSign}
          loading={loadingOverview}
        />
        <StatCard
          title="Total Tokens"
          value={(overview?.total_tokens || 0).toLocaleString()}
          icon={Zap}
          loading={loadingOverview}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart: Request Volume */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Request Volume</h3>
          <RequestsChart data={requestSeries?.data || []} loading={loadingRequests} />
        </div>

        {/* Secondary Chart: Token Usage */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Token Usage by Model</h3>
          <TokenUsageChart data={tokenUsage || []} loading={loadingTokens} />
        </div>
      </div>

      {/* Additional Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
         <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Average Latency</h3>
              <div className="text-2xl font-bold text-gray-900">
                {overview?.avg_latency_ms ? `${overview.avg_latency_ms.toFixed(0)}ms` : 'N/A'}
              </div>
            </div>
            <div className="p-3 bg-blue-50 rounded-full">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
         </div>
      </div>
    </div>
  );
}
