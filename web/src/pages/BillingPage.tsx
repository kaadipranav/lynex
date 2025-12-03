import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { billingApi, Plan } from '../api/billing';
import { useAuth } from '../hooks/useAuth';
import { Check, Zap, Building2, Sparkles, ExternalLink, Key } from 'lucide-react';

export default function BillingPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [licenseKey, setLicenseKey] = useState('');
  const [showLicenseInput, setShowLicenseInput] = useState(false);

  const userId = user?.id || 'user_demo';

  // Fetch usage stats
  const { data: usage, isLoading: loadingUsage } = useQuery({
    queryKey: ['billing', 'usage', userId],
    queryFn: () => billingApi.getUsage(userId),
  });

  // Fetch plans
  const { data: plans } = useQuery({
    queryKey: ['billing', 'plans'],
    queryFn: () => billingApi.getPlans(),
  });

  // Activate license mutation
  const activateMutation = useMutation({
    mutationFn: () => billingApi.activateLicense(userId, licenseKey),
    onSuccess: () => {
      setLicenseKey('');
      setShowLicenseInput(false);
      queryClient.invalidateQueries({ queryKey: ['billing'] });
    },
  });

  const currentTier = usage?.subscription?.tier || 'free';

  const tierIcons: Record<string, any> = {
    free: Sparkles,
    pro: Zap,
    business: Building2,
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Billing & Usage</h1>
        <p className="text-gray-500 mt-1">Manage your subscription and monitor usage</p>
      </div>

      {/* Current Plan & Usage */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Current Plan */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Current Plan</h2>
          <div className="flex items-center gap-3 mb-4">
            {(() => {
              const Icon = tierIcons[currentTier] || Sparkles;
              return <Icon className="w-8 h-8 text-indigo-600" />;
            })()}
            <div>
              <div className="text-2xl font-bold text-gray-900 capitalize">{currentTier}</div>
              <div className="text-sm text-gray-500">
                {usage?.subscription?.status === 'active' ? 'Active' : usage?.subscription?.status}
              </div>
            </div>
          </div>
          {usage?.subscription?.period_end && (
            <p className="text-sm text-gray-500">
              Renews: {new Date(usage.subscription.period_end).toLocaleDateString()}
            </p>
          )}
        </div>

        {/* Usage */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Events This Month</h2>
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span>{(usage?.usage?.used || 0).toLocaleString()} used</span>
              <span>
                {usage?.usage?.limit === 'unlimited' 
                  ? 'Unlimited' 
                  : `${(usage?.usage?.limit || 0).toLocaleString()} limit`}
              </span>
            </div>
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full ${
                  (usage?.usage?.percentage || 0) > 90 ? 'bg-red-500' :
                  (usage?.usage?.percentage || 0) > 70 ? 'bg-yellow-500' :
                  'bg-indigo-600'
                }`}
                style={{ width: `${Math.min(usage?.usage?.percentage || 0, 100)}%` }}
              />
            </div>
          </div>
          {usage?.usage?.percentage !== undefined && usage.usage.percentage > 80 && (
            <p className="text-sm text-yellow-600">
              ⚠️ You're approaching your limit. Consider upgrading.
            </p>
          )}
        </div>
      </div>

      {/* License Key Activation */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-900">Activate License</h2>
          </div>
          {!showLicenseInput && (
            <button
              onClick={() => setShowLicenseInput(true)}
              className="text-sm text-indigo-600 hover:underline"
            >
              Have a license key?
            </button>
          )}
        </div>
        
        {showLicenseInput && (
          <div className="flex gap-3">
            <input
              type="text"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              placeholder="Enter your Whop license key"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={() => activateMutation.mutate()}
              disabled={!licenseKey || activateMutation.isPending}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {activateMutation.isPending ? 'Activating...' : 'Activate'}
            </button>
            <button
              onClick={() => setShowLicenseInput(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Plans */}
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Plans</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans?.map((plan) => {
          const isCurrentPlan = currentTier === plan.id;
          const Icon = tierIcons[plan.id] || Sparkles;
          
          return (
            <div 
              key={plan.id}
              className={`bg-white border rounded-xl p-6 ${
                isCurrentPlan ? 'border-indigo-500 ring-2 ring-indigo-100' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center gap-2 mb-4">
                <Icon className="w-6 h-6 text-indigo-600" />
                <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
              </div>
              
              <div className="mb-4">
                <span className="text-3xl font-bold text-gray-900">${plan.price}</span>
                <span className="text-gray-500">/{plan.interval}</span>
              </div>
              
              <ul className="space-y-2 mb-6">
                <li className="flex items-center gap-2 text-sm text-gray-600">
                  <Check className="w-4 h-4 text-green-500" />
                  {plan.features.events_per_month === -1 
                    ? 'Unlimited events' 
                    : `${(plan.features.events_per_month).toLocaleString()} events/mo`}
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-600">
                  <Check className="w-4 h-4 text-green-500" />
                  {plan.features.retention_days} days retention
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-600">
                  <Check className="w-4 h-4 text-green-500" />
                  {plan.features.projects === -1 ? 'Unlimited' : plan.features.projects} projects
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-600">
                  <Check className="w-4 h-4 text-green-500" />
                  {plan.features.alerts === -1 ? 'Unlimited' : plan.features.alerts} alerts
                </li>
              </ul>
              
              {isCurrentPlan ? (
                <button 
                  disabled 
                  className="w-full py-2 bg-gray-100 text-gray-500 rounded-lg"
                >
                  Current Plan
                </button>
              ) : plan.whop_url ? (
                <a
                  href={plan.whop_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  Upgrade <ExternalLink className="w-4 h-4" />
                </a>
              ) : (
                <button disabled className="w-full py-2 bg-gray-100 text-gray-400 rounded-lg">
                  Free Forever
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
