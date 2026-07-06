import React, { useState, useEffect } from 'react';
import { CreditCard, Check, X, AlertTriangle, TrendingUp, Download } from 'lucide-react';
import { api } from '../../services/api';

export default function BillingDashboard() {
  const [subscription, setSubscription] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/billing/subscriptions/current/'),
      api.get('/billing/invoices/'),
      api.get('/billing/plans/'),
    ]).then(([subRes, invRes, plansRes]) => {
      setSubscription(subRes.data);
      setInvoices(invRes.data.results || []);
      setPlans(plansRes.data.results || []);
      setLoading(false);
    });
  }, []);

  const handleUpgrade = async (plan) => {
    const { data } = await api.post('/billing/subscriptions/checkout/', {
      plan_id: plan.id,
      success_url: window.location.origin + '/billing?success=true',
      cancel_url: window.location.origin + '/billing?canceled=true',
      billing_interval: 'month',
    });
    window.location.href = data.url;
  };

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Current Plan</h2>
            <p className="text-gray-500 mt-1">Manage your subscription and billing</p>
          </div>
          <div className="px-4 py-2 bg-blue-50 text-blue-700 rounded-full text-sm font-semibold">
            {subscription?.plan?.name || 'Free'}
          </div>
        </div>
        <div className="grid grid-cols-4 gap-4 mt-6">
          <StatCard icon={<CreditCard />} label="Status" value={subscription?.status || 'Active'} />
          <StatCard icon={<TrendingUp />} label="Renewal" value={subscription?.days_until_renewal + ' days' || 'N/A'} />
          <StatCard icon={<AlertTriangle />} label="Users" value={`${subscription?.usage?.current_users || 0}/${subscription?.plan?.max_users || 5}`} />
          <StatCard icon={<Download />} label="Storage" value={`${subscription?.usage?.storage_used_mb || 0}MB`} />
        </div>
      </div>

      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-4">Available Plans</h3>
        <div className="grid grid-cols-4 gap-4">
          {plans.map((plan) => (
            <PlanCard key={plan.id} plan={plan} isCurrent={subscription?.plan?.id === plan.id} onUpgrade={() => handleUpgrade(plan)} />
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-4">Invoice History</h3>
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-t border-gray-100">
                  <td className="px-4 py-3 text-sm font-medium">{inv.invoice_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{new Date(inv.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-sm">${inv.total}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      inv.status === 'paid' ? 'bg-green-100 text-green-700' :
                      inv.status === 'open' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-700'
                    }`}>{inv.status}</span>
                  </td>
                  <td className="px-4 py-3">
                    {inv.pdf_url && <a href={inv.pdf_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-700 text-sm font-medium">Download</a>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="bg-gray-50 rounded-xl p-4">
      <div className="text-gray-400 mb-2">{icon}</div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  );
}

function PlanCard({ plan, isCurrent, onUpgrade }) {
  return (
    <div className={`rounded-2xl border-2 p-6 ${isCurrent ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}`}>
      <h4 className="text-lg font-bold text-gray-900">{plan.name}</h4>
      <p className="text-gray-500 text-sm mt-1">{plan.description}</p>
      <div className="mt-4">
        <span className="text-3xl font-bold text-gray-900">${plan.price_monthly}</span>
        <span className="text-gray-500">/month</span>
      </div>
      <ul className="mt-4 space-y-2">
        <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" /> {plan.max_users} Users</li>
        <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" /> {plan.max_warehouses} Warehouses</li>
        <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" /> {plan.storage_limit_gb}GB Storage</li>
        {plan.includes_api_access && <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" /> API Access</li>}
        {plan.includes_ai_features && <li className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" /> AI Features</li>}
      </ul>
      <button onClick={onUpgrade} disabled={isCurrent}
        className={`w-full mt-6 py-2 rounded-lg font-semibold transition-colors ${isCurrent ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`}>
        {isCurrent ? 'Current Plan' : 'Upgrade'}
      </button>
    </div>
  );
}
