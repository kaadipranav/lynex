import React, { useEffect, useState } from 'react';
import { getUsageStats, UsageStats } from '../api/subscription';
import { Card, Title, Text, Metric, ProgressBar, Flex, Badge } from '@tremor/react';

const UsagePage: React.FC = () => {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getUsageStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch usage stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <div className="p-10">Loading usage statistics...</div>;
  }

  if (!stats) {
    return <div className="p-10">Failed to load usage statistics.</div>;
  }

  const isUnlimited = stats.limit === -1;
  const limitDisplay = isUnlimited ? 'Unlimited' : stats.limit.toLocaleString();
  const usageDisplay = stats.usage.toLocaleString();

  return (
    <div className="p-10 space-y-6">
      <Title>Subscription & Usage</Title>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <Flex alignItems="start">
            <div>
              <Text>Current Plan</Text>
              <Metric className="capitalize">{stats.tier}</Metric>
            </div>
            <Badge size="xl" color={stats.tier === 'enterprise' ? 'violet' : stats.tier === 'pro' ? 'blue' : 'gray'}>
              {stats.tier.toUpperCase()}
            </Badge>
          </Flex>
          <div className="mt-4">
            <Text>
              {stats.tier === 'free' && "Upgrade to Pro for 100k events."}
              {stats.tier === 'pro' && "Upgrade to Enterprise for unlimited events."}
              {stats.tier === 'enterprise' && "You have the highest tier."}
            </Text>
          </div>
        </Card>

        <Card>
          <Text>Monthly Event Usage</Text>
          <Flex className="mt-4" justifyContent="between" alignItems="end">
            <Text>
              <span className="text-2xl font-bold text-slate-900 dark:text-slate-50">{usageDisplay}</span>
              <span className="text-slate-500"> / {limitDisplay}</span>
            </Text>
            <Text>{isUnlimited ? '0%' : `${stats.percent_used.toFixed(1)}%`}</Text>
          </Flex>
          <ProgressBar 
            value={isUnlimited ? 0 : stats.percent_used} 
            color={stats.percent_used > 90 ? 'red' : 'blue'} 
            className="mt-2" 
          />
          <Text className="mt-2 text-sm text-slate-500">
            Resets on the 1st of next month.
          </Text>
        </Card>
      </div>

      <Card>
        <Title>Upgrade Plan</Title>
        <Text className="mt-2">
          To upgrade your plan, please contact support or use the admin portal (if you are an admin).
        </Text>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`p-4 border rounded-lg ${stats.tier === 'free' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                <h3 className="font-bold">Free</h3>
                <p>10,000 events/mo</p>
                <p className="text-sm text-gray-500">Perfect for hobby projects.</p>
            </div>
            <div className={`p-4 border rounded-lg ${stats.tier === 'pro' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                <h3 className="font-bold">Pro</h3>
                <p>100,000 events/mo</p>
                <p className="text-sm text-gray-500">For growing startups.</p>
            </div>
            <div className={`p-4 border rounded-lg ${stats.tier === 'enterprise' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                <h3 className="font-bold">Enterprise</h3>
                <p>Unlimited events</p>
                <p className="text-sm text-gray-500">For large scale applications.</p>
            </div>
        </div>
      </Card>
    </div>
  );
};

export default UsagePage;
