import React, { useState, useEffect } from 'react';
import { Users, FileText, TrendingUp, DollarSign } from 'lucide-react';
import api from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState({
    totalClients: 0,
    totalReports: 0,
    totalDisputes: 0,
    totalRevenue: 0
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const clientsRes = await api.get('/api/clients');
      setStats(prev => ({
        ...prev,
        totalClients: clientsRes.data.total
      }));
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const statCards = [
    { title: 'Total Clients', value: stats.totalClients, icon: Users, color: 'bg-blue-500' },
    { title: 'Credit Reports', value: stats.totalReports, icon: FileText, color: 'bg-green-500' },
    { title: 'Active Disputes', value: stats.totalDisputes, icon: TrendingUp, color: 'bg-yellow-500' },
    { title: 'Revenue', value: `$${stats.totalRevenue}`, icon: DollarSign, color: 'bg-purple-500' }
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-xl font-bold">Admin Dashboard</h1>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {statCards.map((card) => (
            <div key={card.title} className="bg-white rounded-xl shadow p-6">
              <div className="flex items-center">
                <div className={`${card.color} p-3 rounded-lg`}>
                  <card.icon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">{card.title}</p>
                  <p className="text-2xl font-bold">{card.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;