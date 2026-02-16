import React, { useState, useEffect } from 'react';
import { Check, X } from 'lucide-react';
import api from '../../services/api';

function PricingPage() {
  const [plans, setPlans] = useState([]);
  const [billingInterval, setBillingInterval] = useState('monthly');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await api.get('/api/payments/plans');
      setPlans(response.data.plans);
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planId) => {
    try {
      const response = await api.post('/api/payments/create-checkout', {
        plan_id: planId,
        interval: billingInterval
      });
      window.location.href = response.data.checkout_url;
    } catch (error) {
      console.error('Checkout error:', error);
    }
  };

  const features = [
    { name: 'Disputes per month', key: 'max_disputes_per_month' },
    { name: 'Credit reports', key: 'max_reports' },
    { name: 'Dispute letters', key: 'includes_letters' },
    { name: 'Credit monitoring', key: 'includes_monitoring' },
    { name: 'Direct creditor disputes', key: 'includes_direct_creditor' },
    { name: 'Phone support', key: 'includes_phone_support' },
    { name: 'Priority support', key: 'priority_support' }
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900">Simple, Transparent Pricing</h1>
          <p className="mt-4 text-xl text-gray-600">Choose the plan that works best for you</p>

          {/* Billing Toggle */}
          <div className="mt-8 flex justify-center items-center space-x-4">
            <button
              onClick={() => setBillingInterval('monthly')}
              className={`px-4 py-2 rounded-lg font-medium ${
                billingInterval === 'monthly'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingInterval('yearly')}
              className={`px-4 py-2 rounded-lg font-medium ${
                billingInterval === 'yearly'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border'
              }`}
            >
              Yearly
              <span className="ml-2 text-sm bg-green-100 text-green-700 px-2 py-0.5 rounded">Save 20%</span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl shadow-lg overflow-hidden ${
                plan.slug === 'professional' ? 'ring-2 ring-blue-600' : ''
              }`}
            >
              {plan.slug === 'professional' && (
                <div className="bg-blue-600 text-white text-center py-2 text-sm font-medium">
                  Most Popular
                </div>
              )}
              
              <div className="p-8">
                <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                <p className="mt-2 text-gray-600">{plan.description}</p>
                
                <div className="mt-6">
                  <span className="text-4xl font-bold text-gray-900">
                    ${billingInterval === 'monthly' 
                      ? plan.price_monthly 
                      : (plan.price_yearly || plan.price_monthly * 10).toFixed(2)}
                  </span>
                  <span className="text-gray-600">/{billingInterval === 'monthly' ? 'mo' : 'yr'}</span>
                </div>

                <button
                  onClick={() => handleSubscribe(plan.id)}
                  className={`mt-6 w-full py-3 px-4 rounded-lg font-medium ${
                    plan.slug === 'professional'
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  Get Started
                </button>
              </div>

              <div className="border-t border-gray-200 p-8">
                <ul className="space-y-4">
                  {features.map((feature) => (
                    <li key={feature.key} className="flex items-center">
                      {typeof plan[feature.key] === 'boolean' ? (
                        plan[feature.key] ? (
                          <Check className="h-5 w-5 text-green-500 mr-3" />
                        ) : (
                          <X className="h-5 w-5 text-gray-300 mr-3" />
                        )
                      ) : (
                        <Check className="h-5 w-5 text-green-500 mr-3" />
                      )}
                      <span className="text-gray-600">
                        {typeof plan[feature.key] === 'number' 
                          ? `${plan[feature.key]} ${feature.name}`
                          : feature.name}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default PricingPage;