import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, FileText, AlertCircle, CheckCircle, 
  Upload, Mail, CreditCard, LogOut, Bell 
} from 'lucide-react';
import api from '../../services/api';

function ClientDashboard({ user }) {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await api.get('/api/client/dashboard');
      setDashboard(response.data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/api/credit-reports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchDashboard();
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">CreditRepair Pro</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="text-gray-500 hover:text-gray-700">
                <Bell className="h-6 w-6" />
              </button>
              <span className="text-sm text-gray-700">{dashboard?.client?.name}</span>
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-gray-700"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Credit Scores */}
        {dashboard?.credit_scores && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {['equifax', 'experian', 'transunion'].map((bureau) => {
              const score = dashboard.credit_scores[bureau];
              const color = score >= 700 ? 'text-green-600' : score >= 600 ? 'text-yellow-600' : 'text-red-600';
              
              return (
                <div key={bureau} className="bg-white rounded-xl shadow p-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-600 capitalize">{bureau}</p>
                      <p className={`text-4xl font-bold ${color}`}>
                        {score || '---'}
                      </p>
                    </div>
                    <CreditCard className="h-8 w-8 text-gray-400" />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-blue-100 rounded-lg">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600">Credit Reports</p>
                <p className="text-2xl font-bold">{dashboard?.stats?.total_reports || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <AlertCircle className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600">Active Disputes</p>
                <p className="text-2xl font-bold">{dashboard?.stats?.active_disputes || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold">{dashboard?.stats?.completed_disputes || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-red-100 rounded-lg">
                <AlertCircle className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600">Errors Found</p>
                <p className="text-2xl font-bold">{dashboard?.stats?.total_errors || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="flex items-center justify-center p-6 border-2 border-dashed border-gray-300 rounded-xl hover:border-blue-500 cursor-pointer transition">
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                className="hidden"
                onChange={handleFileUpload}
                disabled={uploading}
              />
              {uploading ? (
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              ) : (
                <>
                  <Upload className="h-6 w-6 text-gray-400 mr-2" />
                  <span className="text-gray-600">Upload Credit Report</span>
                </>
              )}
            </label>

            <button className="flex items-center justify-center p-6 border border-gray-300 rounded-xl hover:bg-gray-50 transition">
              <FileText className="h-6 w-6 text-gray-400 mr-2" />
              <span className="text-gray-600">View Disputes</span>
            </button>

            <button className="flex items-center justify-center p-6 border border-gray-300 rounded-xl hover:bg-gray-50 transition">
              <Mail className="h-6 w-6 text-gray-400 mr-2" />
              <span className="text-gray-600">View Letters</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default ClientDashboard;